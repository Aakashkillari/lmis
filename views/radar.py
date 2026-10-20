import plotly.graph_objects as go
import streamlit as st

from lmis import config, gaps, ui
from lmis.ui import t

result = ui.data()
frame = result["gaps"]

st.header(t("radar_title"))
st.write(t("radar_intro"))

states = [ui.all_option()] + list(config.STATES)
state = st.selectbox(t("filter_state"), states, key="radar_state")
scope = frame if state == ui.all_option() else frame[frame["state"] == state]

by_trade = gaps.rollup(scope, ["trade", "sector"])
by_trade["demand_growth"] = by_trade["forecast_demand"] / by_trade["last_12m_demand"] - 1
by_trade = by_trade.sort_values("demand_growth", ascending=False)

st.subheader(t("radar_trades"))
ui.table(by_trade, [
    ("trade", "text"),
    ("sector", "text"),
    ("last_12m_demand", "int"),
    ("forecast_demand", "int"),
    ("demand_growth", "pct"),
    ("supply", "int"),
    ("gap_ratio", "ratio"),
    ("status", "status"),
])
ui.source_note()

ordered = by_trade.sort_values("demand_growth")
figure = go.Figure()
figure.add_bar(
    y=ordered["trade"], x=ordered["demand_growth"] * 100, orientation="h",
    marker_color=[ui.SAFFRON if value > 0.1 else ui.NAVY for value in ordered["demand_growth"]],
    text=[f"{value:+.1%}" for value in ordered["demand_growth"]], textposition="outside",
)
figure.update_layout(xaxis_title=t("axis_growth"), showlegend=False)
ui.plot(figure, height=380)
ui.source_note()

st.subheader(t("radar_pairs"))
top_pairs = scope.sort_values("demand_growth", ascending=False).head(15)
ui.table(top_pairs, [
    ("state", "text"),
    ("district", "text"),
    ("trade", "text"),
    ("last_12m_demand", "int"),
    ("forecast_demand", "int"),
    ("demand_growth", "pct"),
    ("gap_ratio", "ratio"),
    ("status", "status"),
])
ui.status_legend()
ui.source_note()
