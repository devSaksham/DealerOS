"""Build the public demo dataset from real HiRise exports, with nothing identifying left in it.
Part numbers are replaced, quantities and prices are jittered per part, dates are shifted to look current,
and dealer/network fields are dropped. Usage: python make_demo.py <combined.csv or export.xlsx>"""
import json
import os
import sys

import numpy as np
import pandas as pd

from core import forecast as F
from core.store import DEMO, _hash

rng = np.random.default_rng(7)
h = F.read_export(sys.argv[1])
h = h[~h.month.isin(F.EXCLUDE)]  # drop lockdown months; shifted, they'd look like a random dip
parts = h.part.unique()
fake = dict(zip(parts, [f"DM-{i:05d}" for i in rng.permutation(len(parts))]))
qty_k = pd.Series(rng.uniform(0.7, 1.3, len(parts)), index=parts)
price_k = pd.Series(rng.uniform(0.9, 1.1, len(parts)), index=parts)
for c in ["opening", "received", "issued", "closing"]:
    h[c] = (h[c] * h.part.map(qty_k)).round()
h["price"] = (h.price * h.part.map(price_k)).round(2)
shift = 2026 - int(h.month.max()[:4])
h["month"] = [f"{int(m[:4]) + shift}{m[4:]}" for m in h.month]
h["part"] = h.part.map(fake)

DEMO.mkdir(exist_ok=True)
h.to_csv(DEMO / "history.csv", index=False)
users = {}
for u in ["admin", "parts", "sales", "service"]:
    salt = os.urandom(16).hex()
    users[u] = {"name": f"Demo {u.title()}", "role": u, "salt": salt, "hash": _hash("demo", salt)}
(DEMO / "users.json").write_text(json.dumps(users, indent=2))
print(f"{len(h):,} rows, {h.month.min()} to {h.month.max()}, {len(parts):,} parts -> {DEMO}")
