import plotly.graph_objects as go
import streamlit as st

from lmis import gaps, ui
from lmis.ui import t

result = ui.data()
frame, chosen = ui.place_filters(result["gaps"], "drill")

all_value = ui.all_option()
crumb = [t("national")]
if chosen["state"] != all_value:
    crumb.append(chosen["state"])
if chosen["district"] != all_value:
    crumb.append(chosen["district"])
if chosen["trade"] != all_value:
    crumb.append(chosen["trade"])

st.header(t("drill_title"))
st.markdown(f'<div class="crumb">{" &rsaquo; ".join(crumb)}</div>', unsafe_allow_html=True)

if frame.empty:
    st.info(t("no_rows"))
    st.stop()

if chosen["state"] == all_value:
    level, level_label = "state", t("col_state")
elif chosen["district"] == all_value:
    level, level_label = "district", t("col_district")
else:
    level, level_label = "trade", t("col_trade")

summary = gaps.rollup(frame, level).sort_values("mismatch_people", ascending=False)

st.subheader(t("drill_compare", level=level_label))
ui.table(summary, [
    (level, "text"),
    ("sanctioned_seats", "int"),
    ("supply", "int"),
    ("forecast_demand", "int"),
    ("gap_ratio", "ratio"),
    ("status", "status"),
    ("oversupply_pairs", "int"),
    ("shortage_pairs", "int"),
    ("mismatch_people", "int"),
])
ui.source_note()

figure = go.Figure()
figure.add_bar(x=summary[level], y=summary["forecast_demand"], name=t("col_forecast_demand"), marker_color=ui.NAVY)
figure.add_bar(x=summary[level], y=summary["supply"], name=t("col_supply"), marker_color=ui.SAFFRON)
figure.update_layout(barmode="group", yaxis_title=t("axis_people"))
ui.plot(figure, height=340)
ui.source_note()

st.subheader(t("drill_pairs"))
st.caption(t("drill_pairs_hint"))
ui.table(gaps.ranked(frame), [("rank", "text")] + ui.GAP_COLUMNS + [("current_status", "status")], height=460)
ui.status_legend()
ui.source_note()
