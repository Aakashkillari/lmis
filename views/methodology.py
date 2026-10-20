import pandas as pd
import streamlit as st

from lmis import config, ui
from lmis.data import trade_table
from lmis.ui import t

result = ui.data()

st.header(t("method_title"))
st.write(t("method_intro"))

st.subheader(t("method_sources"))
sources = pd.DataFrame([
    {"source": t(f"src_{key}"), "counterpart": t(f"src_{key}_real"), "unit": t(f"unit_{key}"), "granularity": t("granularity"), "weight": spec["weight"]}
    for key, spec in config.SOURCES.items()
])
ui.table(sources, [("source", "text"), ("counterpart", "text"), ("unit", "text"), ("granularity", "text"), ("weight", "ratio")])
ui.source_note()

st.subheader(t("method_steps"))
steps = [
    ("step1", "formula1"),
    ("step2", "formula2"),
    ("step3", "formula3"),
    ("step4", "formula4"),
    ("step5", "formula5"),
    ("step6", "formula6"),
    ("step7", None),
    ("step8", None),
    ("step9", "formula9"),
]
weights = " + ".join(f"{spec['weight']:.2f} x z({key})" for key, spec in config.SOURCES.items())
for step, formula in steps:
    st.markdown(t(step, months=config.FORECAST_MONTHS, horizon=config.WARNING_HORIZON, dup=config.PORTAL_DUPLICATION, cov=config.NCS_COVERAGE))
    if formula:
        st.markdown(f'<div class="formula">{t(formula, weights=weights)}</div>', unsafe_allow_html=True)

st.subheader(t("method_thresholds"))
bands = pd.DataFrame([
    {"status": band["status"], "ratio_from": "-" if band["min"] is None else f"{band['min']:.2f}", "ratio_to": "-" if band["max"] is None else f"{band['max']:.2f}", "meaning": t(f"meaning_{band['status']}")}
    for band in config.STATUS_BANDS
])
ui.table(bands, [("status", "status"), ("ratio_from", "text"), ("ratio_to", "text"), ("meaning", "text")])
ui.source_note()

st.subheader(t("method_backtest"))
backtest = result["backtest"]
columns = st.columns(3)
ui.kpi(columns[0], t("bt_mape"), f"{backtest['mape'].median():.1f}%", t("bt_mape_sub", months=config.BACKTEST_MONTHS))
ui.kpi(columns[1], t("bt_naive"), f"{backtest['naive_mape'].median():.1f}%", t("bt_naive_sub"))
ui.kpi(columns[2], t("bt_series"), str(len(backtest)), t("bt_series_sub"))
st.write("")
by_trade = backtest.groupby("trade", as_index=False).agg(mape=("mape", "median"), naive_mape=("naive_mape", "median"), actual_6m=("actual_6m", "sum"), forecast_6m=("forecast_6m", "sum"))
ui.table(by_trade, [("trade", "text"), ("actual_6m", "int"), ("forecast_6m", "int"), ("mape", "dec"), ("naive_mape", "dec")])
ui.source_note()

st.subheader(t("method_trades"))
ui.table(trade_table(), [("trade", "text"), ("sector", "text"), ("nco", "text"), ("qp", "text"), ("nsqf", "text")])
st.caption(t("indicative_codes"))
ui.source_note()

st.subheader(t("method_limits"))
st.markdown(t("limits_text"))
