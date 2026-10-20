import numpy as np
import pandas as pd

from lmis import config

TYPO_TITLES = {
    "Electrician (Domestic)": "Electrition",
    "Solar PV Installer": "Solar Tecnician",
    "Two-Wheeler Service Technician": "Two Weeler Mechanic",
    "EV Service Technician": "E V Mechanic",
}

STRONGER_GROWTH = [
    {"trade": "EV Service Technician", "districts": ["Coimbatore", "Krishnagiri", "Bengaluru Urban"], "extra": 0.18},
    {"trade": "Solar PV Installer", "states": ["Uttar Pradesh", "Delhi"], "extra": 0.12},
]


def history_months():
    return pd.period_range(end=config.HISTORY_END, periods=config.HISTORY_MONTHS, freq="M")


def district_rows():
    rows = []
    for state, districts in config.STATES.items():
        for district in districts:
            rows.append({"state": state, "district": district})
    return rows


def trade_table():
    return pd.DataFrame(config.TRADES)[["trade", "sector", "nco", "qp", "nsqf"]]


def rule_matches(rule, state, district, trade):
    if rule["trade"] != trade:
        return False
    if rule.get("districts"):
        return district in rule["districts"]
    if rule.get("states"):
        return state in rule["states"]
    return True


def extra_growth(state, district, trade):
    for rule in STRONGER_GROWTH:
        if rule_matches(rule, state, district, trade):
            return rule["extra"]
    return 0.0


def season_factor(month_numbers, sector):
    if sector == "Automotive":
        peak = 10
    else:
        peak = 3
    angle = 2 * np.pi * (month_numbers - peak) / 12
    return 1 + 0.12 * np.cos(angle)


def expected_openings(level, growth, sector, start_month, steps):
    index = np.arange(steps)
    month_numbers = ((start_month - 1 + index) % 12) + 1
    return level * (1 + growth) ** (index / 12) * season_factor(month_numbers, sector)


def noisy(rng, values, spread):
    return values * rng.lognormal(0, spread, size=len(values))


def leading_mean(values, window):
    out = []
    for i in range(len(values)):
        out.append(values[i:i + window].mean())
    return np.array(out)


def title_split(rng, trade):
    aliases = config.TITLE_ALIASES[trade][:3]
    if trade in TYPO_TITLES:
        aliases = aliases[:2] + [TYPO_TITLES[trade]]
    shares = rng.dirichlet(np.ones(len(aliases)) * 4)
    return list(zip(aliases, shares))


def generate(seed=config.SEED):
    rng = np.random.default_rng(seed)
    months = history_months()
    start_month = months[0].month
    steps = len(months) + config.FORECAST_MONTHS
    titles = {t["trade"]: title_split(rng, t["trade"]) for t in config.TRADES}

    portal_rows = []
    signal_frames = []
    truth_rows = []

    for place in district_rows():
        state = place["state"]
        district = place["district"]
        for spec in config.TRADES:
            trade = spec["trade"]
            level = spec["base"] * config.DISTRICT_SIZE[district] * rng.uniform(0.85, 1.15)
            growth = spec["growth"] + extra_growth(state, district, trade) + rng.normal(0, 0.02)
            path = expected_openings(level, growth, spec["sector"], start_month, steps)
            past = noisy(rng, path[:len(months)], 0.06)

            portal_total = noisy(rng, past * config.PORTAL_DUPLICATION, 0.10)
            for title, share in titles[trade]:
                counts = np.round(portal_total * share * rng.lognormal(0, 0.05, len(months)))
                for month, count in zip(months, counts):
                    portal_rows.append({"month": month, "state": state, "district": district, "raw_title": title, "postings": int(count)})

            ncs = rng.poisson(past * config.NCS_COVERAGE)
            industry = noisy(rng, 100 * leading_mean(path[:len(months) + 3], 3)[:len(months)] / level, 0.05)
            lagged = np.concatenate([past[:2], past[:-2]])
            eshram = rng.poisson(lagged * 3.0)

            signal_frames.append(pd.DataFrame({
                "month": months,
                "state": state,
                "district": district,
                "trade": trade,
                "ncs": ncs,
                "industry": np.round(industry, 1),
                "eshram": eshram,
            }))
            truth_rows.append({
                "state": state,
                "district": district,
                "trade": trade,
                "next_year_openings": path[len(months):].sum(),
            })

    portal = pd.DataFrame(portal_rows)
    signals = pd.concat(signal_frames, ignore_index=True)
    capacity = capacity_table(rng, pd.DataFrame(truth_rows))
    return {"portal_raw": portal, "signals": signals, "capacity": capacity}


def planted_ratio(rng, state, district, trade):
    for rule in config.PLANTED_RATIOS:
        if rule_matches(rule, state, district, trade):
            return rule["ratio"] * rng.uniform(0.92, 1.08)
    return float(np.clip(rng.normal(1.0, 0.16), 0.72, 1.38))


def capacity_table(rng, truth):
    rows = []
    for row in truth.itertuples():
        completion = rng.uniform(0.78, 0.92)
        certification = rng.uniform(0.64, 0.86)
        ratio = planted_ratio(rng, row.state, row.district, row.trade)
        seats = row.next_year_openings * ratio / (completion * certification)
        seats = max(20, int(round(seats / 20)) * 20)
        iti_share = rng.uniform(0.45, 0.7)
        iti_seats = int(round(seats * iti_share / 4)) * 4
        rows.append({
            "state": row.state,
            "district": row.district,
            "trade": row.trade,
            "sanctioned_seats": seats,
            "iti_seats": iti_seats,
            "pmkvy_seats": seats - iti_seats,
            "completion_rate": round(completion, 3),
            "certification_rate": round(certification, 3),
        })
    return pd.DataFrame(rows)
