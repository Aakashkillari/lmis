import math

import pandas as pd

from lmis import config
from lmis.gaps import status_for

SEAT_BLOCK = 20


def yield_per_seat(row):
    return row["completion_rate"] * row["certification_rate"]


def spare_seats(row, keep_ratio):
    needed = math.ceil(row["forecast_demand"] * keep_ratio / yield_per_seat(row))
    return max(0, (row["seats"] - needed) // SEAT_BLOCK * SEAT_BLOCK)


def missing_seats(row, target_ratio):
    needed = math.ceil(row["forecast_demand"] * target_ratio / yield_per_seat(row))
    return max(0, math.ceil((needed - row["seats"]) / SEAT_BLOCK) * SEAT_BLOCK)


def ratio_for(row):
    return row["seats"] * yield_per_seat(row) / row["forecast_demand"]


def reallocate(gaps, same_sector=True, keep_ratio=config.TARGET_RATIO * 1.1, target_ratio=config.TARGET_RATIO):
    moves = []
    for state, block in gaps.groupby("state"):
        pairs = block.copy()
        pairs["seats"] = pairs["sanctioned_seats"]
        groups = [pairs] if not same_sector else [g for _, g in pairs.groupby("sector")]
        for group in groups:
            moves.extend(match_within(group, keep_ratio, target_ratio))
    columns = ["state", "sector", "from_district", "from_trade", "to_district", "to_trade", "seats_moved",
               "from_ratio_before", "from_ratio_after", "from_status_after",
               "to_ratio_before", "to_ratio_after", "to_status_after"]
    return pd.DataFrame(moves, columns=columns)


def match_within(group, keep_ratio, target_ratio):
    rows = {i: row.to_dict() for i, row in group.iterrows()}
    donors = sorted([i for i in rows if rows[i]["status"] == "Oversupply"], key=lambda i: -rows[i]["severity"])
    receivers = sorted([i for i in rows if rows[i]["status"] == "Shortage"], key=lambda i: -rows[i]["severity"])
    moves = []
    for receiver in receivers:
        for donor in donors:
            need = missing_seats(rows[receiver], target_ratio)
            spare = spare_seats(rows[donor], keep_ratio)
            moved = min(need, spare)
            if moved <= 0:
                continue
            from_before = ratio_for(rows[donor])
            to_before = ratio_for(rows[receiver])
            rows[donor]["seats"] -= moved
            rows[receiver]["seats"] += moved
            moves.append({
                "state": rows[donor]["state"],
                "sector": rows[donor]["sector"],
                "from_district": rows[donor]["district"],
                "from_trade": rows[donor]["trade"],
                "to_district": rows[receiver]["district"],
                "to_trade": rows[receiver]["trade"],
                "seats_moved": moved,
                "from_ratio_before": from_before,
                "from_ratio_after": ratio_for(rows[donor]),
                "from_status_after": status_for(ratio_for(rows[donor])),
                "to_ratio_before": to_before,
                "to_ratio_after": ratio_for(rows[receiver]),
                "to_status_after": status_for(ratio_for(rows[receiver])),
            })
    return moves


def apply_moves(gaps, moves):
    frame = gaps.copy()
    keys = ["state", "district", "trade"]
    change = {}
    for move in moves.itertuples():
        out_key = (move.state, move.from_district, move.from_trade)
        in_key = (move.state, move.to_district, move.to_trade)
        change[out_key] = change.get(out_key, 0) - move.seats_moved
        change[in_key] = change.get(in_key, 0) + move.seats_moved
    frame["sanctioned_seats"] = [
        seats + change.get(key, 0)
        for seats, key in zip(frame["sanctioned_seats"], frame[keys].itertuples(index=False, name=None))
    ]
    frame["supply"] = frame["sanctioned_seats"] * frame["completion_rate"] * frame["certification_rate"]
    frame["gap_ratio"] = frame["supply"] / frame["forecast_demand"]
    frame["gap_people"] = frame["supply"] - frame["forecast_demand"]
    frame["severity"] = frame["gap_people"].abs()
    frame["status"] = frame["gap_ratio"].apply(status_for)
    return frame
