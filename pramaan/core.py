import streamlit as st

from pramaan import model, settings as s
from pramaan.text import translate

LANGUAGES = {"en": "English", "ta": "தமிழ்", "hi": "हिन्दी"}
TRADE_INFO = {t["trade"]: t for t in s.TRADES}


def lang():
    return st.session_state.get("lang", "en")


def t(key, **values):
    return translate(key, lang(), **values)


def status_label(status):
    return t(f"status_{status}")


def sector_label(sector):
    return t(f"sector_{sector}")


@st.cache_resource(show_spinner=False)
def cached_build():
    return model.build()


def data():
    with st.spinner(t("loading")):
        return cached_build()


def pick(name, default):
    return st.session_state.get(f"pick_{name}", default)


def choose(**values):
    for name, value in values.items():
        st.session_state[f"pick_{name}"] = value


def updated_badge():
    return f'<span class="badge"><span class="dot"></span>{t("data_through")} <b>{data()["updated"]}</b></span>'
