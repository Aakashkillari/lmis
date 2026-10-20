import json
import os
import secrets
import time
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pramaan import assistant, model, settings as s, users
from pramaan.text import translate

COOKIE = "pramaan_session"
SESSION_SECONDS = 8 * 60 * 60
SESSIONS: dict[str, tuple[str, float]] = {}
FAILURES: dict[str, list[float]] = {}
MAX_FAILURES, FAILURE_WINDOW = 5, 300
DEMO_LOGINS = os.getenv("PRAMAAN_DEMO_LOGINS", "on").lower() != "off"

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "frontend" / "dist"
STATUS_INDEX = {"Shortage": 0, "Watch (falling)": 1, "Balanced": 2, "Watch (rising)": 3, "Oversupply": 4}
NOTES = {
    "Chennai": "Auto and electronics corridor", "Krishnagiri": "Hosur EV hub", "Salem": "Steel and two-wheeler market",
    "Coimbatore": "Engineering and pumps hub", "Tiruppur": "Knitwear cluster", "Tiruchirappalli": "Heavy engineering cluster",
    "Madurai": "Southern trade centre", "Tirunelveli": "Wind and solar belt",
    "Bengaluru Urban": "Tech and EV start-up hub", "Mysuru": "Two-wheeler and auto parts plants", "Belagavi": "Foundry and auto parts cluster",
    "Dharwad": "Hubballi-Dharwad bus and machine tools belt", "Dakshina Kannada": "Mangaluru port and services", "Kalaburagi": "Solar parks and cement belt",
    "Tumakuru": "Pavagada solar park and industrial corridor", "Ballari": "Steel plants and solar belt",
}
BOM = "\ufeff"  # lets Excel open Tamil, Hindi and Kannada text correctly
SECTOR_KEY = {"Electrical and Power": "power", "Automotive": "auto"}
STATUS_WORDS = {"Shortage": "Not enough trainees", "Watch (falling)": "Running short", "Balanced": "Well matched", "Watch (rising)": "A few too many", "Oversupply": "Too many trainees"}
PLAIN = {
    "Electrician (Domestic)": "Electrician", "Assistant Electrician": "Electrician helper", "Solar PV Installer": "Solar panel installer",
    "Lineman (LT)": "Power line worker", "Electrical Panel Assembler": "Panel assembler", "Two-Wheeler Service Technician": "Bike mechanic",
    "Four-Wheeler Service Technician": "Car mechanic", "EV Service Technician": "EV mechanic", "Auto Body Repair Technician": "Car body repairer",
    "Automotive Painter": "Car painter",
}
ICONS = {
    "Electrician (Domestic)": "bolt", "Assistant Electrician": "plug", "Solar PV Installer": "solar", "Lineman (LT)": "pole",
    "Electrical Panel Assembler": "panel", "Two-Wheeler Service Technician": "bike", "Four-Wheeler Service Technician": "car",
    "EV Service Technician": "ev", "Auto Body Repair Technician": "hammer", "Automotive Painter": "spray",
}

app = FastAPI(title="Pramaan API", version="2.0")


def session_user(request: Request):
    token = request.cookies.get(COOKIE)
    entry = SESSIONS.get(token or "")
    if not entry or entry[1] < time.time():
        SESSIONS.pop(token or "", None)
        return None
    user = users.find(entry[0])
    return {**user, "until": int(entry[1]), "since": int(entry[1] - SESSION_SECONDS)} if user else None


def require_user(request: Request):
    user = session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Sign in to use this")
    return user


def start_session(response: Response, user):
    token = secrets.token_urlsafe(32)
    until = time.time() + SESSION_SECONDS
    SESSIONS[token] = (user["id"], until)
    response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, httponly=True, samesite="lax", secure=os.getenv("PRAMAAN_SECURE_COOKIE") == "on", path="/")
    return {**user, "until": int(until), "since": int(until - SESSION_SECONDS)}


class Login(BaseModel):
    username: str
    password: str


class DemoLogin(BaseModel):
    username: str


@app.post("/api/login")
def api_login(body: Login, response: Response):
    key = body.username.strip().lower()
    now = time.time()
    recent = [t for t in FAILURES.get(key, []) if now - t < FAILURE_WINDOW]
    if len(recent) >= MAX_FAILURES:
        wait = int(FAILURE_WINDOW - (now - recent[0])) // 60 + 1
        raise HTTPException(status_code=429, detail=f"Too many wrong tries for this user ID. Wait {wait} minute{'s' if wait > 1 else ''} and try again.")
    user = users.verify(body.username, body.password)
    if not user:
        FAILURES[key] = recent + [now]
        raise HTTPException(status_code=401, detail="That user ID and password do not match. Check both and try again.")
    FAILURES.pop(key, None)
    return start_session(response, user)


@app.post("/api/login/demo")
def api_login_demo(body: DemoLogin, response: Response):
    user = users.find(body.username) if DEMO_LOGINS else None
    if not user:
        raise HTTPException(status_code=403, detail="Demo sign-in is turned off on this server.")
    return start_session(response, user)


@app.get("/api/accounts")
def api_accounts():
    return {"demo": DEMO_LOGINS, "accounts": [users.public(a) for a in users.ACCOUNTS] if DEMO_LOGINS else []}


@app.get("/api/me")
def api_me(request: Request):
    return {"user": session_user(request)}


@app.post("/api/logout")
def api_logout(request: Request, response: Response):
    SESSIONS.pop(request.cookies.get(COOKIE, ""), None)
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


def check_state(state):
    if state not in s.STATES:
        raise HTTPException(status_code=404, detail=f"Pramaan has no data for {state} yet. Pilot states: {', '.join(s.STATES)}.")
    return state


@lru_cache(maxsize=8)
def results(state=s.STATE):
    return model.build(state)


@lru_cache(maxsize=8)
def moves_for(state=s.STATE):
    gaps = results(state)["gaps"]
    return {"same": model.reallocate(gaps, same_sector=True), "any": model.reallocate(gaps, same_sector=False)}


def number(value):
    return round(float(value), 1)


def method():
    return {
        "weights": s.WEIGHTS, "duplication": s.PORTAL_DUPLICATION, "coverage": s.NCS_COVERAGE, "bandLevel": s.BAND_LEVEL,
        "historyMonths": s.HISTORY_MONTHS, "forecastMonths": s.FORECAST_MONTHS, "warningMonths": s.WARNING_MONTHS, "backtestMonths": s.BACKTEST_MONTHS,
        "bands": [[low, high] for _, low, high in s.BANDS], "donorKeep": s.REALLOCATION["donor_keep"], "receiverTarget": s.REALLOCATION["receiver_target"],
        "block": s.REALLOCATION["block"],
    }


@lru_cache(maxsize=8)
def payload(state=s.STATE):
    data = results(state)
    gaps, index, forecasts = data["gaps"], data["index"], data["forecasts"]
    districts = data["districts"]
    trades = [t["trade"] for t in s.TRADES]
    geo = json.loads((ROOT / "assets" / s.STATES[state]["geo"]).read_text(encoding="utf-8"))
    pairs = []
    for district in districts:
        row = []
        for trade in trades:
            g = gaps[(gaps["district"] == district) & (gaps["trade"] == trade)].iloc[0]
            history = model.series(index, district, trade).tail(24)
            future = model.series(forecasts, district, trade)
            row.append({
                "jobs": number(g["demand"]), "low": number(g["demand_low"]), "high": number(g["demand_high"]),
                "trainees": number(g["supply"]), "last": number(g["last_12m"]), "seats": int(g["seats"]),
                "completion": float(g["completion"]), "certification": float(g["certification"]),
                "ratio": round(float(g["ratio"]), 4), "status": STATUS_INDEX[g["status"]], "growth": round(float(g["growth"]), 4),
                "history": [number(v) for v in history["openings"]],
                "forecast": [number(v) for v in future["forecast"]], "forecastLow": [number(v) for v in future["lower"]], "forecastHigh": [number(v) for v in future["upper"]],
            })
        pairs.append(row)
    history_months = [str(m) for m in model.series(index, districts[0], trades[0]).tail(24)["month"]]
    future_months = [str(m) for m in model.series(forecasts, districts[0], trades[0])["month"]]
    warnings = [{
        "district": districts.index(w.district), "trade": trades.index(w.trade), "now": STATUS_INDEX[w.current_status],
        "next": STATUS_INDEX[w.projected_status], "month": str(w.month), "monthsAhead": int(w.months_ahead), "people": round(float(w.people)),
    } for w in data["warnings"].itertuples()]
    moves = {key: [{
        "from": [districts.index(m.from_district), trades.index(m.from_trade)], "to": [districts.index(m.to_district), trades.index(m.to_trade)],
        "seats": int(m.seats), "fromBefore": round(float(m.from_before), 3), "fromAfter": round(float(m.from_after), 3),
        "toBefore": round(float(m.to_before), 3), "toAfter": round(float(m.to_after), 3),
    } for m in frame.itertuples()] for key, frame in moves_for(state).items()}
    centres = {g["n"]: g for g in geo["d"]}
    backtest = data["backtest"]
    return {
        "state": state,
        "states": list(s.STATES),
        "method": method(),
        "updated": data["updated"],
        "historyMonths": history_months,
        "futureMonths": future_months,
        "districts": [{"name": d, "note": NOTES[d], "cx": centres[d]["cx"], "cy": centres[d]["cy"]} for d in districts],
        "trades": [{"name": PLAIN[t["trade"]], "official": t["trade"], "sector": "power" if t["sector"] == "Electrical and Power" else "auto", "icon": ICONS[t["trade"]], "nco": t["nco"], "nsqf": t["nsqf"]} for t in s.TRADES],
        "pairs": pairs,
        "warnings": warnings,
        "moves": moves,
        "accuracy": {"pramaan": round(float(backtest["mape"].median()), 1), "simple": round(float(backtest["naive_mape"].median()), 1)},
        "weights": s.WEIGHTS,
        "geo": geo,
    }


@app.get("/api/data")
def api_data(state: str = s.STATE):
    return JSONResponse(payload(check_state(state)))


def share(frame):
    jobs, trainees = float(frame["demand"].sum()), float(frame["supply"].sum())
    return {
        "jobs": number(jobs), "trainees": number(trainees),
        "unfilled": number((frame["demand"] - frame["supply"]).clip(lower=0).sum()),
        "extra": number((frame["supply"] - frame["demand"]).clip(lower=0).sum()),
    }


@lru_cache(maxsize=1)
def national():
    trades = [t["trade"] for t in s.TRADES]
    states, pairs = [], []
    for state in s.STATES:
        data = results(state)
        gaps = data["gaps"]
        districts = data["districts"]
        states.append({
            "name": state, "districts": len(districts), "updated": data["updated"], **share(gaps),
            "short": int((gaps["status"] == "Shortage").sum()), "many": int((gaps["status"] == "Oversupply").sum()), "warnings": len(data["warnings"]),
            "sectors": {SECTOR_KEY[sector]: share(group) for sector, group in gaps.groupby("sector")},
            "trades": [share(gaps[gaps["trade"] == trade]) for trade in trades],
            "accuracy": {"pramaan": round(float(data["backtest"]["mape"].median()), 1), "simple": round(float(data["backtest"]["naive_mape"].median()), 1)},
        })
        for row in gaps.itertuples():
            pairs.append({
                "state": state, "district": row.district, "trade": trades.index(row.trade), "jobs": number(row.demand),
                "trainees": number(row.supply), "ratio": round(float(row.ratio), 4), "status": STATUS_INDEX[row.status],
            })
    return {"states": states, "pairs": pairs, "trades": [{"name": PLAIN[t["trade"]], "sector": SECTOR_KEY[t["sector"]], "icon": ICONS[t["trade"]]} for t in s.TRADES], "method": method()}


@app.get("/api/national")
def api_national():
    return JSONResponse(national())


@app.get("/api/match")
def api_match(q: str = "", user=Depends(require_user)):
    return {"results": model.match_title(q)}


class Question(BaseModel):
    question: str
    history: list = []
    lang: str = "en"
    state: str = s.STATE


@app.post("/api/ask")
def api_ask(body: Question, user=Depends(require_user)):
    state = check_state(body.state)
    data = results(state)
    moves = moves_for(state)["same"]

    def t(key, **values):
        return translate(key, body.lang, **values)

    def stream():
        sent = False
        if assistant.connected():
            try:
                for piece in assistant.stream_answer(body.question, body.history[-6:], data, moves, body.lang, user):
                    sent = True
                    yield piece
            except Exception as error:
                print(f"[pramaan] llm error: {type(error).__name__}: {error}", flush=True)
        if not sent:
            yield assistant.fallback_answer(body.question, data, t)

    return StreamingResponse(stream(), media_type="text/plain; charset=utf-8", headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})


@app.get("/api/status")
def api_status():
    return {"ai": assistant.connected(), "model": assistant.model_name(), "updated": results()["updated"], "states": list(s.STATES)}


@app.get("/api/gaps")
def api_gaps(state: str = s.STATE, district: Optional[str] = None, trade: Optional[str] = None):
    frame = results(check_state(state))["gaps"]
    if district:
        frame = frame[frame["district"].str.lower() == district.lower()]
    if trade:
        frame = frame[frame["trade"].str.lower() == trade.lower()]
    columns = ["district", "trade", "sector", "nco", "nsqf", "seats", "supply", "demand", "ratio", "status"]
    return {"state": state, "count": len(frame), "results": frame[columns].round(3).to_dict(orient="records")}


def keep(frame, sector="all", district=None, trade=None, columns=("district", "trade")):
    """Filter any table by field, district and trade. Moves match on either end."""
    sector_name = {v: k for k, v in SECTOR_KEY.items()}.get(sector)
    mask = frame.index == frame.index
    if sector_name:
        trades = {t["trade"] for t in s.TRADES if t["sector"] == sector_name}
        mask &= frame[[c for c in columns if "trade" in c]].isin(trades).any(axis=1)
    if district:
        mask &= frame[[c for c in columns if "district" in c]].eq(district).any(axis=1)
    if trade:
        mask &= frame[[c for c in columns if "trade" in c]].isin([trade]).any(axis=1)
    return frame[mask]


def per_ten(value):
    return round(float(value) * 10, 1)


def export_table(kind, state, sector, district, trade, mode, budget):
    data = results(state)
    info = {t["trade"]: t for t in s.TRADES}
    if kind == "gaps":
        g = keep(data["gaps"], sector, district, trade)
        return pd.DataFrame({
            "State": state, "District": g["district"], "Trade": g["trade"].map(PLAIN), "Official trade name": g["trade"],
            "Field": g["sector"].map({"Electrical and Power": "Electrical & power", "Automotive": "Vehicles"}),
            "NCO code": g["trade"].map(lambda t: info[t]["nco"]), "Qualification pack": g["trade"].map(lambda t: info[t]["qp"]),
            "NSQF level": g["trade"].map(lambda t: info[t]["nsqf"]),
            "Jobs next 12 months": g["demand"].round(0), "Likely low": g["demand_low"].round(0), "Likely high": g["demand_high"].round(0),
            "Trainees ready per year": g["supply"].round(0), "Training seats": g["seats"], "Trainees per 10 jobs": g["ratio"].map(per_ten),
            "Status": g["status"].map(STATUS_WORDS), "Job growth vs last year (%)": (g["growth"] * 100).round(1),
        })
    if kind == "forecast":
        f = keep(data["forecasts"], sector, district, trade)
        return pd.DataFrame({
            "State": state, "District": f["district"], "Trade": f["trade"].map(PLAIN), "Month": f["month"].astype(str),
            "Expected jobs": f["forecast"].round(1), "Likely low": f["lower"].round(1), "Likely high": f["upper"].round(1),
        })
    if kind == "warnings":
        w = keep(data["warnings"], sector, district, trade)
        return pd.DataFrame({
            "State": state, "District": w["district"], "Trade": w["trade"].map(PLAIN), "Status now": w["current_status"].map(STATUS_WORDS),
            "Status coming": w["projected_status"].map(STATUS_WORDS), "Month": w["month"].astype(str), "Months ahead": w["months_ahead"],
            "People affected": w["people"].round(0),
        })
    if kind == "moves":
        m = keep(moves_for(state)["any" if mode == "any" else "same"], sector, district, trade, ("from_district", "to_district", "from_trade", "to_trade")).copy()
        if budget is not None:
            left, seats = budget, []
            for value in m["seats"]:
                take = min(int(value), left // 10 * 10)
                seats.append(take)
                left -= take
            m["seats"] = seats
            m = m[m["seats"] > 0]
        return pd.DataFrame({
            "State": state, "Take seats from (district)": m["from_district"], "Take seats from (trade)": m["from_trade"].map(PLAIN),
            "Give seats to (district)": m["to_district"], "Give seats to (trade)": m["to_trade"].map(PLAIN), "Seats to move": m["seats"],
            "From: trainees per 10 jobs today": m["from_before"].map(per_ten), "To: trainees per 10 jobs today": m["to_before"].map(per_ten),
        })
    raise HTTPException(status_code=404, detail="Choose one of: gaps, forecast, warnings, moves.")


@app.get("/api/export/{kind}.csv")
def api_export(kind: str, state: str = s.STATE, sector: str = "all", district: Optional[str] = None, trade: Optional[str] = None,
               mode: str = "same", budget: Optional[int] = None, user=Depends(require_user)):
    """Download any Pramaan table as a spreadsheet. Use state=all for every pilot state."""
    states = list(s.STATES) if state == "all" else [check_state(state)]
    frame = pd.concat([export_table(kind, st, sector, district, trade, mode, budget) for st in states], ignore_index=True)
    name = "-".join(part.lower().replace(" ", "-") for part in [kind, state, district or "", trade and PLAIN.get(trade, trade) or ""] if part)
    return Response(content=BOM + frame.to_csv(index=False), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="pramaan-{name}.csv"'})


if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        target = DIST / path
        return FileResponse(target if path and target.is_file() else DIST / "index.html")
