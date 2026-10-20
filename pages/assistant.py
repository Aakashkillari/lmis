import sys
from itertools import chain

import streamlit as st

from pramaan import assistant, charts, model, settings as s, theme
from pramaan.core import data, lang, sector_label, t

result = data()
gaps = result["gaps"]

if assistant.connected():
    badge = f'<span class="badge"><span class="dot"></span>{t("ai_on")} <b>{assistant.model_name()}</b></span>'
else:
    badge = f'<span class="badge"><span class="dot off"></span>{t("ai_off")}</span>'
theme.page_header(t("crumb_assistant"), t("assistant_title"), t("assistant_sub"), badge)


def show_evidence(question):
    kind, name, frame = assistant.evidence(question, gaps)
    st.markdown(f'<div class="answer-evidence">{t("evidence", name=name)}</div>', unsafe_allow_html=True)
    sectors = assistant.sector_frame(frame).assign(sector=lambda f: f["sector"].map(sector_label))
    left, right = st.columns([2, 3])
    with left:
        st.plotly_chart(charts.sector_bars(sectors, t("legend_jobs"), t("legend_trainees"), t("axis_people")), width="stretch", config=charts.CONFIG, key=f"ev_sector_{len(st.session_state['chat'])}_{name}")
    with right:
        st.plotly_chart(charts.trade_bars(frame, t("legend_jobs"), t("legend_trainees"), t("axis_people")), width="stretch", config=charts.CONFIG, key=f"ev_trade_{len(st.session_state['chat'])}_{name}")


if "chat" not in st.session_state:
    st.session_state["chat"] = []

suggestions = [t("q1"), t("q2"), t("q3"), t("q4"), t("q5")]
picked = st.pills(t("try_asking"), suggestions, key=f"suggest_{len(st.session_state['chat'])}")

for turn in st.session_state["chat"]:
    with st.chat_message(turn["role"], avatar=":material/person:" if turn["role"] == "user" else ":material/insights:"):
        st.markdown(turn["content"])
        if turn["role"] == "assistant" and assistant.wants_evidence(turn["question"]):
            show_evidence(turn["question"])

question = st.chat_input(t("ask_placeholder")) or picked
if question:
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(question)
    with st.chat_message("assistant", avatar=":material/insights:"):
        moves = model.reallocate(gaps)
        history = [{"role": x["role"], "content": x["content"]} for x in st.session_state["chat"]]
        answer_slot = st.empty()
        if assistant.wants_evidence(question):
            show_evidence(question)
        answer = ""
        if assistant.connected():
            answer_slot.caption(t("ai_loading"))
            try:
                stream = assistant.stream_answer(question, history, result, moves, lang())
                first = next(stream)
                with answer_slot.container():
                    answer = st.write_stream(chain([first], stream))
            except StopIteration:
                print("[pramaan] llm returned no text", file=sys.stderr, flush=True)
            except Exception as error:
                print(f"[pramaan] llm error: {type(error).__name__}: {error}", file=sys.stderr, flush=True)
        if not str(answer).strip():
            answer = assistant.fallback_answer(question, result, t)
            with answer_slot.container():
                st.markdown(answer)
                if assistant.connected():
                    st.caption(t("ai_fallback"))
    st.session_state["chat"] += [
        {"role": "user", "content": question, "question": question},
        {"role": "assistant", "content": str(answer), "question": question},
    ]
    st.rerun()

if st.session_state["chat"]:
    if st.button(t("clear_chat"), key="clear_chat"):
        st.session_state["chat"] = []
        st.rerun()
