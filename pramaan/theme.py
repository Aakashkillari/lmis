import base64
import html
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
INK = "rgba(0, 0, 0, 0.85)"

STATUS_STYLE = {
    "Shortage": ("#D70015", "rgba(215, 0, 21, 0.10)"),
    "Watch (falling)": ("#C93400", "rgba(201, 52, 0, 0.10)"),
    "Balanced": ("#248A3D", "rgba(36, 138, 61, 0.10)"),
    "Watch (rising)": ("#0071A4", "rgba(0, 113, 164, 0.10)"),
    "Oversupply": ("#8944AB", "rgba(137, 68, 171, 0.10)"),
}

VALUE_COLOURS = {"#B03A3A": "#D70015", "#D9822B": "#C93400", "#3F8A4E": "#248A3D", "#9AA3AF": "rgba(0, 0, 0, 0.5)"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600;700&family=Noto+Sans+Tamil:wght@400;600;700&display=swap');
:root { --accent: #007AFF; --bg: #F5F5F7; --card: #FFFFFF; --line: rgba(0, 0, 0, 0.10); --ink: rgba(0, 0, 0, 0.85); --muted: rgba(0, 0, 0, 0.5);
  --shadow: 0 1px 1px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.04); }
.stApp, .stApp *:not([data-testid="stIconMaterial"]):not(.material-symbols-rounded) { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, "Noto Sans Tamil", "Noto Sans Devanagari", Arial, sans-serif !important; }
.stApp { background: var(--bg); color: var(--ink); }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] { display: none !important; }
[data-testid="stHeader"] { background: transparent; height: 0; }
.block-container { padding: 0 28px 40px 28px !important; max-width: 1440px; }
.st-key-pramaan_header { margin: 0 -28px 0 -28px; width: calc(100% + 56px) !important; position: sticky; top: 0; z-index: 1000; }
.st-key-pramaan_dashboard { margin: 0 -28px; width: calc(100% + 56px) !important; }
.stApp p, .stApp li, .stApp label { font-size: 14px; }

.topline { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; margin: 18px 0 12px 0; }
.crumb { font-size: 12px; color: var(--muted); }
.crumb span { color: var(--muted); }
.page-title { font-size: 24px; font-weight: 600; color: var(--ink); line-height: 1.25; letter-spacing: -0.02em; margin-top: 3px; }
.page-sub { font-size: 13px; color: var(--muted); margin-top: 3px; }
.badge { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--muted); white-space: nowrap; padding-bottom: 4px; }
.badge b { color: var(--ink); font-weight: 600; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: #34C759; display: inline-block; }
.dot.off { background: #B0B0B8; }

.kpi { background: var(--card); border-radius: 14px; padding: 14px 16px; min-height: 104px; box-shadow: var(--shadow); }
.kpi .label { font-size: 12px; color: var(--muted); font-weight: 500; }
.kpi .value { font-size: 28px; font-weight: 600; letter-spacing: -0.03em; color: var(--valuecolour, rgba(0, 0, 0, 0.85)); line-height: 1.25; margin-top: 4px; font-variant-numeric: tabular-nums; }
.kpi .note { font-size: 11px; color: var(--muted); margin-top: 3px; }

[data-testid="stVerticalBlockBorderWrapper"]:has(.card-head) { background: var(--card); border: 0 !important; border-radius: 14px !important; box-shadow: var(--shadow); }
.card-head { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; padding-bottom: 2px; }
.card-title { font-size: 15px; font-weight: 600; color: var(--ink); }
.card-tag { font-size: 11.5px; color: var(--muted); white-space: nowrap; }
.card-caption { font-size: 12.5px; color: var(--muted); margin: 2px 0 0 0; line-height: 1.45; }

.chip { display: inline-block; padding: 2px 9px; border-radius: 99px; font-weight: 600; font-size: 12px; white-space: nowrap; }
.chip:before { content: "■ "; }
.tag { display: inline-block; background: rgba(120, 120, 128, 0.12); border-radius: 6px; padding: 2px 8px; font-size: 11.5px; color: var(--muted); margin-right: 6px; }

.rank { display: grid; grid-template-columns: 22px 1fr auto; gap: 4px 10px; align-items: center; padding: 9px 4px; border-bottom: 1px solid var(--line); }
.rank:last-child { border-bottom: none; }
.rank .n { font-size: 12px; color: var(--muted); font-weight: 600; }
.rank .name { font-size: 13px; font-weight: 600; color: var(--ink); }
.rank .where { font-size: 11.5px; color: var(--muted); font-weight: 400; }
.rank .val { font-size: 12.5px; font-weight: 600; text-align: right; font-variant-numeric: tabular-nums; }
.rank .bar { grid-column: 2 / 4; height: 3px; border-radius: 2px; background: #E8E8ED; overflow: hidden; }
.rank .bar i { display: block; height: 100%; border-radius: 2px; }

.tbl-wrap { border-radius: 10px; overflow: auto; background: #FFFFFF; }
table.tbl { border-collapse: collapse; width: 100%; font-size: 13px; }
table.tbl th { background: #FFFFFF; color: var(--muted); font-weight: 500; text-align: left; padding: 8px 10px; position: sticky; top: 0; z-index: 1; font-size: 11.5px; border-bottom: 1.5px solid rgba(0, 0, 0, 0.85); }
table.tbl td { padding: 8px 10px; border-bottom: 1px solid var(--line); }
table.tbl tr:hover td { background: #F5F5F7; }
table.tbl .num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
table.tbl th.num { text-align: right; }

.steps { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
.step { background: #FFFFFF; border-radius: 14px; padding: 14px 16px; box-shadow: var(--shadow); }
.step .no { width: 24px; height: 24px; border-radius: 7px; background: var(--accent); color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 12px; }
.step .h { font-weight: 600; color: var(--ink); margin-top: 10px; font-size: 14px; }
.step .p { font-size: 12.5px; color: var(--muted); margin-top: 4px; line-height: 1.45; }
@media (max-width: 900px) { .steps { grid-template-columns: 1fr 1fr; } }

.answer-evidence { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; font-weight: 600; margin-top: 6px; }
.stButton button, .stDownloadButton button { border-radius: 8px; font-weight: 500; font-size: 13px; box-shadow: 0 1px 1px rgba(0, 0, 0, 0.04); }
.stButton button[kind="primary"] { background: var(--accent); border-color: var(--accent); }
.stButton button[kind="primary"]:hover { background: #0A6FE8; border-color: #0A6FE8; }
[data-testid="stChatMessage"] { background: #FFFFFF; border-radius: 14px; padding: 12px 14px; box-shadow: var(--shadow); }
div[data-baseweb="select"] > div, .stTextInput input { border-radius: 8px !important; }
.stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { font-size: 13.5px; padding: 8px 0; }
.stTabs [aria-selected="true"] { font-weight: 600; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--accent); }
a:focus-visible, button:focus-visible { outline: 2px solid var(--accent) !important; outline-offset: 2px; }
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)


def mark_uri():
    return "data:image/svg+xml;base64," + base64.b64encode((ROOT / "assets" / "pramaan_mark.svg").read_bytes()).decode()


def indian(value):
    if pd.isna(value):
        return ""
    number = int(round(float(value)))
    sign = "-" if number < 0 else ""
    digits = str(abs(number))
    if len(digits) <= 3:
        return sign + digits
    head, tail = digits[:-3], digits[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return sign + ",".join(groups) + "," + tail


def signed(value):
    text = indian(value)
    return text if text.startswith("-") else "+" + text


def chip(status, label):
    colour, background = STATUS_STYLE[status]
    return f'<span class="chip" style="color:{colour};background:{background}">{html.escape(label)}</span>'


def page_header(crumb, title, subtitle, badge_html=""):
    st.markdown(
        f'<div class="topline"><div><div class="crumb">{crumb}</div><div class="page-title">{title}</div>'
        f'<div class="page-sub">{subtitle}</div></div><div>{badge_html}</div></div>',
        unsafe_allow_html=True,
    )


def kpi(column, label, value, note="", accent=""):
    colour = VALUE_COLOURS.get(accent, INK)
    column.markdown(
        f'<div class="kpi" style="--valuecolour:{colour}"><div class="label">{label}</div><div class="value">{value}</div><div class="note">{note}</div></div>',
        unsafe_allow_html=True,
    )


@contextmanager
def card(title, tag="", caption=""):
    with st.container(border=True):
        st.markdown(f'<div class="card-head"><div class="card-title">{title}</div><div class="card-tag">{tag}</div></div>', unsafe_allow_html=True)
        if caption:
            st.markdown(f'<div class="card-caption">{caption}</div>', unsafe_allow_html=True)
        yield


def rank_list(rows, colour):
    top = max([abs(r["value"]) for r in rows] + [1])
    items = []
    for n, row in enumerate(rows, start=1):
        width = 100 * abs(row["value"]) / top
        items.append(
            f'<div class="rank"><div class="n">{n}</div><div class="name">{html.escape(row["name"])} <span class="where">· {html.escape(row["where"])}</span></div>'
            f'<div class="val" style="color:{colour}">{row["label"]}</div><div class="bar"><i style="width:{width:.0f}%;background:{colour}"></i></div></div>'
        )
    st.markdown("".join(items) or "&nbsp;", unsafe_allow_html=True)


def table(frame, columns, height=None):
    head = "".join(f'<th class="{"num" if kind in ("int", "ratio", "pct", "signed") else ""}">{html.escape(label)}</th>' for _, label, kind in columns)
    rows = []
    for record in frame.to_dict("records"):
        cells = []
        for name, _, kind in columns:
            value = record[name]
            if kind == "int":
                cells.append(f'<td class="num">{indian(value)}</td>')
            elif kind == "signed":
                cells.append(f'<td class="num">{signed(value)}</td>')
            elif kind == "ratio":
                cells.append(f'<td class="num">{value:.2f}</td>')
            elif kind == "pct":
                cells.append(f'<td class="num">{value:+.0%}</td>')
            elif kind == "html":
                cells.append(f"<td>{value}</td>")
            else:
                cells.append(f"<td>{html.escape(str(value))}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    style = f' style="max-height:{height}px"' if height else ""
    st.markdown(f'<div class="tbl-wrap"{style}><table class="tbl"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>', unsafe_allow_html=True)
