import pandas as pd
import streamlit as st

from lmis import normalise, ui
from lmis.ui import t

result = ui.data()

st.header(t("norm_title"))
st.write(t("norm_intro"))

text = st.text_area(t("norm_input"), value="Urgent requirement: E V mechanic for electric scooter service centre, Hosur. ITI pass.", height=100)

if text.strip():
    matches = pd.DataFrame(normalise.match_title(text, top=3))
    best = matches.iloc[0]
    band = t("conf_high") if best["confidence"] >= 0.9 else t("conf_medium") if best["confidence"] >= 0.75 else t("conf_low")
    columns = st.columns(3)
    ui.kpi(columns[0], t("norm_best"), best["trade"], f"{t('col_matched_alias')}: {best['matched_alias']}")
    ui.kpi(columns[1], t("col_nco"), best["nco"], f"{t('col_qp')}: {best['qp']}")
    ui.kpi(columns[2], t("col_confidence"), f"{best['confidence']:.0%}", band)
    st.write("")
    st.subheader(t("norm_candidates"))
    ui.table(matches, [("trade", "text"), ("nco", "text"), ("qp", "text"), ("matched_alias", "text"), ("confidence", "rate")])
    st.caption(t("norm_rule"))

st.subheader(t("norm_applied"))
st.caption(t("norm_applied_hint"))
ui.table(result["title_mapping"], [("raw_title", "text"), ("trade", "text"), ("nco", "text"), ("confidence", "rate")], height=360)
ui.source_note()

st.subheader(t("norm_lookup"))
ui.table(normalise.alias_table(), [("alias", "text"), ("trade", "text"), ("nco", "text"), ("qp", "text")], height=360)
ui.source_note()
