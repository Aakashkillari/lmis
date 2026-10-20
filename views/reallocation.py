import streamlit as st

from lmis import config, recommend, ui
from lmis.ui import t

result = ui.data()
frame = result["gaps"]

st.header(t("realloc_title"))
st.write(t("realloc_intro"))

columns = st.columns([1, 1, 2])
states = [ui.all_option()] + list(config.STATES)
state = columns[0].selectbox(t("filter_state"), states, key="realloc_state")
same_sector = columns[1].checkbox(t("same_sector"), value=True)

moves = recommend.reallocate(frame, same_sector=same_sector)
after = recommend.apply_moves(frame, moves)
if state != ui.all_option():
    moves = moves[moves["state"] == state]
    before_scope = frame[frame["state"] == state]
    after_scope = after[after["state"] == state]
else:
    before_scope, after_scope = frame, after

columns = st.columns(4)
ui.kpi(columns[0], t("seats_moved_total"), ui.number(moves["seats_moved"].sum()), t("moves_sub", count=len(moves)))
ui.kpi(columns[1], t("shortage_pairs_change"), f"{int((before_scope['status'] == 'Shortage').sum())} &rarr; {int((after_scope['status'] == 'Shortage').sum())}")
ui.kpi(columns[2], t("oversupply_pairs_change"), f"{int((before_scope['status'] == 'Oversupply').sum())} &rarr; {int((after_scope['status'] == 'Oversupply').sum())}")
ui.kpi(columns[3], t("mismatch_change"), f"{ui.number(before_scope['severity'].sum())} &rarr; {ui.number(after_scope['severity'].sum())}")
st.write("")

st.subheader(t("realloc_table"))
if moves.empty:
    st.info(t("no_rows"))
else:
    ui.table(moves, [
        ("state", "text"),
        ("from_district", "text"),
        ("from_trade", "text"),
        ("to_district", "text"),
        ("to_trade", "text"),
        ("seats_moved", "int"),
        ("from_ratio_before", "ratio"),
        ("from_ratio_after", "ratio"),
        ("from_status_after", "status"),
        ("to_ratio_before", "ratio"),
        ("to_ratio_after", "ratio"),
        ("to_status_after", "status"),
    ], height=480)
    ui.status_legend()
st.caption(t("realloc_rule"))
ui.source_note()
