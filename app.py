import streamlit as st

from lmis import ui

st.set_page_config(page_title="LMIS | MSDE", layout="wide", initial_sidebar_state="expanded")

if "lang" not in st.session_state:
    st.session_state["lang"] = "en"

ui.apply_style()

with st.sidebar:
    choice = st.radio("Language / भाषा", ["English", "हिन्दी"], index=0 if ui.lang() == "en" else 1, horizontal=True)
    st.session_state["lang"] = "en" if choice == "English" else "hi"

PAGES = [
    ("views/overview.py", "nav_overview", True),
    ("views/drilldown.py", "nav_drilldown", False),
    ("views/trade_forecast.py", "nav_forecast", False),
    ("views/warnings.py", "nav_warnings", False),
    ("views/whatif.py", "nav_whatif", False),
    ("views/reallocation.py", "nav_reallocation", False),
    ("views/radar.py", "nav_radar", False),
    ("views/normaliser.py", "nav_normaliser", False),
    ("views/methodology.py", "nav_methodology", False),
    ("views/export.py", "nav_export", False),
]

pages = [st.Page(path, title=ui.t(key), default=default) for path, key, default in PAGES]
current = st.navigation(pages, position="sidebar")

with st.sidebar:
    st.caption(ui.t("sidebar_note"))

ui.header()
ui.data()
current.run()
