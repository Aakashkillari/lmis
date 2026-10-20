from functools import lru_cache
from typing import Optional

from fastapi import FastAPI

from pramaan import model

app = FastAPI(title="Pramaan API", description="Skill demand and supply outlook for Tamil Nadu, by district and trade.", version="1.0")


@lru_cache(maxsize=1)
def results():
    return model.build()


def keep(frame, column, value):
    return frame if not value else frame[frame[column].str.lower() == value.strip().lower()]


@app.get("/api/gaps")
def gaps(district: Optional[str] = None, trade: Optional[str] = None, sector: Optional[str] = None, status: Optional[str] = None):
    frame = results()["gaps"]
    for column, value in [("district", district), ("trade", trade), ("sector", sector), ("status", status)]:
        frame = keep(frame, column, value)
    columns = ["district", "trade", "sector", "nco", "qp", "nsqf", "seats", "supply", "demand", "demand_low", "demand_high", "gap", "ratio", "status", "growth"]
    out = frame[columns].copy()
    for column in ["supply", "demand", "demand_low", "demand_high", "gap"]:
        out[column] = out[column].round(0).astype(int)
    out[["ratio", "growth"]] = out[["ratio", "growth"]].round(3)
    return {"state": "Tamil Nadu", "data_through": results()["updated"], "count": len(out), "results": out.to_dict(orient="records")}


@app.get("/api/warnings")
def warnings():
    frame = results()["warnings"].copy()
    frame["month"] = frame["month"].astype(str)
    frame[["ratio", "people"]] = frame[["ratio", "people"]].round(2)
    return {"count": len(frame), "results": frame.to_dict(orient="records")}


@app.get("/api/health")
def health():
    return {"status": "ok", "data_through": results()["updated"]}
