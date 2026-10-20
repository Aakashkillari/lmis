import streamlit as st

from lmis import config, ui
from lmis.ui import t

result = ui.data()
warnings = result["warnings"]

st.header(t("warnings_title"))
st.write(t("warnings_intro", months=config.WARNING_HORIZON))

frame, _ = ui.place_filters(warnings, "warn", show_trade=False)
directions = [ui.all_option(), "Towards shortage", "Towards oversupply"]
direction = st.radio(t("filter_direction"), directions, horizontal=True, format_func=lambda d: d if d == ui.all_option() else t(f"dir_{d}"))
if direction != ui.all_option():
    frame = frame[frame["direction"] == direction]

columns = st.columns(3)
ui.kpi(columns[0], t("kpi_warnings"), str(len(frame)))
ui.kpi(columns[1], t("dir_Towards shortage"), str(int((frame["direction"] == "Towards shortage").sum())))
ui.kpi(columns[2], t("dir_Towards oversupply"), str(int((frame["direction"] == "Towards oversupply").sum())))
st.write("")

if frame.empty:
    st.info(t("no_rows"))
else:
    view = frame.copy()
    view["direction"] = view["direction"].map(lambda d: t(f"dir_{d}"))
    ui.table(view, [
        ("crossing_month", "month"),
        ("months_ahead", "text"),
        ("state", "text"),
        ("district", "text"),
        ("trade", "text"),
        ("current_status", "status"),
        ("current_ratio", "ratio"),
        ("direction", "text"),
        ("projected_status", "status"),
        ("ratio_at_crossing", "ratio"),
        ("severity", "int"),
    ], height=520)
    ui.status_legend()
ui.source_note()
