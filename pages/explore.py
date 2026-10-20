import streamlit as st

from pramaan import charts, model, settings as s, theme
from pramaan.core import TRADE_INFO, choose, data, pick, sector_label, status_label, t, updated_badge

result = data()
gaps = result["gaps"]

theme.page_header(t("crumb_explore"), t("explore_title"), t("explore_sub"), updated_badge())

districts = list(s.DISTRICTS)
trades = [x["trade"] for x in s.TRADES]
district = st.pills(t("pick_district"), districts, default=pick("district", "Coimbatore"), key="explore_district") or pick("district", "Coimbatore")
trade = st.selectbox(t("pick_trade"), trades, index=trades.index(pick("trade", "EV Service Technician")), format_func=lambda x: f"{x}  ·  {sector_label(TRADE_INFO[x]['sector'])}", key="explore_trade")
choose(district=district, trade=trade)

row = gaps[(gaps["district"] == district) & (gaps["trade"] == trade)].iloc[0]
info = TRADE_INFO[trade]
st.markdown(
    f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:8px 0 14px 0">'
    f'<span style="font-size:20px;font-weight:600;letter-spacing:-0.02em;color:rgba(0,0,0,.85)">{t("pair_heading", trade=trade, district=district)}</span>'
    f'{theme.chip(row["status"], status_label(row["status"]))}'
    f'<span class="tag">NCO {info["nco"]}</span><span class="tag">QP {info["qp"]}</span><span class="tag">NSQF {info["nsqf"]}</span></div>',
    unsafe_allow_html=True,
)

band = int(s.BAND_LEVEL * 100)
backtest = result["backtest"]
error = backtest[(backtest["district"] == district) & (backtest["trade"] == trade)]["mape"].iloc[0]
columns = st.columns(4)
theme.kpi(columns[0], t("kpi_jobs"), theme.indian(row["demand"]), t("range_note", band=band, low=theme.indian(row["demand_low"]), high=theme.indian(row["demand_high"])), "#3A63A8")
theme.kpi(columns[1], t("kpi_trainees"), theme.indian(row["supply"]), t("seats_note", seats=theme.indian(row["seats"])), "#E07A10")
theme.kpi(columns[2], t("kpi_gap"), theme.signed(row["supply"] - row["demand"]), t("gap_note") if row["gap"] < 0 else t("surplus_note"), "#B03A3A" if row["gap"] < 0 else "#3A63A8")
theme.kpi(columns[3], t("kpi_accuracy"), f"{100 - error:.0f}%", t("accuracy_note", months=s.BACKTEST_MONTHS), "#3F8A4E")
st.write("")

history = model.series(result["index"], district, trade)
future = model.series(result["forecasts"], district, trade)
with theme.card(t("forecast_title"), t("forecast_tag"), t("forecast_caption")):
    labels = {"band": t("legend_band", band=band), "history": t("legend_history"), "forecast": t("legend_forecast"), "supply": t("legend_supply_month")}
    st.plotly_chart(charts.forecast_chart(history, future, row["supply"], labels, t("axis_openings")), width="stretch", config=charts.CONFIG)

left, right = st.columns([5, 4], gap="medium")
with left:
    with theme.card(t("whatif_title"), t("whatif_tag"), t("whatif_caption")):
        seats = st.slider(t("whatif_seats"), 0, int(row["seats"]) * 3 + 100, int(row["seats"]), 10, key=f"seats_{district}_{trade}")
        rates = st.columns(2)
        completion = rates[0].slider(t("whatif_completion"), 0.5, 1.0, float(row["completion"]), 0.01, key=f"comp_{district}_{trade}")
        certification = rates[1].slider(t("whatif_certification"), 0.5, 1.0, float(row["certification"]), 0.01, key=f"cert_{district}_{trade}")
        after = model.with_seats(gaps, district, trade, seats, completion, certification)
        after = after[(after["district"] == district) & (after["trade"] == trade)].iloc[0]
        st.plotly_chart(charts.whatif_strip(row["ratio"], after["ratio"], t("before"), t("after")), width="stretch", config=charts.CONFIG)
        result_columns = st.columns(3)
        theme.kpi(result_columns[0], t("kpi_trainees_short"), theme.indian(after["supply"]), t("was", value=theme.indian(row["supply"])), "#E07A10")
        theme.kpi(result_columns[1], t("hover_ratio"), f"{after['ratio']:.2f}", t("was", value=f"{row['ratio']:.2f}"), "#12305B")
        theme.kpi(result_columns[2], t("status"), theme.chip(after["status"], status_label(after["status"])), t("was", value=status_label(row["status"])), "#12305B")
        balance = row["demand"] / (completion * certification)
        st.caption(t("balance_hint", seats=theme.indian(round(balance / 10) * 10)))

with right:
    path = model.ratio_path(result["index"], result["forecasts"], district, trade, row["supply"])
    with theme.card(t("path_title"), t("path_tag"), t("path_caption")):
        st.plotly_chart(charts.ratio_path(path, status_label, t("hover_ratio")), width="stretch", config=charts.CONFIG)
    with theme.card(t("signal_title"), t("signal_tag"), t("signal_caption")):
        st.plotly_chart(charts.contributions(history, lambda x: t(f"src_{x}"), t("legend_index"), t("axis_index")), width="stretch", config=charts.CONFIG)

with st.expander(t("monthly_table")):
    table = path.copy()
    table["lower"] = future["lower"].to_numpy()
    table["upper"] = future["upper"].to_numpy()
    table["month"] = table["month"].astype(str)
    table["status_html"] = [theme.chip(x, status_label(x)) for x in table["status"]]
    theme.table(table, [("month", t("col_month"), "text"), ("forecast", t("col_forecast"), "int"), ("lower", t("col_low"), "int"), ("upper", t("col_high"), "int"), ("rolling_demand", t("col_rolling"), "int"), ("ratio", t("hover_ratio"), "ratio"), ("status_html", t("status"), "html")])
    st.download_button(t("download"), table.drop(columns=["status_html"]).to_csv(index=False).encode("utf-8"), file_name=f"pramaan_{district}_{info['short']}.csv", mime="text/csv")
