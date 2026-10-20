import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lmis import config, gaps, ui
from lmis.ui import t

result = ui.data()

st.header(t("forecast_title"))
st.write(t("forecast_intro"))
state, district, trade = ui.pair_picker("forecast")
row = ui.pair_row(result["gaps"], state, district, trade)

index_frame = result["index"]
history = index_frame[(index_frame["state"] == state) & (index_frame["district"] == district) & (index_frame["trade"] == trade)].sort_values("month")
future = result["forecasts"]
future = future[(future["state"] == state) & (future["district"] == district) & (future["trade"] == trade)].sort_values("month")

columns = st.columns(5)
ui.kpi(columns[0], t("col_forecast_demand"), ui.number(row["forecast_demand"]), t("band_sub", low=ui.number(row["demand_lower"]), high=ui.number(row["demand_upper"])))
ui.kpi(columns[1], t("col_supply"), ui.number(row["supply"]), t("supply_sub", seats=ui.number(row["sanctioned_seats"])))
ui.kpi(columns[2], t("col_gap_ratio"), f"{row['gap_ratio']:.2f}", t("gap_sub", gap=ui.number(row["gap_people"])))
ui.kpi(columns[3], t("col_status"), ui.chip(row["status"]), t("current_sub", status=ui.status_text(row["current_status"])))
ui.kpi(columns[4], t("col_nco"), row["nco"], f"{t('col_qp')}: {row['qp']} | NSQF {row['nsqf']}")
st.write("")

st.subheader(t("demand_vs_supply"))
history_x = history["month"].dt.to_timestamp()
future_x = future["month"].dt.to_timestamp()
monthly_supply = row["supply"] / 12
figure = go.Figure()
figure.add_scatter(x=list(future_x) + list(future_x[::-1]), y=list(future["upper"]) + list(future["lower"][::-1]), fill="toself", fillcolor=ui.BAND, line=dict(width=0), name=t("legend_band"), hoverinfo="skip")
figure.add_scatter(x=history_x, y=history["openings"], name=t("legend_history"), line=dict(color=ui.NAVY, width=2))
figure.add_scatter(x=future_x, y=future["forecast"], name=t("legend_forecast"), line=dict(color=ui.NAVY, width=2, dash="dash"))
figure.add_scatter(x=list(history_x) + list(future_x), y=[monthly_supply] * (len(history_x) + len(future_x)), name=t("legend_supply"), line=dict(color=ui.SAFFRON, width=2, dash="dot"))
figure.update_layout(yaxis_title=t("axis_openings"))
ui.plot(figure, height=400)
ui.source_note()

st.subheader(t("ratio_path"))
st.caption(t("ratio_path_hint"))
months, trailing = gaps.rolling_path(index_frame, result["forecasts"], (state, district, trade))
path = pd.DataFrame({"month": months, "forecast_demand": trailing})
path["gap_ratio"] = row["supply"] / path["forecast_demand"]
path["status"] = path["gap_ratio"].apply(gaps.status_for)
ui.table(path, [("month", "month"), ("forecast_demand", "int"), ("gap_ratio", "ratio"), ("status", "status")], height=300)
ui.source_note()

st.subheader(t("source_contribution"))
st.caption(t("source_contribution_hint"))
recent = history.tail(12)
figure = go.Figure()
palette = {"portal": ui.NAVY, "ncs": "#3D6FA8", "industry": ui.SAFFRON, "eshram": ui.GREY}
for source, spec in config.SOURCES.items():
    figure.add_bar(x=recent["month"].dt.to_timestamp(), y=recent[f"c_{source}"], name=f"{t('src_' + source)} ({spec['weight']:.2f})", marker_color=palette[source])
figure.add_scatter(x=recent["month"].dt.to_timestamp(), y=recent["index"], name=t("legend_index"), line=dict(color="#1A1A1A", width=2))
figure.update_layout(barmode="relative", yaxis_title=t("axis_index"))
ui.plot(figure, height=360)
ui.source_note()

st.subheader(t("raw_signals"))
raw = history.tail(12).copy()
ui.table(raw, [("month", "month"), ("portal", "int"), ("ncs", "int"), ("industry", "dec"), ("eshram", "int"), ("index", "ratio"), ("openings", "int")])
ui.source_note()
