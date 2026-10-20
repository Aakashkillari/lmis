import plotly.graph_objects as go
import streamlit as st

from lmis import config, gaps, ui
from lmis.ui import t

result = ui.data()

st.header(t("whatif_title"))
st.write(t("whatif_intro"))
state, district, trade = ui.pair_picker("whatif", default=("Tamil Nadu", "Madurai", "Electrician (Domestic)"))
row = ui.pair_row(result["gaps"], state, district, trade)
seats = int(row["sanctioned_seats"])

change = st.slider(t("seat_change"), min_value=-seats, max_value=seats * 2, value=0, step=20, key=f"seats_{state}_{district}_{trade}")
columns = st.columns(2)
completion = columns[0].slider(t("col_completion_rate"), 0.5, 1.0, float(row["completion_rate"]), 0.01, key=f"comp_{state}_{district}_{trade}")
certification = columns[1].slider(t("col_certification_rate"), 0.4, 1.0, float(row["certification_rate"]), 0.01, key=f"cert_{state}_{district}_{trade}")

new_seats = seats + change
new_supply = new_seats * completion * certification
new_ratio = new_supply / row["forecast_demand"]
new_status = gaps.status_for(new_ratio)

columns = st.columns(4)
ui.kpi(columns[0], t("col_sanctioned_seats"), f"{seats:,} &rarr; {new_seats:,}", t("change_sub", change=f"{change:+,}"))
ui.kpi(columns[1], t("col_supply"), f"{ui.number(row['supply'])} &rarr; {ui.number(new_supply)}")
ui.kpi(columns[2], t("col_gap_ratio"), f"{row['gap_ratio']:.2f} &rarr; {new_ratio:.2f}", t("demand_sub", demand=ui.number(row["forecast_demand"])))
ui.kpi(columns[3], t("col_status"), f"{ui.chip(row['status'])} &rarr; {ui.chip(new_status)}")
st.write("")

needed = row["forecast_demand"] * config.TARGET_RATIO / (completion * certification)
st.markdown(t("seats_for_balance", seats=ui.number(round(needed / 20) * 20)))

figure = go.Figure()
upper_limit = max(2.5, new_ratio + 0.3, row["gap_ratio"] + 0.3)
for band in config.STATUS_BANDS:
    background, text = config.STATUS_COLOURS[band["status"]]
    start = band["min"] or 0
    end = band["max"] or upper_limit
    figure.add_shape(type="rect", x0=start, x1=end, y0=0, y1=1, fillcolor=background, line=dict(color=text, width=1), layer="below")
    figure.add_annotation(x=(start + end) / 2, y=0.85, text=ui.status_text(band["status"]), showarrow=False, font=dict(color=text, size=12))
figure.add_scatter(x=[row["gap_ratio"]], y=[0.45], mode="markers+text", marker=dict(symbol="circle-open", size=16, color=ui.GREY, line=dict(width=3)), text=[t("before")], textposition="bottom center", name=t("before"))
figure.add_scatter(x=[new_ratio], y=[0.45], mode="markers+text", marker=dict(symbol="diamond", size=16, color=ui.NAVY), text=[t("after")], textposition="top center", name=t("after"))
figure.update_xaxes(range=[0, upper_limit], title=t("col_gap_ratio"))
figure.update_yaxes(visible=False, range=[0, 1])
figure.update_layout(showlegend=False)
ui.plot(figure, height=220)
ui.source_note()
