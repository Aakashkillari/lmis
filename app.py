from pathlib import Path

import streamlit as st

from pramaan import theme, web
from pramaan.core import choose, data, lang, t

ROOT = Path(__file__).resolve().parent
MARK = str(ROOT / "assets" / "pramaan_mark.svg")

st.set_page_config(page_title="Pramaan · Skill Demand Intelligence", page_icon=MARK, layout="wide", initial_sidebar_state="collapsed")
theme.apply()

if "lang" not in st.session_state:
    st.session_state["lang"] = "en"

pages = [
    st.Page(web.PAGES[0], title=t("nav_dashboard"), default=True),
    st.Page(web.PAGES[1], title=t("nav_explore")),
    st.Page(web.PAGES[2], title=t("nav_plan")),
    st.Page(web.PAGES[3], title=t("nav_assistant")),
    st.Page(web.PAGES[4], title=t("nav_about")),
]
current = st.navigation(pages, position="hidden")
active = next((i for i, page in enumerate(pages) if page.url_path == current.url_path), 0)

web.header(active, lang(), choose)
data()
current.run()
