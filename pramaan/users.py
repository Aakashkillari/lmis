import hashlib
import hmac
import os
import secrets

DEMO_PASSWORD = os.getenv("PRAMAAN_DEMO_PASSWORD", "pramaan-demo-2026")
ITERATIONS = 120_000

ACCOUNTS = [
    {
        "id": "msde.planner",
        "name": "National skill planner",
        "title": "Ministry of Skill Development, all states",
        "role": "national",
        "initials": "NP",
        "scope": {"state": None, "district": None, "sector": None},
        "summary": "Sets training targets for every pilot state and compares them.",
    },
    {
        "id": "state.planner",
        "name": "State planning cell",
        "title": "Tamil Nadu skill planning",
        "role": "state",
        "initials": "SP",
        "scope": {"state": "Tamil Nadu", "district": None, "sector": None},
        "summary": "Plans training seats for every district and trade in the state.",
    },
    {
        "id": "cbe.officer",
        "name": "District skill officer",
        "title": "Coimbatore district",
        "role": "district",
        "initials": "DO",
        "scope": {"state": "Tamil Nadu", "district": "Coimbatore", "sector": None},
        "summary": "Runs training in one district and asks for seat changes.",
    },
    {
        "id": "vehicles.council",
        "name": "Vehicles sector council",
        "title": "Two-wheelers, cars and EVs",
        "role": "sector",
        "initials": "VC",
        "scope": {"state": None, "district": None, "sector": "auto"},
        "summary": "Advises on vehicle trades in every pilot state.",
    },
]


def _hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)


_SALTS = {a["id"]: secrets.token_bytes(16) for a in ACCOUNTS}
_HASHES = {a["id"]: _hash(DEMO_PASSWORD, _SALTS[a["id"]]) for a in ACCOUNTS}
_BY_ID = {a["id"]: a for a in ACCOUNTS}


def public(account):
    return {k: account[k] for k in ("id", "name", "title", "role", "initials", "scope", "summary")}


def find(user_id):
    account = _BY_ID.get((user_id or "").strip().lower())
    return public(account) if account else None


def verify(user_id, password):
    user_id = (user_id or "").strip().lower()
    if user_id not in _HASHES:
        _hash(password or "", secrets.token_bytes(16))
        return None
    if hmac.compare_digest(_hash(password or "", _SALTS[user_id]), _HASHES[user_id]):
        return public(_BY_ID[user_id])
    return None
