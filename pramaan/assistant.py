import os
import re
import sys
from pathlib import Path

from pramaan import settings as s

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
LANGUAGE_NAMES = {"en": "English", "ta": "Tamil", "hi": "Hindi"}

DISTRICT_WORDS = {
    "chennai": "Chennai", "madras": "Chennai", "krishnagiri": "Krishnagiri", "hosur": "Krishnagiri", "salem": "Salem",
    "coimbatore": "Coimbatore", "kovai": "Coimbatore", "tiruppur": "Tiruppur", "tirupur": "Tiruppur",
    "tiruchirappalli": "Tiruchirappalli", "trichy": "Tiruchirappalli", "tiruchi": "Tiruchirappalli",
    "madurai": "Madurai", "tirunelveli": "Tirunelveli", "nellai": "Tirunelveli",
    "சென்னை": "Chennai", "கிருஷ்ணகிரி": "Krishnagiri", "ஓசூர்": "Krishnagiri", "சேலம்": "Salem", "கோயம்புத்தூர்": "Coimbatore", "கோவை": "Coimbatore",
    "திருப்பூர்": "Tiruppur", "திருச்சி": "Tiruchirappalli", "மதுரை": "Madurai", "திருநெல்வேலி": "Tirunelveli", "நெல்லை": "Tirunelveli",
    "चेन्नई": "Chennai", "कोयंबटूर": "Coimbatore", "मदुरै": "Madurai", "सेलम": "Salem",
}

TRADE_WORDS = [
    (r"\bev\b|electric vehicle|e-rickshaw", "EV Service Technician"),
    (r"solar|suryamitra", "Solar PV Installer"),
    (r"assistant electrician|electrician helper", "Assistant Electrician"),
    (r"electrician|wireman", "Electrician (Domestic)"),
    (r"lineman|line man", "Lineman (LT)"),
    (r"panel", "Electrical Panel Assembler"),
    (r"two.?wheeler|bike|motorcycle|scooter", "Two-Wheeler Service Technician"),
    (r"four.?wheeler|\bcar\b", "Four-Wheeler Service Technician"),
    (r"body|denting|denter", "Auto Body Repair Technician"),
    (r"paint", "Automotive Painter"),
]


def load_env():
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if value.strip() and not os.getenv(key.strip()):
            os.environ[key.strip()] = value.strip().strip('"').strip("'")


def llm_key():
    load_env()
    return os.getenv("NVIDIA_API_KEY") or os.getenv("PRAMAAN_LLM_KEY") or ""


def connected():
    return bool(llm_key())


def model_name():
    return os.getenv("PRAMAAN_LLM_MODEL", DEFAULT_MODEL)


def entities(question):
    text = question.lower()
    districts = []
    for word, district in DISTRICT_WORDS.items():
        if word in text and district not in districts:
            districts.append(district)
    trades = []
    for pattern, trade in TRADE_WORDS:
        if re.search(pattern, text) and trade not in trades:
            if trade == "Electrician (Domestic)" and "Assistant Electrician" in trades:
                continue
            trades.append(trade)
    sectors = [sector for sector, words in {"Electrical and Power": ["electrical", "power"], "Automotive": ["automotive", "auto ", "vehicle"]}.items() if any(w in text for w in words)]
    return {"districts": districts, "trades": trades, "sectors": sectors}


DATA_WORDS = ["short", "surplus", "oversuppl", "demand", "supply", "seat", "gap", "trainee", "job", "warning", "critical", "sector", "trade", "emerging", "grow", "need",
              "பற்றாக்குறை", "தேவை", "இடங்", "துறை", "தொழில்", "कमी", "मांग", "सीट", "सेक्टर", "ट्रेड"]
EXPLAIN_STARTS = ("how does", "how do", "how is", "what is", "what are you", "what can you", "explain", "why", "who ")
GREETINGS = {"hi", "hello", "hey", "namaste", "vanakkam", "வணக்கம்", "नमस्ते"}


def wants_evidence(question):
    found = entities(question)
    if found["districts"] or found["trades"] or found["sectors"]:
        return True
    text = question.lower().strip()
    first_word = re.split(r"[\s,!.?]+", text)[0] if text else ""
    if first_word in GREETINGS or text.startswith(EXPLAIN_STARTS):
        return False
    return any(word in text for word in DATA_WORDS)


def sector_table(gaps, district=None):
    frame = gaps if district is None else gaps[gaps["district"] == district]
    table = frame.groupby("sector", as_index=False)[["demand", "supply"]].sum()
    table["gap"] = table["demand"] - table["supply"]
    table["ratio"] = table["supply"] / table["demand"]
    return table.sort_values("gap", ascending=False)


def number(value):
    return f"{value:,.0f}"


def balance(demand, supply):
    shortfall = demand - supply
    if shortfall >= 0:
        return f"short by {number(shortfall)}"
    return f"surplus of {number(-shortfall)}"


def status_of(ratio):
    for status, low, high in s.BANDS:
        if (low is None or ratio >= low) and (high is None or ratio < high):
            return status
    return "Balanced"


def describe(row):
    return (f"{row.trade}: {number(row.demand)} jobs, {number(row.supply)} trainees, {balance(row.demand, row.supply)}, "
            f"ratio {row.ratio:.2f}, {row.status}, demand {row.growth:+.0%} vs last year, {number(row.seats)} seats")


def about(data):
    backtest = data["backtest"]
    weights = ", ".join(f"{name} {weight:.0%}" for name, weight in [("job portal postings", s.WEIGHTS["portal"]), ("NCS vacancies", s.WEIGHTS["ncs"]), ("industry hiring outlook", s.WEIGHTS["industry"]), ("e-Shram registrations", s.WEIGHTS["eshram"])])
    return "\n".join([
        "ABOUT PRAMAAN",
        f"- Pramaan is a skill demand intelligence platform for {s.STATE}. It covers {len(s.DISTRICTS)} districts ({', '.join(s.DISTRICTS)}), {len(s.TRADES)} trades in 2 sectors (Electrical and Power; Automotive). Data runs through {data['updated']}.",
        "- Pages: Dashboard (district map, opportunity grid, top shortages and surpluses), Explore a trade (forecast chart and live seat simulator), Plan seats (seat reallocation, emerging trades, early warnings), Ask Pramaan (this assistant), How it works.",
        f"- How demand is forecast: (1) collect four monthly signals: {weights}. (2) Clean: messy job titles are matched to official NCO codes. (3) Combine: each signal is scaled to a z-score and blended with those weights into one demand index, then converted to expected job openings using NCS and portal counts. "
        f"(4) Forecast: a Holt-Winters seasonal model projects openings for the next 12 months with an {int(s.BAND_LEVEL * 100)}% likely range. (5) Compare: openings are compared with certified trainees and gaps are ranked.",
        f"- Accuracy: on the last {s.BACKTEST_MONTHS} months held out, the median forecast error is {backtest['mape'].median():.1f}%, against {backtest['naive_mape'].median():.1f}% for a simple average.",
        "- Supply (trainees per year) = sanctioned seats x completion rate x certification rate.",
        "- Supply ratio = trainees / jobs. Below 0.6 Shortage (add seats or centres); 0.6 to 0.8 Watch (falling) (prepare to add capacity); 0.8 to 1.2 Balanced (keep as is); 1.2 to 1.5 Watch (rising) (hold seats); above 1.5 Oversupply (cut seats or retrain).",
        "- Early warning: a trade is flagged if its ratio is projected to cross into Shortage or Oversupply within the next 6 months.",
        "- Seat reallocation moves seats from oversupplied trades to short trades within the same sector, keeping total seats the same.",
        "- Designed for these feeds: online job portals, National Career Service (NCS), Sector Skill Councils, e-Shram, PLFS, NCVT MIS and Skill India Digital Hub.",
    ])


def facts(data, moves):
    gaps = data["gaps"]
    lines = ["STATE TOTALS"]
    lines.append(f"- All trades: {number(gaps['demand'].sum())} jobs expected in the next 12 months, {number(gaps['supply'].sum())} trainees per year, {balance(gaps['demand'].sum(), gaps['supply'].sum())}.")
    for row in sector_table(gaps).itertuples():
        lines.append(f"- {row.sector}: {number(row.demand)} jobs, {number(row.supply)} trainees, {balance(row.demand, row.supply)}, ratio {row.ratio:.2f}, {status_of(row.ratio)}.")
    shortfall = gaps.assign(short=gaps["demand"] - gaps["supply"])
    lines += ["", "BIGGEST SHORTAGES IN THE STATE (most unfilled jobs first)"]
    for row in shortfall.sort_values("short", ascending=False).head(8).itertuples():
        lines.append(f"- {row.district}, {describe(row)}")
    lines += ["", "BIGGEST SURPLUSES IN THE STATE (most extra trainees first)"]
    for row in shortfall.sort_values("short").head(8).itertuples():
        lines.append(f"- {row.district}, {describe(row)}")
    trades = gaps.groupby(["trade", "sector"], as_index=False)[["demand", "supply", "last_12m"]].sum()
    trades["growth"] = trades["demand"] / trades["last_12m"] - 1
    lines += ["", "TRADES ACROSS THE STATE (fastest growing first)"]
    for row in trades.sort_values("growth", ascending=False).itertuples():
        ratio = row.supply / row.demand
        lines.append(f"- {row.trade} ({row.sector}): {number(row.demand)} jobs, {number(row.supply)} trainees, {balance(row.demand, row.supply)}, ratio {ratio:.2f}, {status_of(ratio)}, demand {row.growth:+.0%} vs last year")
    for district in s.DISTRICTS:
        frame = shortfall[shortfall["district"] == district].sort_values("short", ascending=False)
        lines += ["", f"DISTRICT: {district}"]
        lines.append(f"- Total: {number(frame['demand'].sum())} jobs, {number(frame['supply'].sum())} trainees, {balance(frame['demand'].sum(), frame['supply'].sum())}.")
        for row in sector_table(gaps, district).itertuples():
            lines.append(f"- Sector {row.sector}: {number(row.demand)} jobs, {number(row.supply)} trainees, {balance(row.demand, row.supply)}, ratio {row.ratio:.2f}, {status_of(row.ratio)}.")
        lines.append("- Trades, most short first:")
        for row in frame.itertuples():
            lines.append(f"  - {describe(row)}")
    lines += ["", "EARLY WARNINGS (next 6 months)"]
    for row in data["warnings"].itertuples():
        lines.append(f"- {row.trade} in {row.district}: {row.current_status} now, becomes {row.projected_status} in {row.month.strftime('%B %Y')}.")
    lines += ["", "SUGGESTED SEAT MOVES (total seats unchanged)"]
    for row in moves.itertuples():
        lines.append(f"- Move {row.seats} seats from {row.from_trade} in {row.from_district} to {row.to_trade} in {row.to_district}.")
    return "\n".join(lines)


def context(data, moves):
    return about(data) + "\n\n" + facts(data, moves)


def system_prompt(data, moves, language):
    return (
        "You are Pramaan Assistant, a friendly expert inside Pramaan, a skill demand intelligence platform. You help Tamil Nadu skill planners "
        "decide how many training seats each trade should get in each district.\n\n"
        "How to answer:\n"
        "- Answer exactly the question asked, like a knowledgeable colleague. Do not add facts the question did not ask for.\n"
        "- Match the length to the question. A greeting or 'what can you do' gets 2 to 3 friendly sentences and 3 example questions, with no statistics. "
        "A simple fact gets 1 to 3 sentences. A district or trade question gets a short answer plus the few numbers that matter. "
        "A comparison gets a small markdown table. A 'how does it work' question is explained in plain words from ABOUT PRAMAAN.\n"
        "- Only give a recommendation when the user asks what to do, or when one specific action clearly follows from the answer. Never repeat the same recommendation in every answer.\n"
        "- Do not repeat state totals, rankings or warnings unless they answer the question.\n"
        "- For follow-up questions, use the conversation so far and do not repeat what you already said.\n"
        "- Use only the facts below. Copy numbers exactly as written; do not recompute them. Use the status names exactly as given. "
        "If the facts do not cover something, say so in one sentence and suggest what Pramaan can answer instead.\n"
        "- 'Short by N' means N more jobs than trainees. 'Surplus of N' means N more trainees than jobs.\n"
        f"- Write in {LANGUAGE_NAMES.get(language, 'English')}. Use plain language that a district officer understands. Bold the key number or trade in each answer.\n\n"
        + context(data, moves)
    )


def stream_answer(question, history, data, moves, language):
    from openai import OpenAI

    client = OpenAI(base_url=os.getenv("PRAMAAN_LLM_BASE_URL", DEFAULT_BASE_URL), api_key=llm_key(), timeout=75, max_retries=0)
    messages = [{"role": "system", "content": system_prompt(data, moves, language)}]
    for turn in history[-6:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": question})
    response = client.chat.completions.create(model=model_name(), messages=messages, temperature=0.3, top_p=0.9, max_tokens=8000, stream=True)
    thinking = 0
    finish = None
    for chunk in response:
        if not getattr(chunk, "choices", None):
            continue
        choice = chunk.choices[0]
        finish = choice.finish_reason or finish
        delta = choice.delta
        if delta is None:
            continue
        if getattr(delta, "reasoning_content", None):
            thinking += 1
        if getattr(delta, "content", None):
            yield delta.content
    print(f"[pramaan] llm done: model={model_name()} thinking_chunks={thinking} finish={finish}", file=sys.stderr, flush=True)


def fallback_answer(question, data, t):
    gaps = data["gaps"]
    found = entities(question)
    if found["districts"]:
        district = found["districts"][0]
        sectors = sector_table(gaps, district)
        top = sectors.iloc[0]
        frame = gaps[gaps["district"] == district].assign(need=lambda f: f["demand"] - f["supply"]).sort_values("need", ascending=False)
        lines = [t("fb_district", district=district, sector=t(f"sector_{top.sector}"), demand=number(top.demand), supply=number(top.supply))]
        for row in frame.head(3).itertuples():
            lines.append(t("fb_trade_line", trade=row.trade, demand=number(row.demand), supply=number(row.supply), status=t(f"status_{row.status}")))
        return "\n".join(lines)
    if found["trades"]:
        trade = found["trades"][0]
        frame = gaps[gaps["trade"] == trade].assign(need=lambda f: f["demand"] - f["supply"]).sort_values("need", ascending=False)
        lines = [t("fb_trade", trade=trade, district=frame.iloc[0]["district"])]
        for row in frame.head(3).itertuples():
            lines.append(t("fb_district_line", district=row.district, demand=number(row.demand), supply=number(row.supply), status=t(f"status_{row.status}")))
        return "\n".join(lines)
    sectors = sector_table(gaps)
    top = sectors.iloc[0]
    frame = gaps.assign(need=lambda f: f["demand"] - f["supply"]).sort_values("need", ascending=False)
    lines = [t("fb_state", sector=t(f"sector_{top.sector}"), demand=number(top.demand), supply=number(top.supply))]
    for row in frame.head(3).itertuples():
        lines.append(t("fb_pair_line", trade=row.trade, district=row.district, demand=number(row.demand), supply=number(row.supply)))
    return "\n".join(lines)


def evidence(question, gaps):
    found = entities(question)
    if found["districts"]:
        district = found["districts"][0]
        return "district", district, gaps[gaps["district"] == district]
    if found["trades"]:
        trade = found["trades"][0]
        frame = gaps[gaps["trade"] == trade].copy()
        frame["short"] = frame["district"]
        return "trade", trade, frame
    return "state", s.STATE, gaps


def sector_frame(gaps):
    return gaps.groupby("sector", as_index=False)[["demand", "supply"]].sum()

