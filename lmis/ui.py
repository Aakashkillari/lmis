import streamlit as st

from lmis import config, pipeline
from lmis.i18n import translate

NAVY = "#0B2E59"
SAFFRON = "#C25E00"
GREY = "#5B6573"
BAND = "rgba(11, 46, 89, 0.14)"

CSS = """
<style>
.stApp { background: #FFFFFF; }
html, body, [class*="css"] { font-size: 16px; }
h1, h2, h3, h4 { color: #0B2E59; font-weight: 600; letter-spacing: 0; }
h1 { font-size: 1.6rem; margin-bottom: 0.2rem; }
h2 { font-size: 1.25rem; }
h3 { font-size: 1.08rem; }
[data-testid="stSidebar"] { background: #F4F6FA; border-right: 1px solid #D0D7E2; }
.lmis-head { border-top: 4px solid #E07B00; border-bottom: 2px solid #0B2E59; padding: 8px 0 8px 0; margin-bottom: 14px; }
.lmis-head .ministry { font-size: 0.85rem; color: #333; text-transform: uppercase; letter-spacing: 0.04em; }
.lmis-head .system { font-size: 1.35rem; color: #0B2E59; font-weight: 700; }
.lmis-head .scope { font-size: 0.85rem; color: #444; }
.kpi { border: 1px solid #C9D1DD; border-left: 4px solid #0B2E59; padding: 8px 12px; background: #FFFFFF; height: 100%; }
.kpi .label { font-size: 0.82rem; color: #333; }
.kpi .value { font-size: 1.45rem; font-weight: 700; color: #0B2E59; }
.kpi .sub { font-size: 0.78rem; color: #444; }
.chip { display: inline-block; padding: 1px 8px; border: 1px solid #8A94A3; font-size: 0.82rem; font-weight: 600; margin-right: 6px; }
.note { font-size: 0.8rem; color: #3A3A3A; border-top: 1px solid #E1E5EC; padding-top: 4px; margin-bottom: 18px; }
.crumb { font-size: 0.9rem; color: #0B2E59; font-weight: 600; margin-bottom: 8px; }
.formula { font-family: Consolas, monospace; background: #F4F6FA; border: 1px solid #D0D7E2; padding: 8px 12px; margin: 6px 0; }
a:focus, button:focus, [tabindex]:focus { outline: 3px solid #E07B00 !important; outline-offset: 1px; }
</style>
"""


def lang():
    return st.session_state.get("lang", "en")


def t(key, **values):
    return translate(key, lang(), **values)


@st.cache_resource(show_spinner=False)
def get_data():
    return pipeline.load()


def data():
    with st.spinner(t("loading")):
        return get_data()


def apply_style():
    st.markdown(CSS, unsafe_allow_html=True)


def header():
    st.markdown(
        f"""<div class="lmis-head">
        <div class="ministry">{t("ministry")}</div>
        <div class="system">{t("system_name")}</div>
        <div class="scope">{t("scope_line")}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def source_note():
    refreshed = data()["refreshed"]
    st.markdown(f'<div class="note">{t("source_note")} {t("last_refreshed")}: {refreshed}.</div>', unsafe_allow_html=True)


def status_text(status):
    return t(f"status_{status}")


def chip(status):
    background, text = config.STATUS_COLOURS[status]
    return f'<span class="chip" style="background:{background};color:{text}">{status_text(status)}</span>'


def status_legend():
    chips = "".join(chip(band["status"]) for band in config.STATUS_BANDS)
    st.markdown(f'<div style="margin:4px 0 6px 0">{chips}</div>', unsafe_allow_html=True)


def kpi(column, label, value, sub=""):
    column.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)


def number(value):
    return f"{value:,.0f}"


FORMATS = {
    "int": "{:,.0f}",
    "ratio": "{:.2f}",
    "pct": "{:+.1%}",
    "rate": "{:.0%}",
    "dec": "{:.1f}",
}


def table(frame, columns, height=None, key=None):
    view = frame[[c for c, _ in columns]].copy()
    formats = {}
    status_columns = []
    for column, kind in columns:
        if kind == "status":
            view[column] = view[column].map(status_text)
            status_columns.append(column)
        elif kind == "month":
            view[column] = view[column].astype(str)
        elif kind in FORMATS:
            formats[column] = FORMATS[kind]
    labels = {column: t(f"col_{column}") for column, _ in columns}
    colour_by_label = {status_text(s): c for s, c in config.STATUS_COLOURS.items()}

    def paint(value):
        background, text = colour_by_label.get(value, ("#FFFFFF", "#1A1A1A"))
        return f"background-color: {background}; color: {text}; font-weight: 600"

    view = view.rename(columns=labels)
    styled = view.style.format({labels[c]: f for c, f in formats.items()})
    if status_columns:
        styled = styled.map(paint, subset=[labels[c] for c in status_columns])
    options = {"hide_index": True, "width": "stretch"}
    if height:
        options["height"] = height
    st.dataframe(styled, key=key, **options)


def chart_layout(figure, height=380):
    figure.update_layout(
        template="simple_white",
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(family="Segoe UI, Noto Sans, Arial, sans-serif", size=13, color="#1A1A1A"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(bgcolor="#FFFFFF"),
    )
    figure.update_xaxes(showgrid=False, linecolor="#8A94A3")
    figure.update_yaxes(showgrid=True, gridcolor="#E6E9EF", linecolor="#8A94A3")
    return figure


def plot(figure, height=380):
    st.plotly_chart(chart_layout(figure, height), width="stretch", config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})


def all_option():
    return t("all")


def place_filters(gaps, key, show_trade=True, columns=None):
    columns = columns or st.columns(4 if show_trade else 3)
    states = [all_option()] + list(config.STATES)
    state = columns[0].selectbox(t("filter_state"), states, key=f"{key}_state")
    districts = [all_option()]
    if state != all_option():
        districts += config.STATES[state]
    district = columns[1].selectbox(t("filter_district"), districts, key=f"{key}_district")
    sectors = [all_option()] + list(config.SECTORS)
    sector = columns[2].selectbox(t("filter_sector"), sectors, key=f"{key}_sector")
    trade = all_option()
    if show_trade:
        trades = [all_option()] + [x["trade"] for x in config.TRADES if sector in (all_option(), x["sector"])]
        trade = columns[3].selectbox(t("filter_trade"), trades, key=f"{key}_trade")
    frame = gaps
    if state != all_option():
        frame = frame[frame["state"] == state]
    if district != all_option():
        frame = frame[frame["district"] == district]
    if sector != all_option():
        frame = frame[frame["sector"] == sector]
    if trade != all_option():
        frame = frame[frame["trade"] == trade]
    return frame, {"state": state, "district": district, "sector": sector, "trade": trade}


def pair_picker(key, default=("Tamil Nadu", "Coimbatore", "EV Service Technician")):
    columns = st.columns(3)
    states = list(config.STATES)
    state = columns[0].selectbox(t("filter_state"), states, index=states.index(default[0]), key=f"{key}_state")
    districts = config.STATES[state]
    district_index = districts.index(default[1]) if default[1] in districts else 0
    district = columns[1].selectbox(t("filter_district"), districts, index=district_index, key=f"{key}_district")
    trades = [x["trade"] for x in config.TRADES]
    trade = columns[2].selectbox(t("filter_trade"), trades, index=trades.index(default[2]), key=f"{key}_trade")
    return state, district, trade


def pair_row(gaps, state, district, trade):
    match = gaps[(gaps["state"] == state) & (gaps["district"] == district) & (gaps["trade"] == trade)]
    return match.iloc[0]


GAP_COLUMNS = [
    ("state", "text"),
    ("district", "text"),
    ("trade", "text"),
    ("nco", "text"),
    ("nsqf", "text"),
    ("sanctioned_seats", "int"),
    ("supply", "int"),
    ("forecast_demand", "int"),
    ("gap_people", "int"),
    ("gap_ratio", "ratio"),
    ("status", "status"),
]
