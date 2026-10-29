"""Parts demand forecast + reorder list, built from HiRise "Month Wise Stock Report (Detailed)" exports.

Model, in two layers:
1. Calendar factor (whole dealership): a log-linear fit on the total monthly demand of regular parts,
   with annual growth, a festive-month flag (Dhanteras..Diwali) and month-of-year seasonality.
   Each term switches on only when there is enough history to estimate it (see FIT_RULES).
2. Per part: TSB (Teunter-Syntetos-Babai) on the part's demand with the calendar factor divided out.
   Spare parts sell in bursts with many zero months, so TSB tracks how much sells when it sells (size)
   and how often a month has any sale (probability), and updates both every month. That is how the
   model learns: a part that stops selling fades out, one that picks up rises.
Forecast for a month = part level x calendar factor of that month.
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
# Festive = any month touched by Dhanteras..Diwali (Lakshmi Puja). Sources: timeanddate.com (2021-31),
# drikpanchang (2026), learnreligions (2019-25). 2024 straddled Oct 31 / Nov 1, so both months count.
FESTIVE = {
    "2018-11": "Dhanteras 5 Nov, Diwali 7 Nov", "2019-10": "25-27 Oct", "2020-11": "13-14 Nov",
    "2021-11": "2-4 Nov", "2022-10": "22-24 Oct", "2023-11": "10-12 Nov",
    "2024-10": "29 Oct - 1 Nov", "2024-11": "29 Oct - 1 Nov", "2025-10": "18-20 Oct",
    "2026-11": "6-8 Nov", "2027-10": "Diwali 29 Oct", "2028-10": "Diwali 17 Oct",
}
# Minimum history before each calendar term is estimated (else it stays at "no effect").
# Growth needs 2 full years too: with one year it cannot be told apart from seasonality.
FIT_RULES = {"growth_months": 24, "festive_months": 2, "season_months": 24}
GROWTH_CAP = (-0.3, 0.5)  # ponytail: clamp annual growth; a short run can't support more


def fy_month(fy, month_name):
    """('2020-21', 'January') -> '2021-01'. Fiscal year runs April to March."""
    m = MONTHS.index(str(month_name).strip()) + 1
    y = int(str(fy)[:4]) + (1 if m < 4 else 0)
    return f"{y}-{m:02d}"


def add_months(month, n):
    y, m = divmod(int(month[:4]) * 12 + int(month[5:7]) - 1 + n, 12)
    return f"{y}-{m + 1:02d}"


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


def latest_run(history, min_months=12):
    """Keep the latest unbroken run of months (e.g. 2024-10.. when 2020-10..2024-09 was never exported),
    so a gap of missing years isn't read as consecutive months. Falls back to everything if the run is short."""
    months = sorted(history.month.unique())
    start = 0
    for i in range(1, len(months)):
        if add_months(months[i - 1], 1) != months[i]:
            start = i
    return history if len(months) - start < min_months else history[history.month >= months[start]]


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
        d = d[(d.month <= (through or "9999")) & (d.month < pd.Timestamp.today().strftime("%Y-%m"))
              & (d.month >= h.month.min())]
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


def regular_parts(demand, min_active=3):
    """A part is 'regular' (keep it on the shelf) if it sells in at least `min_active` of 12 months,
    counting only months where it could be seen. An always-out-of-stock part still qualifies."""
    last12 = demand.iloc[:, -12:]
    observed, active = last12.notna().sum(axis=1), (last12 > 0).sum(axis=1)
    rate12 = active / observed.replace(0, np.nan) * 12
    return pd.DataFrame({"active": active, "observed": observed,
                         "regular": (observed >= 3) & (rate12 >= min_active)})


class Calendar:
    """Dealership-wide calendar factor: exp(growth*years + festive*flag + season[month])."""

    def __init__(self, demand, regular):
        tot = demand[regular].sum(axis=0, min_count=1).dropna()
        tot = tot[tot > 0]
        # Skip the opening ramp-up (a new dealership filling its shelves) and any near-empty month.
        ok = tot >= 0.5 * tot.median()
        tot = tot[ok.cummax()] if len(tot) else tot
        self.t0 = tot.index[0] if len(tot) else None
        self.growth = self.festive = 0.0
        self.season = {m: 0.0 for m in range(1, 13)}
        self.used = {"months": len(tot), "festive_months": int(sum(m in FESTIVE for m in tot.index))}
        if len(tot) < FIT_RULES["growth_months"]:
            return
        cols = [np.ones(len(tot)), [self._years(m) for m in tot.index]]
        use_fest = self.used["festive_months"] >= FIT_RULES["festive_months"]
        use_season = len(tot) >= FIT_RULES["season_months"]
        if use_fest:
            cols.append([float(m in FESTIVE) for m in tot.index])
        if use_season:
            cols += [[float(int(m[5:]) == k) for m in tot.index] for k in range(2, 13)]  # Jan = baseline
        coef = np.linalg.lstsq(np.column_stack(cols), np.log(tot.to_numpy(float)), rcond=None)[0]
        self.growth = float(np.clip(coef[1], *np.log1p(GROWTH_CAP)))
        k = 2
        if use_fest:
            n = self.used["festive_months"]
            self.festive, k = float(coef[2]) * n / (n + 1), 3  # shrink: few festive months, less trust
        if use_season:
            years = len(tot) / 12
            raw = np.r_[0.0, coef[k:k + 11]]
            raw = (raw - raw.mean()) * years / (years + 1)
            self.season = {m: float(raw[m - 1]) for m in range(1, 13)}

    def _years(self, month):
        return ((int(month[:4]) - int(self.t0[:4])) * 12 + int(month[5:]) - int(self.t0[5:])) / 12

    def factor(self, month):
        if self.t0 is None:
            return 1.0
        return math.exp(self.growth * self._years(month) + self.festive * (month in FESTIVE)
                        + self.season[int(month[5:])])

    def summary(self):
        return {"annual_growth_pct": round(math.expm1(self.growth) * 100, 1),
                "festive_effect_pct": round(math.expm1(self.festive) * 100, 1),
                "season_pct": {MONTHS[m - 1][:3]: round(math.expm1(v) * 100, 1) for m, v in self.season.items()},
                **self.used}


def forecast(history, daily=None, through=None, target=None, min_active=3, calendar=True):
    """One row per part: forecast for `target` month (default: month after the last export),
    sigma, regular flag, latest stock and price."""
    h = latest_run(history if through is None else history[history.month <= through])
    demand = demand_matrix(h, daily)
    seg = regular_parts(demand, min_active)
    cal = Calendar(demand, seg.regular) if calendar else Calendar(demand.iloc[:0], seg.regular.iloc[:0])
    target = target or add_months(h.month.max(), 1)
    f = pd.Series([cal.factor(m) for m in demand.columns], index=demand.columns)
    base = demand / f  # calendar effects divided out
    rows = [(part, *tsb(base.loc[part].to_numpy(dtype=float))) for part in base.index]
    fc = pd.DataFrame(rows, columns=["part", "rate", "sigma"]).set_index("part")
    fc[["rate", "sigma"]] *= cal.factor(target)
    fc = fc.join(seg)
    last = h.sort_values("month").groupby("part").last()
    fc = fc.join(last[["desc", "category", "closing", "price", "month"]].rename(columns={"month": "last_seen"}))
    fc["stock"] = fc.closing
    if daily is not None and len(daily):
        after = daily[daily.date.str[:7] > h.month.max()]
        moves = after.assign(sign=after.kind.map({"sale": -1, "received": 1}).fillna(0))
        fc["stock"] = (fc.stock + (moves.qty * moves.sign).groupby(moves.part).sum()
                       .reindex(fc.index).fillna(0)).clip(lower=0)
    fc.attrs.update(target=target, calendar=cal.summary())
    return fc


def reorder(fc, lead_days=10, review_days=7, z=1.65, open_lost=None):
    """Order-up-to policy for a weekly (review_days) order, regular parts only: stock enough to cover
    until the next order arrives, plus a safety buffer of z * sigma (z=1.65 ~ 95% of weeks covered).
    Other parts are ordered only when a customer asked and we didn't have it."""
    cover = (lead_days + review_days) / 30
    target = (fc.rate * cover + z * fc.sigma * math.sqrt(cover)).where(fc.regular, 0)
    need = target - fc.stock
    asked = open_lost.reindex(fc.index).astype(float).fillna(0) if open_lost is not None else 0 * need
    need = np.maximum(need, asked - fc.stock)  # customers asked this month and walked away
    out = fc.assign(target=target.round(1), order=np.floor(need.clip(lower=0) + 0.5).astype(int))
    out["why"] = np.where(out.regular, "regular", "customer asked")
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


def backtest(history, months_back=6, min_active=3, **policy):
    """Replay the last `months_back` months: at the end of each month, forecast with only the data known
    then, and score against what happened next month. Scored on regular parts (the ones we stock).
    wape = total |error| / total actual units, so 0.4 means 40% off on average, weighted by volume."""
    history = latest_run(history)
    months = sorted(history.month.unique())
    names = ["model", "no_calendar", "last_month", "avg_6m"]
    err, units, total_err, total_units = dict.fromkeys(names, 0.0), 0.0, dict.fromkeys(names, 0.0), 0.0
    out_n = hit_n = 0
    pairs = [(p, m) for p, m in zip(months[:-1], months[1:]) if m not in EXCLUDE][-months_back:]
    for prev, m in pairs:
        fc = forecast(history, through=prev, target=m, min_active=min_active)
        plain = forecast(history, through=prev, target=m, min_active=min_active, calendar=False)
        train = demand_matrix(latest_run(history[history.month <= prev]))
        reg = fc.index[fc.regular]
        t = history[history.month == m].set_index("part")
        actual = t.issued.reindex(reg).fillna(0)
        guesses = {"model": fc.rate, "no_calendar": plain.rate,
                   "last_month": train.ffill(axis=1).iloc[:, -1], "avg_6m": train.iloc[:, -6:].mean(axis=1)}
        for name, g in guesses.items():
            g = g.reindex(reg).fillna(0)
            err[name] += float((g - actual).abs().sum())
            total_err[name] += abs(float(g.sum() - actual.sum()))
        units += float(actual.sum())
        total_units += float(actual.sum())
        # Regular parts that sold out during month m having started it with stock (parts already at
        # zero would be flagged just for being empty, which isn't foresight).
        out = set(t.index[(t.closing <= 0) & (t.issued > 0)]) & set(fc.index[fc.regular & (fc.stock > 0)])
        out_n, hit_n = out_n + len(out), hit_n + len(out & set(reorder(fc, **policy).index))
    return {"months": [m for _, m in pairs], "regular_parts": int(fc.regular.sum()),
            "wape": {k: round(v / max(units, 1), 3) for k, v in err.items()},
            "total_error": {k: round(v / max(total_units, 1), 3) for k, v in total_err.items()},
            "stockouts": out_n, "flagged": hit_n, "calendar": fc.attrs["calendar"]}


if __name__ == "__main__":
    import sys
    # Logic checks on toy data.
    assert fy_month("2020-21", "January") == "2021-01" and fy_month("2018-19", "October") == "2018-10"
    assert add_months("2024-11", 2) == "2025-01" and add_months("2025-01", -1) == "2024-12"
    assert tsb([0, 0, 0]) == (0.0, 0.0)
    steady, _ = tsb([4.0] * 12)
    assert abs(steady - 4) < 1e-9, steady
    fading, _ = tsb([5, 5, 5, 5, 0, 0, 0, 0, 0, 0])
    assert fading < 2, fading  # stopped selling -> forecast decays
    fc = pd.DataFrame({"rate": [10.0, 0.1, 0.0], "sigma": [2.0, 0.3, 0.0], "stock": [0, 5, 0],
                       "price": [100, 50, 10], "regular": [True, True, False]}, index=["FAST", "SLOW", "RARE"])
    r = reorder(fc, lead_days=10, review_days=7, open_lost=pd.Series({"RARE": 2}))
    assert list(r.index) == ["FAST", "RARE"] and r.loc["FAST", "order"] == 8 and r.loc["RARE", "order"] == 2, r
    # Gap in exported months: only the latest unbroken run is used.
    gap = pd.DataFrame({"month": ["2020-08", "2020-09"] + [add_months("2024-10", i) for i in range(12)]})
    assert latest_run(gap).month.min() == "2024-10"
    # Calendar: 3 years of a series that grows 20%/yr with +30% in festive months is recovered.
    ms = [add_months("2021-01", i) for i in range(36)]
    tot = pd.DataFrame([[100 * 1.2 ** (i / 12) * (1.3 if m in FESTIVE else 1) for i, m in enumerate(ms)]], columns=ms)
    cal = Calendar(tot, pd.Series([True]))
    assert abs(math.expm1(cal.growth) - 0.2) < 0.02 and cal.festive > 0.15, cal.summary()
    print("logic checks ok")
    if len(sys.argv) > 1:
        h = read_export(sys.argv[1])
        print(backtest(h))
