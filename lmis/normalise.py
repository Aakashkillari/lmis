import re
from difflib import SequenceMatcher

import pandas as pd

from lmis import config


def clean(text):
    text = text.lower().replace("-", " ")
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def alias_table():
    trades = {t["trade"]: t for t in config.TRADES}
    rows = []
    for trade, aliases in config.TITLE_ALIASES.items():
        for alias in aliases:
            rows.append({"alias": alias, "trade": trade, "nco": trades[trade]["nco"], "qp": trades[trade]["qp"]})
    return pd.DataFrame(rows)


def windows(words, size):
    if len(words) <= size:
        return [" ".join(words)]
    return [" ".join(words[i:i + size]) for i in range(len(words) - size + 1)]


def alias_score(text, alias):
    alias_clean = clean(alias)
    if alias_clean == text:
        return 1.0
    if f" {alias_clean} " in f" {text} ":
        return 0.9 + 0.1 * len(alias_clean) / len(text)
    words = text.split()
    size = len(alias_clean.split())
    best = 0.0
    for size_try in {size, size + 1, max(1, size - 1)}:
        for chunk in windows(words, size_try):
            best = max(best, SequenceMatcher(None, chunk, alias_clean).ratio())
    return best


def match_title(raw, top=3):
    text = clean(raw)
    if not text:
        return []
    scores = {}
    aliases = {}
    for row in alias_table().itertuples():
        score = alias_score(text, row.alias)
        if score > scores.get(row.trade, -1):
            scores[row.trade] = score
            aliases[row.trade] = row.alias
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top]
    trades = {t["trade"]: t for t in config.TRADES}
    return [
        {"trade": trade, "nco": trades[trade]["nco"], "qp": trades[trade]["qp"], "matched_alias": aliases[trade], "confidence": round(score, 2)}
        for trade, score in ranked
    ]


def title_map(raw_titles, min_confidence=0.75):
    rows = []
    for raw in sorted(set(raw_titles)):
        best = match_title(raw, top=1)[0]
        mapped = best["trade"] if best["confidence"] >= min_confidence else None
        rows.append({"raw_title": raw, "trade": mapped, "nco": best["nco"], "confidence": best["confidence"]})
    return pd.DataFrame(rows)


def aggregate_portal(portal_raw):
    mapping = title_map(portal_raw["raw_title"])
    merged = portal_raw.merge(mapping[["raw_title", "trade"]], on="raw_title", how="left")
    merged = merged.dropna(subset=["trade"])
    grouped = merged.groupby(["month", "state", "district", "trade"], as_index=False)["postings"].sum()
    return grouped.rename(columns={"postings": "portal"}), mapping


def zscore(series):
    spread = series.std(ddof=0)
    if spread == 0:
        return series * 0
    return (series - series.mean()) / spread


def demand_index(signals):
    keys = ["state", "district", "trade"]
    frame = signals.copy()
    frame["index"] = 0.0
    for source, spec in config.SOURCES.items():
        frame[f"z_{source}"] = frame.groupby(keys)[source].transform(zscore)
        frame[f"c_{source}"] = spec["weight"] * frame[f"z_{source}"]
        frame["index"] += frame[f"c_{source}"]
    frame["reference"] = (frame["portal"] / config.PORTAL_DUPLICATION + frame["ncs"] / config.NCS_COVERAGE) / 2
    frame["openings"] = frame.groupby(keys, group_keys=False)[["index", "reference"]].apply(calibrate)
    return frame


def calibrate(group):
    index_spread = group["index"].std(ddof=0)
    scale = group["reference"].std(ddof=0) / index_spread if index_spread else 0
    return (group["reference"].mean() + scale * (group["index"] - group["index"].mean())).clip(lower=0)


def build_signals(raw):
    portal, mapping = aggregate_portal(raw["portal_raw"])
    signals = raw["signals"].merge(portal, on=["month", "state", "district", "trade"], how="left")
    signals["portal"] = signals["portal"].fillna(0)
    return demand_index(signals), mapping
