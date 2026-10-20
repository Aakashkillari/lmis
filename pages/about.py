import pandas as pd
import streamlit as st

from pramaan import charts, model, settings as s, theme
from pramaan.core import data, status_label, t, updated_badge

result = data()

theme.page_header(t("crumb_about"), t("about_title"), t("about_sub"), updated_badge())

steps = "".join(f'<div class="step"><div class="no">{n}</div><div class="h">{t(f"step{n}_h")}</div><div class="p">{t(f"step{n}_p")}</div></div>' for n in range(1, 6))
st.markdown(f'<div class="steps">{steps}</div>', unsafe_allow_html=True)
st.write("")

left, right = st.columns(2, gap="medium")
with left:
    with theme.card(t("weights_title"), t("weights_tag"), t("weights_caption")):
        st.plotly_chart(charts.weight_bars(lambda x: t(f"src_{x}"), t("axis_weight")), width="stretch", config=charts.CONFIG)
with right:
    with theme.card(t("bands_title"), t("bands_tag"), t("bands_caption")):
        bands = pd.DataFrame([{
            "status": theme.chip(status, status_label(status)),
            "range": f"< {high:.1f}" if low is None else f"> {low:.1f}" if high is None else f"{low:.1f} – {high:.1f}",
            "action": t(f"action_{status}"),
        } for status, low, high in s.BANDS])
        theme.table(bands, [("status", t("status"), "html"), ("range", t("col_ratio_range"), "text"), ("action", t("col_action"), "text")])

backtest = result["backtest"]
by_trade = backtest.groupby(["trade", "short"], as_index=False)[["mape", "naive_mape"]].median()
with theme.card(t("accuracy_title"), t("accuracy_tag", months=s.BACKTEST_MONTHS), t("accuracy_caption")):
    columns = st.columns(3)
    theme.kpi(columns[0], t("kpi_model_error"), f"{backtest['mape'].median():.1f}%", t("model_note"), "#3A63A8")
    theme.kpi(columns[1], t("kpi_naive_error"), f"{backtest['naive_mape'].median():.1f}%", t("naive_note"), "#9AA3AF")
    theme.kpi(columns[2], t("kpi_series"), str(len(backtest)), t("series_note"), "#3F8A4E")
    st.plotly_chart(charts.accuracy_bars(by_trade, t("model_label"), t("naive_label"), t("axis_error")), width="stretch", config=charts.CONFIG)

left, right = st.columns(2, gap="medium")
with left:
    with theme.card(t("sources_title"), t("sources_tag")):
        sources = pd.DataFrame([{"source": t(f"real_{k}"), "use": t(f"real_{k}_use")} for k in ["portal", "ncs", "industry", "eshram", "plfs", "ncvt"]])
        theme.table(sources, [("source", t("col_source"), "text"), ("use", t("col_use"), "text")])
with right:
    with theme.card(t("matcher_title"), t("matcher_tag"), t("matcher_caption")):
        text = st.text_input(t("matcher_input"), value="Electrition for house wiring", key="matcher_text")
        matches = model.match_title(text)
        if matches:
            frame = pd.DataFrame(matches)
            frame["score"] = [f"{c} / 100" for c in frame["confidence"]]
            theme.table(frame, [("trade", t("col_trade"), "text"), ("nco", "NCO", "text"), ("matched", t("col_matched"), "text"), ("score", t("col_confidence"), "text")])

with theme.card(t("api_title"), t("api_tag"), t("api_caption")):
    st.code("GET /api/gaps?district=Coimbatore&sector=Automotive&status=Shortage\nGET /api/warnings\nGET /api/health", language="text")

st.caption(t("pilot_note"))
