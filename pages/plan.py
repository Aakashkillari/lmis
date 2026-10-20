import streamlit as st

from pramaan import charts, model, settings as s, theme
from pramaan.core import data, status_label, t, updated_badge

result = data()
gaps = result["gaps"]

theme.page_header(t("crumb_plan"), t("plan_title"), t("plan_sub"), updated_badge())

tab_moves, tab_emerging, tab_warnings = st.tabs([t("tab_moves"), t("tab_emerging"), t("tab_warnings")])

with tab_moves:
    controls = st.columns([2, 3], vertical_alignment="bottom")
    same_sector = controls[0].toggle(t("same_sector"), value=True, key="plan_same_sector")
    full = model.reallocate(gaps, same_sector=same_sector)
    total = int(full["seats"].sum()) if not full.empty else 0
    budget = controls[1].slider(t("budget"), 0, max(total, 10), total, 10, key=f"plan_budget_{same_sector}") if total else 0
    moves = model.reallocate(gaps, same_sector=same_sector, budget=budget)
    after = model.apply_moves(gaps, moves)
    columns = st.columns(4)
    theme.kpi(columns[0], t("kpi_moved"), theme.indian(moves["seats"].sum()), t("kpi_moved_note", total=theme.indian(gaps["seats"].sum())), "#12305B")
    theme.kpi(columns[1], t("kpi_short_pairs"), f'{int((gaps["status"] == "Shortage").sum())} → {int((after["status"] == "Shortage").sum())}', t("before_after"), "#B03A3A")
    theme.kpi(columns[2], t("kpi_over_pairs"), f'{int((gaps["status"] == "Oversupply").sum())} → {int((after["status"] == "Oversupply").sum())}', t("before_after"), "#3A63A8")
    theme.kpi(columns[3], t("kpi_mismatch"), f'{theme.indian(gaps["severity"].sum())} → {theme.indian(after["severity"].sum())}', t("kpi_mismatch_note"), "#3F8A4E")
    st.write("")
    if moves.empty:
        st.info(t("no_moves"))
    else:
        with theme.card(t("sankey_title"), t("sankey_tag"), t("sankey_caption")):
            st.plotly_chart(charts.sankey(moves, t("seats_word")), width="stretch", config=charts.CONFIG)
        with theme.card(t("moves_title"), t("moves_tag", count=len(moves))):
            view = moves.copy()
            view["from"] = view["from_short"] + " · " + view["from_district"]
            view["to"] = view["to_short"] + " · " + view["to_district"]
            view["from_change"] = [f"{a:.2f} → {b:.2f}" for a, b in zip(view["from_before"], view["from_after"])]
            view["to_change"] = [f"{a:.2f} → {b:.2f}" for a, b in zip(view["to_before"], view["to_after"])]
            theme.table(view, [("from", t("col_from"), "text"), ("to", t("col_to"), "text"), ("seats", t("col_seats"), "int"), ("from_change", t("col_from_ratio"), "text"), ("to_change", t("col_to_ratio"), "text")])
            st.download_button(t("download"), moves.to_csv(index=False).encode("utf-8"), file_name="pramaan_seat_moves.csv", mime="text/csv", key="dl_moves")

with tab_emerging:
    threshold = st.slider(t("growth_threshold"), 0.05, 0.40, s.EMERGING_GROWTH, 0.05, format="%.2f", key="plan_threshold")
    radar = gaps.groupby(["trade", "short", "sector"], as_index=False).agg(demand=("demand", "sum"), supply=("supply", "sum"), last_12m=("last_12m", "sum"))
    radar["growth"] = radar["demand"] / radar["last_12m"] - 1
    radar["ratio"] = radar["supply"] / radar["demand"]
    radar["status"] = radar["ratio"].apply(model.status_for)
    emerging = radar[radar["growth"] > threshold].sort_values("growth", ascending=False)
    columns = st.columns(3)
    theme.kpi(columns[0], t("kpi_emerging"), str(len(emerging)), t("kpi_emerging_note", value=f"{threshold:.0%}"), "#E07A10")
    lead = radar.sort_values("growth", ascending=False).iloc[0]
    theme.kpi(columns[1], t("kpi_fastest"), lead["short"], f"{lead['growth']:+.0%} {t('per_year')}", "#3A63A8")
    theme.kpi(columns[2], t("kpi_emerging_short"), str(int((emerging["status"] == "Shortage").sum())), t("kpi_emerging_short_note"), "#B03A3A")
    st.write("")
    left, right = st.columns([3, 2], gap="medium")
    with left:
        with theme.card(t("quadrant_title"), t("quadrant_tag"), t("quadrant_caption")):
            st.plotly_chart(charts.quadrant(radar, threshold, t("axis_growth"), t("hover_ratio"), status_label), width="stretch", config=charts.CONFIG)
    with right:
        with theme.card(t("growth_title"), t("growth_tag")):
            st.plotly_chart(charts.growth_bars(radar, threshold, t("axis_growth")), width="stretch", config=charts.CONFIG)

with tab_warnings:
    warnings = result["warnings"]
    months = [str(m) for m in result["forecasts"]["month"].drop_duplicates().sort_values().head(s.WARNING_MONTHS)]
    with theme.card(t("timeline_title"), t("timeline_tag", months=s.WARNING_MONTHS), t("timeline_caption")):
        st.plotly_chart(charts.warning_timeline(warnings, months, status_label, t("axis_count")), width="stretch", config=charts.CONFIG)
    with theme.card(t("warn_table_title"), t("warn_table_tag", count=len(warnings))):
        view = warnings.copy()
        view["month"] = view["month"].astype(str)
        view["now"] = [theme.chip(x, status_label(x)) for x in view["current_status"]]
        view["next"] = [theme.chip(x, status_label(x)) for x in view["projected_status"]]
        theme.table(view, [("month", t("col_month"), "text"), ("district", t("col_district"), "text"), ("trade", t("col_trade"), "text"), ("now", t("col_now"), "html"), ("next", t("col_next"), "html"), ("people", t("col_people"), "int")])
        st.download_button(t("download"), warnings.to_csv(index=False).encode("utf-8"), file_name="pramaan_early_warnings.csv", mime="text/csv", key="dl_warnings")
