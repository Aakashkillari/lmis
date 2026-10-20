import numpy as np
import pandas as pd

from lmis import config
from lmis.data import trade_table

KEYS = ["state", "district", "trade"]
ALERT_STATUSES = ["Oversupply", "Shortage"]


def status_for(ratio):
    for band in config.STATUS_BANDS:
        above_min = band["min"] is None or ratio >= band["min"]
        below_max = band["max"] is None or ratio < band["max"]
        if above_min and below_max:
            return band["status"]
    return "Balanced"


def supply_table(capacity):
    frame = capacity.copy()
    frame["supply"] = frame["sanctioned_seats"] * frame["completion_rate"] * frame["certification_rate"]
    return frame


def gap_table(capacity, index_frame, forecasts):
    supply = supply_table(capacity)
    demand = forecasts.groupby(KEYS, as_index=False).agg(
        forecast_demand=("forecast", "sum"),
        demand_lower=("lower", "sum"),
        demand_upper=("upper", "sum"),
    )
    last_months = index_frame[index_frame["month"] > index_frame["month"].max() - 12]
    current = last_months.groupby(KEYS, as_index=False)["openings"].sum().rename(columns={"openings": "last_12m_demand"})
    frame = supply.merge(demand, on=KEYS).merge(current, on=KEYS).merge(trade_table(), on="trade")
    frame["gap_ratio"] = frame["supply"] / frame["forecast_demand"]
    frame["gap_people"] = frame["supply"] - frame["forecast_demand"]
    frame["severity"] = frame["gap_people"].abs()
    frame["status"] = frame["gap_ratio"].apply(status_for)
    frame["current_ratio"] = frame["supply"] / frame["last_12m_demand"]
    frame["current_status"] = frame["current_ratio"].apply(status_for)
    frame["demand_growth"] = frame["forecast_demand"] / frame["last_12m_demand"] - 1
    return frame


def rolling_path(index_frame, forecasts, key):
    state, district, trade = key
    past = index_frame[(index_frame["state"] == state) & (index_frame["district"] == district) & (index_frame["trade"] == trade)]
    future = forecasts[(forecasts["state"] == state) & (forecasts["district"] == district) & (forecasts["trade"] == trade)]
    values = np.concatenate([past.sort_values("month")["openings"].to_numpy()[-12:], future.sort_values("month")["forecast"].to_numpy()])
    months = list(future.sort_values("month")["month"])
    trailing = [values[step + 1:step + 13].sum() for step in range(len(months))]
    return months, trailing


def early_warnings(gaps, index_frame, forecasts):
    rows = []
    past_by_key = {key: group.sort_values("month")["openings"].to_numpy()[-12:] for key, group in index_frame.groupby(KEYS)}
    future_by_key = {key: group.sort_values("month") for key, group in forecasts.groupby(KEYS)}
    for row in gaps.itertuples():
        key = (row.state, row.district, row.trade)
        future = future_by_key[key]
        values = np.concatenate([past_by_key[key], future["forecast"].to_numpy()])
        months = list(future["month"])
        for step in range(config.WARNING_HORIZON):
            demand = values[step + 1:step + 13].sum()
            ratio = row.supply / demand
            status = status_for(ratio)
            if status in ALERT_STATUSES and status != row.current_status:
                rows.append({
                    "state": row.state,
                    "district": row.district,
                    "trade": row.trade,
                    "sector": row.sector,
                    "current_status": row.current_status,
                    "current_ratio": row.current_ratio,
                    "projected_status": status,
                    "direction": "Towards oversupply" if status == "Oversupply" else "Towards shortage",
                    "crossing_month": months[step],
                    "months_ahead": step + 1,
                    "ratio_at_crossing": ratio,
                    "severity": abs(row.supply - demand),
                })
                break
    columns = ["state", "district", "trade", "sector", "current_status", "current_ratio", "projected_status", "direction", "crossing_month", "months_ahead", "ratio_at_crossing", "severity"]
    frame = pd.DataFrame(rows, columns=columns)
    return frame.sort_values(["months_ahead", "severity"], ascending=[True, False]).reset_index(drop=True)


def ranked(gaps, status=None, top=None):
    frame = gaps if status is None else gaps[gaps["status"] == status]
    frame = frame.sort_values("severity", ascending=False).reset_index(drop=True)
    frame.insert(0, "rank", range(1, len(frame) + 1))
    return frame.head(top) if top else frame


def rollup(gaps, level):
    frame = gaps.groupby(level, as_index=False).agg(
        supply=("supply", "sum"),
        forecast_demand=("forecast_demand", "sum"),
        last_12m_demand=("last_12m_demand", "sum"),
        sanctioned_seats=("sanctioned_seats", "sum"),
        oversupply_pairs=("status", lambda s: int((s == "Oversupply").sum())),
        shortage_pairs=("status", lambda s: int((s == "Shortage").sum())),
        mismatch_people=("severity", "sum"),
    )
    frame["gap_ratio"] = frame["supply"] / frame["forecast_demand"]
    frame["status"] = frame["gap_ratio"].apply(status_for)
    return frame


def with_seats(row, seats):
    supply = seats * row["completion_rate"] * row["certification_rate"]
    ratio = supply / row["forecast_demand"]
    return supply, ratio, status_for(ratio)
