"""Parts demand forecast + reorder list, built from HiRise "Month Wise Stock Report (Detailed)" exports.

Model: TSB (Teunter-Syntetos-Babai) per part. Spare parts sell in bursts with many zero months,
so we track two things and update both every month: how big an order is when one comes (size)
and how often a month has any demand (probability). Forecast = size * probability.
Every new month of data moves both, which is how the model "learns": a part that stops selling
decays toward zero, a part that picks up rises.
"""
import math

import numpy as np
import pandas as pd

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
COLS = {"Part Number": "part", "Part Description": "desc", "Part Category": "category",
        "Opening Stock": "opening", "Received Qty": "received", "Issued Qty": "issued",
        "Closing Stock": "closing", "Closing Unit Price": "price"}
# COVID lockdown: issued qty in these months says nothing about normal demand.
EXCLUDE = ("2020-04", "2020-05")


def fy_month(fy, month_name):
    """('2020-21', 'January') -> '2021-01'. Fiscal year runs April to March."""
    m = MONTHS.index(str(month_name).strip()) + 1
    y = int(str(fy)[:4]) + (1 if m < 4 else 0)
    return f"{y}-{m:02d}"


def read_export(path_or_file, name=""):
    """Read one HiRise export (.xlsx) or a combined CSV into tidy rows: month, part, desc, category, qty columns, price."""
    name = name or str(path_or_file)
    if name.lower().endswith(".csv"):
        raw = pd.read_csv(path_or_file)
    else:
        raw = pd.read_excel(path_or_file, header=None)
        hdr = raw.index[raw.eq("Part Number").any(axis=1)][0]
        raw.columns = raw.iloc[hdr]
        raw = raw.iloc[hdr + 1:]
    # Fiscal Year / Month / Category are blank on continuation rows in some exports.
    raw = raw.dropna(subset=["Part Number"]).ffill().infer_objects()
    if "month" not in raw:
        raw["month"] = [fy_month(f, m) for f, m in zip(raw["Fiscal Year"], raw["Month Name"])]
    df = raw.rename(columns=COLS)[["month", *COLS.values()]]
    for c in ["opening", "received", "issued", "closing", "price"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df.groupby(["month", "part"], as_index=False).agg(
        desc=("desc", "first"), category=("category", "first"), opening=("opening", "sum"),
        received=("received", "sum"), issued=("issued", "sum"), closing=("closing", "sum"),
        price=("price", "max"))


def tsb(series, alpha=0.2, beta=0.2):
    """series: monthly demand, NaN = month not observed (skipped).
    Returns (monthly rate, monthly error sigma). Errors are one-step-ahead, so sigma is honest."""
    obs = [y for y in series if not math.isnan(y)]
    nz = [y for y in obs if y > 0]
    if not nz:
        return 0.0, 0.0
    z, p = float(np.mean(nz)), len(nz) / len(obs)
    errors = []
    for y in obs:
        errors.append(y - z * p)
        p += beta * ((y > 0) - p)
        if y > 0:
            z += alpha * (y - z)
    rate = z * p
    sigma = float(np.sqrt(np.mean(np.square(errors)))) if len(errors) >= 3 else math.sqrt(rate)
    return rate, sigma


def demand_matrix(history, daily=None, exclude=EXCLUDE, through=None):
    """parts x months demand. Lost sales are added back (they are demand we couldn't serve).
    NaN where demand was unobservable: before a part first appears, excluded months,
    and months with no stock at all and nothing recorded (zero sales there means nothing)."""
    h = history if through is None else history[history.month <= through]
    issued = h.pivot_table(index="part", columns="month", values="issued", aggfunc="sum")
    avail = h.pivot_table(index="part", columns="month", values="opening", aggfunc="sum") \
        + h.pivot_table(index="part", columns="month", values="received", aggfunc="sum")
    demand = issued.copy()
    if daily is not None and len(daily):
        d = daily.assign(month=daily.date.str[:7])
        # A half-finished month would look like a slow month, so only complete months feed the model.
        # This month's lost sales still reach the order list through reorder(open_lost=...).
        d = d[(d.month <= (through or "9999")) & (d.month < pd.Timestamp.today().strftime("%Y-%m"))]
        lost = d[d.kind == "lost"].pivot_table(index="part", columns="month", values="qty", aggfunc="sum")
        # Daily sales only count for months that have no HiRise export yet (avoid double counting).
        sale = d[(d.kind == "sale") & ~d.month.isin(h.month.unique())] \
            .pivot_table(index="part", columns="month", values="qty", aggfunc="sum")
        demand = demand.add(lost, fill_value=0).add(sale, fill_value=0)
    demand = demand.reindex(sorted(demand.columns), axis=1)
    avail = avail.reindex_like(demand)
    blind = (avail.fillna(0) <= 0) & (demand.fillna(0) <= 0)
    demand = demand.mask(blind)
    for m in exclude:
        if m in demand:
            demand[m] = np.nan
    return demand


def forecast(history, daily=None, through=None, exclude=EXCLUDE):
    """One row per part: monthly rate, sigma, latest stock and price."""
    h = history if through is None else history[history.month <= through]
    demand = demand_matrix(h, daily, exclude)
    rows = [(part, *tsb(demand.loc[part].to_numpy(dtype=float))) for part in demand.index]
    fc = pd.DataFrame(rows, columns=["part", "rate", "sigma"]).set_index("part")
    last = h.sort_values("month").groupby("part").last()
    fc = fc.join(last[["desc", "category", "closing", "price", "month"]].rename(columns={"month": "last_seen"}))
    fc["stock"] = fc.closing
    if daily is not None and len(daily):
        after = daily[daily.date.str[:7] > h.month.max()]
        moves = after.assign(sign=after.kind.map({"sale": -1, "received": 1}).fillna(0))
        fc["stock"] = (fc.stock + (moves.qty * moves.sign).groupby(moves.part).sum()
                       .reindex(fc.index).fillna(0)).clip(lower=0)
    return fc


def reorder(fc, lead_days=10, review_days=7, z=1.65, open_lost=None):
    """Order-up-to policy for a weekly (review_days) order: stock enough to cover until the
    next order arrives, plus a safety buffer of z * sigma. z=1.65 ~ 95% of weeks without a stockout."""
    cover = (lead_days + review_days) / 30
    target = fc.rate * cover + z * fc.sigma * math.sqrt(cover)
    need = target - fc.stock
    if open_lost is not None:  # customers asked this month and walked away: at least cover them
        need = np.maximum(need, open_lost.reindex(fc.index).astype(float).fillna(0) - fc.stock)
    out = fc.assign(target=target.round(1), order=np.floor(need.clip(lower=0) + 0.5).astype(int))
    out["order_value"] = (out.order * out.price).round(0)
    out["days_left"] = (out.stock / (out.rate / 30)).round(0)  # at current sales pace
    return out[out.order > 0].sort_values(["days_left", "order_value"], ascending=[True, False])


def dead_stock(history, months=12):
    """Parts holding stock with zero issues in the last `months` months."""
    recent = sorted(history.month.unique())[-months:]
    sold = history[history.month.isin(recent)].groupby("part").issued.sum()
    last = history[history.month == history.month.max()].set_index("part")
    dead = last[(last.closing > 0) & (sold.reindex(last.index).fillna(0) == 0)]
    return dead.assign(value=(dead.closing * dead.price).round(0))[["desc", "category", "closing", "price", "value"]] \
        .sort_values("value", ascending=False)


def backtest(history, months_back=6, **policy):
    """Replay the last `months_back` months: at the end of each month, forecast with only the data
    known then, and check against what happened next month. Fast movers = sells >= 1/month."""
    months = sorted(history.month.unique())
    err = {"model": 0.0, "last_month": 0.0, "avg_6m": 0.0}
    n = out_all = hit_all = out_fast = hit_fast = 0
    pairs = [(p, m) for p, m in zip(months[:-1], months[1:]) if m not in EXCLUDE][-months_back:]
    for prev, m in pairs:
        fc = forecast(history, through=prev)
        train = demand_matrix(history, through=prev)
        t = history[history.month == m].set_index("part")
        parts = t.index.union(fc.index)
        actual = t.issued.reindex(parts).fillna(0)
        for name, guess in [("model", fc.rate), ("last_month", train.ffill(axis=1).iloc[:, -1]),
                            ("avg_6m", train.iloc[:, -6:].mean(axis=1))]:
            err[name] += float((guess.reindex(parts).fillna(0) - actual).abs().sum())
        n += len(parts)
        # Sold out during month m, having started it with stock. Parts already at zero would be
        # flagged just for being empty, which isn't foresight, so they don't count.
        out = set(t.index[(t.closing <= 0) & (t.issued > 0)]) & set(fc.index[fc.stock > 0])
        fast, flagged = set(fc.index[fc.rate >= 1]), set(reorder(fc, **policy).index)
        out_all, hit_all = out_all + len(out), hit_all + len(out & flagged)
        out_fast, hit_fast = out_fast + len(out & fast), hit_fast + len(out & fast & flagged)
    return {"months": [m for _, m in pairs], "mae": {k: round(v / n, 3) for k, v in err.items()},
            "stockouts": out_all, "flagged": hit_all, "fast_stockouts": out_fast, "fast_flagged": hit_fast}


if __name__ == "__main__":
    import sys
    # Logic checks on toy data.
    assert fy_month("2020-21", "January") == "2021-01" and fy_month("2018-19", "October") == "2018-10"
    assert tsb([0, 0, 0]) == (0.0, 0.0)
    steady, _ = tsb([4.0] * 12)
    assert abs(steady - 4) < 1e-9, steady
    fading, _ = tsb([5, 5, 5, 5, 0, 0, 0, 0, 0, 0])
    assert fading < 2, fading  # stopped selling -> forecast decays
    fc = pd.DataFrame({"rate": [10.0, 0.1], "sigma": [2.0, 0.3], "stock": [0, 5], "price": [100, 50]},
                      index=["FAST", "SLOW"])
    r = reorder(fc, lead_days=10, review_days=7)
    assert list(r.index) == ["FAST"] and r.loc["FAST", "order"] == 8, r
    print("logic checks ok")
    if len(sys.argv) > 1:
        h = read_export(sys.argv[1])
        print(backtest(h))
