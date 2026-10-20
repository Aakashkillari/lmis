import plotly.graph_objects as go
import streamlit as st

from lmis import config, gaps, ui
from lmis.ui import t

result = ui.data()
frame = result["gaps"]

st.header(t("overview_title"))
st.write(t("overview_intro"))

columns = st.columns(5)
ui.kpi(columns[0], t("kpi_demand"), ui.number(frame["forecast_demand"].sum()), t("kpi_demand_sub"))
ui.kpi(columns[1], t("kpi_supply"), ui.number(frame["supply"].sum()), t("kpi_supply_sub"))
ui.kpi(columns[2], t("kpi_oversupply"), str(int((frame["status"] == "Oversupply").sum())), t("kpi_pairs_sub", total=len(frame)))
ui.kpi(columns[3], t("kpi_shortage"), str(int((frame["status"] == "Shortage").sum())), t("kpi_pairs_sub", total=len(frame)))
ui.kpi(columns[4], t("kpi_warnings"), str(len(result["warnings"])), t("kpi_warnings_sub", months=config.WARNING_HORIZON))
st.write("")
ui.source_note()

ranked_columns = [("rank", "text")] + ui.GAP_COLUMNS

st.subheader(t("top_oversupply"))
ui.table(gaps.ranked(frame, "Oversupply", 10), ranked_columns)
ui.source_note()

st.subheader(t("top_shortage"))
ui.table(gaps.ranked(frame, "Shortage", 10), ranked_columns)
ui.status_legend()
ui.source_note()

st.subheader(t("status_by_state"))
counts = frame.pivot_table(index="state", columns="status", values="trade", aggfunc="count", fill_value=0)
order = [band["status"] for band in config.STATUS_BANDS]
counts = counts.reindex(columns=order, fill_value=0).reset_index()
counts.columns = ["state"] + order
state_view = counts.rename(columns={s: ui.status_text(s) for s in order}).rename(columns={"state": t("col_state")})
st.dataframe(state_view, hide_index=True, width="stretch")

figure = go.Figure()
for status in order:
    background, text = config.STATUS_COLOURS[status]
    figure.add_bar(
        y=counts["state"], x=counts[status], name=ui.status_text(status), orientation="h",
        marker=dict(color=background, line=dict(color=text, width=1)),
        text=counts[status], textposition="inside", textfont=dict(color=text),
    )
figure.update_layout(barmode="stack", xaxis_title=t("axis_pairs"))
ui.plot(figure, height=300)
ui.source_note()
