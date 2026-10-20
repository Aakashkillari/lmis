from functools import lru_cache
from typing import Optional

from fastapi import FastAPI

from lmis import config, pipeline

GAP_FIELDS = [
    "state", "district", "sector", "trade", "nco", "qp", "nsqf",
    "sanctioned_seats", "iti_seats", "pmkvy_seats", "completion_rate", "certification_rate",
    "supply", "last_12m_demand", "forecast_demand", "demand_lower", "demand_upper",
    "gap_ratio", "gap_people", "severity", "status", "current_status", "demand_growth",
]

app = FastAPI(
    title="LMIS Forecast API",
    description="Demand-supply gap forecasts by state, district and trade. " + config.SOURCE_NOTE,
    version="1.0",
)


@lru_cache(maxsize=1)
def results():
    return pipeline.load()


def gap_records(frame):
    out = frame[GAP_FIELDS].copy()
    for column in ["supply", "last_12m_demand", "forecast_demand", "demand_lower", "demand_upper", "gap_people", "severity"]:
        out[column] = out[column].round(0).astype(int)
    for column in ["gap_ratio", "demand_growth"]:
        out[column] = out[column].round(3)
    return out.sort_values("severity", ascending=False).reset_index(drop=True)


def warning_records(frame):
    out = frame.copy()
    out["crossing_month"] = out["crossing_month"].astype(str)
    out["current_ratio"] = out["current_ratio"].round(3)
    out["ratio_at_crossing"] = out["ratio_at_crossing"].round(3)
    out["severity"] = out["severity"].round(0).astype(int)
    return out


def filtered(frame, state, district, trade, sector=None):
    if state:
        frame = frame[frame["state"].str.lower() == state.lower()]
    if district:
        frame = frame[frame["district"].str.lower() == district.lower()]
    if trade:
        frame = frame[frame["trade"].str.lower() == trade.lower()]
    if sector:
        frame = frame[frame["sector"].str.lower() == sector.lower()]
    return frame


def envelope(records):
    data = results()
    return {
        "source_note": config.SOURCE_NOTE,
        "last_refreshed": data["refreshed"],
        "forecast_horizon_months": config.FORECAST_MONTHS,
        "count": len(records),
        "results": records,
    }


@app.get("/api/gaps")
def gaps(state: Optional[str] = None, district: Optional[str] = None, trade: Optional[str] = None, sector: Optional[str] = None, status: Optional[str] = None):
    frame = filtered(results()["gaps"], state, district, trade, sector)
    if status:
        frame = frame[frame["status"].str.lower() == status.lower()]
    return envelope(gap_records(frame).to_dict(orient="records"))


@app.get("/api/warnings")
def warnings(state: Optional[str] = None, district: Optional[str] = None, trade: Optional[str] = None):
    frame = filtered(results()["warnings"], state, district, trade)
    return envelope(warning_records(frame).to_dict(orient="records"))


@app.get("/api/meta")
def meta():
    return {
        "states": config.STATES,
        "trades": config.TRADES,
        "weights": {key: spec["weight"] for key, spec in config.SOURCES.items()},
        "status_bands": config.STATUS_BANDS,
        "source_note": config.SOURCE_NOTE,
        "last_refreshed": results()["refreshed"],
    }
