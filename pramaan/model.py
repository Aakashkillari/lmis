import hashlib
import math
import pickle
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from rapidfuzz import fuzz
from scipy.stats import norm
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from pramaan import settings as s

KEYS = ["district", "trade"]
SOURCES = list(s.WEIGHTS)
CACHE = Path(__file__).resolve().parent.parent / ".cache"


def trade_info():
    return pd.DataFrame(s.TRADES)[["trade", "short", "sector", "nco", "qp", "nsqf"]]


def history_months():
    return pd.period_range(end=s.HISTORY_END, periods=s.HISTORY_MONTHS, freq="M")


def season(month_numbers, sector):
    peak = 10 if sector == "Automotive" else 3
    return 1 + 0.12 * np.cos(2 * np.pi * (month_numbers - peak) / 12)


def rule_value(rules, district, trade, default):
    for name, districts, value in rules:
        if name == trade and (districts is None or district in districts):
            return value
    return default


def generate(state=s.STATE):
    config = s.STATES[state]
    rng = np.random.default_rng(config["seed"])
    months = history_months()
    count = len(months)
    steps = count + s.FORECAST_MONTHS
    month_numbers = ((months[0].month - 1 + np.arange(steps)) % 12) + 1
    signals, seats = [], []
    for district, place in config["districts"].items():
        for spec in s.TRADES:
            trade = spec["trade"]
            growth = spec["growth"] + rule_value(config["growth_boost"], district, trade, 0.0) + rng.normal(0, 0.02)
            level = spec["base"] * place["size"] * rng.uniform(0.85, 1.15)
            path = level * (1 + growth) ** (np.arange(steps) / 12) * season(month_numbers, spec["sector"])
            actual = path[:count] * rng.lognormal(0, 0.06, count)
            ahead = np.array([path[i:i + 3].mean() for i in range(count)])
            lagged = np.concatenate([actual[:2], actual[:-2]])
            signals.append(pd.DataFrame({
                "month": months,
                "district": district,
                "trade": trade,
                "portal": np.round(actual * s.PORTAL_DUPLICATION * rng.lognormal(0, 0.10, count)),
                "ncs": rng.poisson(actual * s.NCS_COVERAGE),
                "industry": np.round(100 * ahead / level * rng.lognormal(0, 0.05, count), 1),
                "eshram": rng.poisson(lagged * 3.0),
            }))
            completion = rng.uniform(0.78, 0.92)
            certification = rng.uniform(0.66, 0.86)
            ratio = rule_value(config["supply_stories"], district, trade, None)
            ratio = ratio * rng.uniform(0.95, 1.05) if ratio else float(np.clip(rng.normal(1.0, 0.1), 0.85, 1.15))
            total = path[count:].sum() * ratio / (completion * certification)
            seats.append({
                "district": district,
                "trade": trade,
                "seats": max(20, int(round(total / 10)) * 10),
                "completion": round(completion, 3),
                "certification": round(certification, 3),
            })
    return pd.concat(signals, ignore_index=True), pd.DataFrame(seats)


def zscore(series):
    spread = series.std(ddof=0)
    return series * 0.0 if not spread else (series - series.mean()) / spread


def calibrate(group):
    spread = group["index"].std(ddof=0)
    scale = group["reference"].std(ddof=0) / spread if spread else 0
    return (group["reference"].mean() + scale * (group["index"] - group["index"].mean())).clip(lower=0)


def demand_index(signals):
    frame = signals.copy()
    frame["index"] = 0.0
    for source in SOURCES:
        frame[f"c_{source}"] = s.WEIGHTS[source] * frame.groupby(KEYS)[source].transform(zscore)
        frame["index"] += frame[f"c_{source}"]
    frame["reference"] = (frame["portal"] / s.PORTAL_DUPLICATION + frame["ncs"] / s.NCS_COVERAGE) / 2
    frame["openings"] = frame.groupby(KEYS, group_keys=False)[["index", "reference"]].apply(calibrate)
    return frame


def predict(values, steps):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = ExponentialSmoothing(np.asarray(values, float), trend="add", seasonal="add", seasonal_periods=12, initialization_method="estimated").fit(optimized=True, use_brute=False)
    mean = np.clip(fit.forecast(steps), 0, None)
    spread = norm.ppf(0.5 + s.BAND_LEVEL / 2) * np.std(fit.resid, ddof=1) * np.sqrt(np.arange(1, steps + 1))
    return mean, np.clip(mean - spread, 0, None), mean + spread


def mape(actual, predicted):
    actual, predicted = np.asarray(actual, float), np.asarray(predicted, float)
    mask = actual > 0
    return float(np.mean(np.abs(actual[mask] - predicted[mask]) / actual[mask]) * 100)


def forecast(index):
    future = pd.period_range(index["month"].max() + 1, periods=s.FORECAST_MONTHS, freq="M")
    frames, tests = [], []
    for (district, trade), group in index.groupby(KEYS, sort=False):
        series = group["openings"].to_numpy()
        mean, lower, upper = predict(series, s.FORECAST_MONTHS)
        frames.append(pd.DataFrame({"month": future, "district": district, "trade": trade, "forecast": mean, "lower": lower, "upper": upper}))
        hold = s.BACKTEST_MONTHS
        test, _, _ = predict(series[:-hold], hold)
        naive = np.repeat(series[:-hold][-12:].mean(), hold)
        tests.append({"district": district, "trade": trade, "mape": mape(series[-hold:], test), "naive_mape": mape(series[-hold:], naive)})
    return pd.concat(frames, ignore_index=True), pd.DataFrame(tests).merge(trade_info(), on="trade")


def status_for(ratio):
    for status, low, high in s.BANDS:
        if (low is None or ratio >= low) and (high is None or ratio < high):
            return status
    return "Balanced"


def score(frame):
    frame = frame.copy()
    frame["supply"] = frame["seats"] * frame["completion"] * frame["certification"]
    frame["ratio"] = frame["supply"] / frame["demand"]
    frame["gap"] = frame["supply"] - frame["demand"]
    frame["severity"] = frame["gap"].abs()
    frame["status"] = frame["ratio"].apply(status_for)
    frame["current_ratio"] = frame["supply"] / frame["last_12m"]
    frame["current_status"] = frame["current_ratio"].apply(status_for)
    frame["growth"] = frame["demand"] / frame["last_12m"] - 1
    return frame


def gap_table(seats, index, forecasts):
    demand = forecasts.groupby(KEYS, as_index=False).agg(demand=("forecast", "sum"), demand_low=("lower", "sum"), demand_high=("upper", "sum"))
    recent = index[index["month"] > index["month"].max() - 12].groupby(KEYS, as_index=False)["openings"].sum().rename(columns={"openings": "last_12m"})
    return score(seats.merge(demand, on=KEYS).merge(recent, on=KEYS).merge(trade_info(), on="trade"))


def with_seats(gaps, district, trade, seats, completion=None, certification=None):
    frame = gaps.copy()
    mask = (frame["district"] == district) & (frame["trade"] == trade)
    frame.loc[mask, "seats"] = seats
    if completion is not None:
        frame.loc[mask, "completion"] = completion
    if certification is not None:
        frame.loc[mask, "certification"] = certification
    return score(frame)


def series(frame, district, trade):
    return frame[(frame["district"] == district) & (frame["trade"] == trade)].sort_values("month")


def ratio_path(index, forecasts, district, trade, supply):
    past = series(index, district, trade)["openings"].to_numpy()[-12:]
    ahead = series(forecasts, district, trade)
    values = np.concatenate([past, ahead["forecast"].to_numpy()])
    rolling = [values[step + 1:step + 13].sum() for step in range(len(ahead))]
    path = pd.DataFrame({"month": ahead["month"].to_numpy(), "forecast": ahead["forecast"].to_numpy(), "rolling_demand": rolling})
    path["ratio"] = supply / path["rolling_demand"]
    path["status"] = path["ratio"].apply(status_for)
    return path


def early_warnings(gaps, index, forecasts):
    rows = []
    for row in gaps.itertuples():
        path = ratio_path(index, forecasts, row.district, row.trade, row.supply).head(s.WARNING_MONTHS)
        for step, point in enumerate(path.itertuples(), start=1):
            if point.status in ("Shortage", "Oversupply") and point.status != row.current_status:
                rows.append({
                    "district": row.district, "trade": row.trade, "short": row.short, "sector": row.sector,
                    "current_status": row.current_status, "projected_status": point.status,
                    "month": point.month, "months_ahead": step, "ratio": point.ratio,
                    "people": abs(row.supply - point.rolling_demand),
                })
                break
    columns = ["district", "trade", "short", "sector", "current_status", "projected_status", "month", "months_ahead", "ratio", "people"]
    return pd.DataFrame(rows, columns=columns).sort_values(["months_ahead", "people"], ascending=[True, False]).reset_index(drop=True)


def yield_rate(row):
    return row["completion"] * row["certification"]


def reallocate(gaps, same_sector=True, budget=None):
    rules = s.REALLOCATION
    groups = [g for _, g in gaps.groupby("sector")] if same_sector else [gaps]
    moves = []
    remaining = budget if budget is not None else math.inf
    for group in groups:
        rows = {i: r.to_dict() for i, r in group.iterrows()}
        donors = sorted([i for i in rows if rows[i]["status"] == "Oversupply"], key=lambda i: -rows[i]["severity"])
        receivers = sorted([i for i in rows if rows[i]["status"] == "Shortage"], key=lambda i: -rows[i]["severity"])
        for receiver in receivers:
            for donor in donors:
                need = math.ceil(rows[receiver]["demand"] * rules["receiver_target"] / yield_rate(rows[receiver]))
                need = max(0, math.ceil((need - rows[receiver]["seats"]) / rules["block"]) * rules["block"])
                keep = math.ceil(rows[donor]["demand"] * rules["donor_keep"] / yield_rate(rows[donor]))
                spare = max(0, (rows[donor]["seats"] - keep) // rules["block"] * rules["block"])
                moved = int(min(need, spare, remaining // rules["block"] * rules["block"]))
                if moved <= 0:
                    continue
                before_from = rows[donor]["seats"] * yield_rate(rows[donor]) / rows[donor]["demand"]
                before_to = rows[receiver]["seats"] * yield_rate(rows[receiver]) / rows[receiver]["demand"]
                rows[donor]["seats"] -= moved
                rows[receiver]["seats"] += moved
                remaining -= moved
                moves.append({
                    "from_district": rows[donor]["district"], "from_trade": rows[donor]["trade"], "from_short": rows[donor]["short"],
                    "to_district": rows[receiver]["district"], "to_trade": rows[receiver]["trade"], "to_short": rows[receiver]["short"],
                    "sector": rows[donor]["sector"], "seats": moved,
                    "from_before": before_from, "from_after": rows[donor]["seats"] * yield_rate(rows[donor]) / rows[donor]["demand"],
                    "to_before": before_to, "to_after": rows[receiver]["seats"] * yield_rate(rows[receiver]) / rows[receiver]["demand"],
                })
    columns = ["from_district", "from_trade", "from_short", "to_district", "to_trade", "to_short", "sector", "seats", "from_before", "from_after", "to_before", "to_after"]
    return pd.DataFrame(moves, columns=columns)


def apply_moves(gaps, moves):
    frame = gaps.copy()
    for move in moves.itertuples():
        frame.loc[(frame["district"] == move.from_district) & (frame["trade"] == move.from_trade), "seats"] -= move.seats
        frame.loc[(frame["district"] == move.to_district) & (frame["trade"] == move.to_trade), "seats"] += move.seats
    return score(frame)


def clean_title(text):
    text = re.sub(r"[^a-z0-9 ]", " ", str(text).lower().replace("-", " "))
    return re.sub(r"\s+", " ", text).strip()


def match_title(text, top=3):
    query = clean_title(text)
    if not query:
        return []
    best = {}
    for trade, aliases in s.ALIASES.items():
        for alias in aliases:
            target = clean_title(alias)
            score_value = 100.0 if target == query else min(99.0, fuzz.WRatio(query, target))
            key = (score_value, len(target))
            if trade not in best or key > best[trade][0]:
                best[trade] = (key, alias)
    info = {t["trade"]: t for t in s.TRADES}
    ranked = sorted(best.items(), key=lambda item: item[1][0], reverse=True)[:top]
    return [{"trade": trade, "nco": info[trade]["nco"], "qp": info[trade]["qp"], "matched": alias, "confidence": round(key[0])} for trade, (key, alias) in ranked]


def fingerprint(state=s.STATE):
    text = repr([state, s.STATES[state], s.HISTORY_MONTHS, s.HISTORY_END, s.FORECAST_MONTHS, s.TRADES, s.WEIGHTS, s.BANDS, s.BAND_LEVEL])
    return hashlib.md5(text.encode()).hexdigest()[:12]


def compute(state=s.STATE):
    signals, seats = generate(state)
    index = demand_index(signals).merge(trade_info()[["trade", "short", "sector"]], on="trade")
    forecasts, backtest = forecast(index)
    gaps = gap_table(seats, index, forecasts)
    return {
        "index": index,
        "forecasts": forecasts,
        "backtest": backtest,
        "gaps": gaps,
        "warnings": early_warnings(gaps, index, forecasts),
        "updated": str(index["month"].max().strftime("%b %Y")),
        "state": state,
        "districts": list(s.STATES[state]["districts"]),
    }


def build(state=s.STATE):
    path = CACHE / f"pramaan_{fingerprint(state)}.pkl"
    if path.exists():
        with path.open("rb") as handle:
            return pickle.load(handle)
    result = compute(state)
    CACHE.mkdir(exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(result, handle)
    return result
