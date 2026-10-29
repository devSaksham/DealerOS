"""Files on disk are the database: one CSV of monthly HiRise history, one CSV of daily entries,
users.json and settings.json. Lives in DATA_DIR (default ./data, git-ignored).
ponytail: CSV + whole-file rewrites, fine for one dealership; move to Postgres when several branches write at once."""
import hashlib
import hmac
import json
import os
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("DEALEROS_DATA", ROOT / "data"))
DEMO_DIR = ROOT / "demo_data"
HISTORY, DAILY, USERS, SETTINGS = (DATA / n for n in ("history.csv", "daily.csv", "users.json", "settings.json"))

DEMO = bool(os.environ.get("DEALEROS_DEMO"))  # public demo: no shared settings or user changes
ROLES = ["admin", "parts", "sales", "service"]
DEFAULT_SETTINGS = {"dealer_name": "Demo Honda Dealership", "lead_days": 10, "review_days": 7, "z": 1.65,
                    "min_active": 3, "calendar": True, "report_emails": [], "report_lang": "en"}


def _seed():
    """First run: start from the demo data so the app is never empty."""
    DATA.mkdir(parents=True, exist_ok=True)
    for f in DEMO_DIR.glob("*"):
        if not (DATA / f.name).exists():
            shutil.copy(f, DATA / f.name)


_seed()


def history():
    return pd.read_csv(HISTORY, dtype={"month": str, "part": str}) if HISTORY.exists() else pd.DataFrame()


def add_export(df):
    """Merge a new export. Months in the upload replace the same months already stored."""
    old = history()
    if len(old):
        old = old[~old.month.isin(df.month.unique())]
    pd.concat([old, df]).sort_values(["month", "part"]).to_csv(HISTORY, index=False)
    return sorted(df.month.unique())


def daily():
    if not DAILY.exists():
        return pd.DataFrame(columns=["date", "part", "qty", "kind", "note", "by"])
    return pd.read_csv(DAILY, dtype={"date": str, "part": str}).fillna({"note": ""})


def add_daily(date, part, qty, kind, note, by):
    row = pd.DataFrame([{"date": str(date), "part": part, "qty": qty, "kind": kind, "note": note, "by": by}])
    row.to_csv(DAILY, mode="a", header=not DAILY.exists(), index=False)


def _hash(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()


def users():
    return json.loads(USERS.read_text()) if USERS.exists() else {}


def check_login(username, pw):
    u = users().get(username.strip().lower())
    return u if u and hmac.compare_digest(u["hash"], _hash(pw, u["salt"])) else None


def save_user(username, name, role, pw):
    all_ = users()
    salt = os.urandom(16).hex()
    all_[username.strip().lower()] = {"name": name, "role": role, "salt": salt, "hash": _hash(pw, salt)}
    USERS.write_text(json.dumps(all_, indent=2))


def settings():
    return {**DEFAULT_SETTINGS, **(json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {})}


def save_settings(s):
    SETTINGS.write_text(json.dumps(s, indent=2))
