import json
from pathlib import Path

import streamlit as st

from pramaan import settings as s
from pramaan.dash_text import DASH, LABELS, MONTHS, SHORT_TRADES

WEB = Path(__file__).resolve().parent / "web"
ROOT = Path(__file__).resolve().parent.parent
STATUS_INDEX = {"Shortage": 0, "Watch (falling)": 1, "Balanced": 2, "Watch (rising)": 3, "Oversupply": 4}
PAGES = ["pages/dashboard.py", "pages/explore.py", "pages/plan.py", "pages/assistant.py", "pages/about.py"]
LANGUAGE_OPTIONS = [{"value": "en", "label": "English"}, {"value": "ta", "label": "தமிழ்"}, {"value": "hi", "label": "हिन्दी"}]


def read(name):
    return (WEB / name).read_text(encoding="utf-8")


HEADER = st.components.v2.component("pramaan_header", js=read("header.js"), css=read("header.css"))
DASHBOARD = st.components.v2.component("pramaan_dashboard", js=read("dashboard.js"), css=read("dashboard.css"))
GEO = json.loads((ROOT / "assets" / "tn_districts.json").read_text(encoding="utf-8"))


def month_label(period, lang):
    return f"{MONTHS[lang][period.month - 1]} {period.year}"


def search_items(lang):
    district_word = {"en": "District", "ta": "மாவட்டம்", "hi": "ज़िला"}[lang]
    trade_word = {"en": "Trade", "ta": "தொழில்", "hi": "ट्रेड"}[lang]
    items = [{"label": d, "kind": district_word, "value": f"district:{d}"} for d in s.DISTRICTS]
    items += [{"label": t["trade"], "kind": trade_word, "value": f"trade:{t['trade']}"} for t in s.TRADES]
    return items


def header(active, lang, choose):
    labels = DASH[lang]
    result = HEADER(
        key="pramaan_header",
        data={"active": active, "lang": lang, "nav": labels["nav"], "search": labels["search"], "role": labels["role"], "langs": LANGUAGE_OPTIONS, "items": search_items(lang)},
        on_nav_change=lambda: None,
        on_lang_change=lambda: None,
        on_search_change=lambda: None,
    )
    if result.lang:
        st.session_state["lang"] = result.lang
        st.rerun()
    if result.nav is not None and result.nav != active:
        st.switch_page(PAGES[int(result.nav)])
    if result.search:
        kind, value = result.search.split(":", 1)
        if kind == "district":
            choose(district=value)
        else:
            choose(trade=value)
        st.switch_page(PAGES[1])


def dashboard_payload(result, lang, district, trade, sector):
    gaps = result["gaps"]
    labels = dict(DASH[lang])
    names = list(s.DISTRICTS)
    trades = [t["trade"] for t in s.TRADES]
    pairs = []
    for name in names:
        row = []
        for trade_name in trades:
            pair = gaps[(gaps["district"] == name) & (gaps["trade"] == trade_name)].iloc[0]
            row.append({"j": round(float(pair["demand"]), 1), "t": round(float(pair["supply"]), 1), "r": round(float(pair["ratio"]), 4), "s": STATUS_INDEX[pair["status"]]})
        pairs.append(row)
    centres = {g["n"]: g for g in GEO["d"]}
    districts = [{
        "n": name, "note": labels["notes"].get(name, ""), "cx": centres[name]["cx"], "cy": centres[name]["cy"],
        "lx": LABELS[name]["x"], "ly": LABELS[name]["y"], "side": LABELS[name]["s"],
    } for name in names]
    forecast_months = sorted(result["forecasts"]["month"].unique())[: s.WARNING_MONTHS]
    month_index = {m: i for i, m in enumerate(forecast_months)}
    warnings = []
    for row in result["warnings"].itertuples():
        pair = gaps[(gaps["district"] == row.district) & (gaps["trade"] == row.trade)].iloc[0]
        warnings.append({
            "di": names.index(row.district), "k": trades.index(row.trade), "to": STATUS_INDEX[row.projected_status],
            "mi": month_index.get(row.month, 0), "now": round(float(pair["current_ratio"]), 3), "nowS": STATUS_INDEX[row.current_status],
        })
    backtest = result["backtest"]
    return {
        "stamp": f"{lang}|{district}|{trade}|{sector}",
        "L": {k: v for k, v in labels.items() if k != "notes"},
        "through": month_label(result["index"]["month"].max(), lang),
        "months": [month_label(m, lang) for m in forecast_months],
        "monthsShort": [MONTHS[lang][m.month - 1] for m in forecast_months],
        "districts": districts,
        "trades": [{"n": t["trade"], "s": SHORT_TRADES[t["trade"]], "sec": "E" if t["sector"] == "Electrical and Power" else "A"} for t in s.TRADES],
        "pairs": pairs,
        "warnings": warnings,
        "geo": GEO,
        "accuracy": {"model": float(backtest["mape"].median()), "naive": float(backtest["naive_mape"].median())},
        "statusNames": list(STATUS_INDEX),
        "start": {"sel": names.index(district) if district in names else 1, "tr": trades.index(trade) if trade in trades else 7, "sec": sector},
    }


def dashboard(result, lang, district, trade, sector):
    return DASHBOARD(key="pramaan_dashboard", data=dashboard_payload(result, lang, district, trade, sector), on_open_change=lambda: None)
