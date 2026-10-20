import streamlit as st

from pramaan import web
from pramaan.core import choose, data, lang, pick

result = data()
event = web.dashboard(result, lang(), pick("district", "Krishnagiri"), pick("trade", "EV Service Technician"), pick("sector", "all"))

if event.open:
    request = event.open
    choose(district=request["district"], trade=request["trade"], sector=request.get("sector", "all"))
    if request["page"] == "plan":
        st.session_state["plan_tab"] = request.get("tab") or "moves"
        st.switch_page(web.PAGES[2])
    st.switch_page(web.PAGES[1])
