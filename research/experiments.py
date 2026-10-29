"""Try forecasting methods / ordering policies from research against our data before adopting them.
    python research/experiments.py <HiRise export or combined CSV>
Every candidate is scored on the same test months and the same regular parts (chosen by the current model),
on three things:
  wape      - per-part forecast error, weighted by volume (lower is better)
  total_err - error on the dealership's total demand (lower is better)
  fill / stock_value - inventory simulation: each month, top stock up to the policy's target and see how much
              of the real demand it would have served (fill rate) and how much stock value it carried.
Research (arXiv 2601.21844, 2609.13840) shows lower forecast error does not mean better service for spare
parts, so fill rate vs stock value is the deciding score. Adopt a candidate only if it is not worse on any
of the three; record the result in research/methods.md."""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import forecast as F  # noqa: E402


def _obs(series):
    return [y for y in series if not math.isnan(y)]


def ses_blocks(series, k=1, alpha=0.2):
    """ADIDA: add up non-overlapping blocks of k months, smooth the block totals, divide back by k.
    Aggregating hides the zeros that make intermittent parts hard (Nikolopoulos et al. 2011)."""
    obs = _obs(series)
    obs = obs[len(obs) % k:]
    blocks = [sum(obs[i:i + k]) for i in range(0, len(obs), k)]
    if not blocks or not any(blocks):
        return 0.0, 0.0
    level, errors = blocks[0], []
    for b in blocks[1:]:
        errors.append(b - level)
        level += alpha * (b - level)
    sigma = float(np.sqrt(np.mean(np.square(errors)))) / math.sqrt(k) if len(errors) >= 2 else math.sqrt(level / k)
    return level / k, sigma


def imapa(series):
    """IMAPA: average ADIDA over block sizes 1..3 (Petropoulos & Kourentzes 2015)."""
    runs = [ses_blocks(series, k) for k in (1, 2, 3)]
    return float(np.mean([r for r, _ in runs])), float(np.mean([s for _, s in runs]))


def sba(series, alpha=0.2):
    """Croston with the Syntetos-Boylan bias correction."""
    obs = _obs(series)
    if not any(obs):
        return 0.0, 0.0
    z = p = None
    q, errors = 1, []
    for y in obs:
        if z is not None:
            errors.append(y - z / p)
        if y > 0:
            z, p = (y, q) if z is None else (z + alpha * (y - z), p + alpha * (q - p))
            q = 1
        else:
            q += 1
    rate = (1 - alpha / 2) * z / p
    return rate, float(np.sqrt(np.mean(np.square(errors)))) if len(errors) >= 3 else math.sqrt(rate)


def mean6(series):
    obs = _obs(series)[-6:]
    return (float(np.mean(obs)), float(np.std(obs))) if obs else (0.0, 0.0)


FORECASTERS = {"tsb (current)": F.tsb, "sba": sba, "ses": lambda s: ses_blocks(s, 1),
               "adida k=3": lambda s: ses_blocks(s, 3), "imapa": imapa, "avg_6m": mean6}


def abc_z(train, prices, z_by_class=(2.05, 1.65, 1.0)):
    """Part-class safety: A = parts making the top 80% of issued value, B the next 15%, C the rest."""
    value = (train.iloc[:, -12:].sum(axis=1) * prices.reindex(train.index).fillna(0)).sort_values(ascending=False)
    share = value.cumsum() / max(value.sum(), 1)
    return pd.Series(np.select([share <= 0.8, share <= 0.95], z_by_class[:2], z_by_class[2]), index=value.index)


def run(history, months_back=6, zs=(1.0, 1.28, 1.65, 2.05)):
    history = F.latest_run(history)
    months = sorted(history.month.unique())
    pairs = [(p, m) for p, m in zip(months[:-1], months[1:]) if m not in F.EXCLUDE][-months_back:]
    policies = [(name, z) for name in FORECASTERS for z in zs] + [("tsb + ABC safety", "abc")]
    acc = {p: {"err": 0.0, "units": 0.0, "tot_err": 0.0, "served": 0.0, "stock_value": 0.0} for p in policies}
    for prev, m in pairs:
        fc = F.forecast(history, through=prev, target=m)
        train = F.demand_matrix(F.latest_run(history[history.month <= prev]))
        reg = fc.index[fc.regular]
        t = history[history.month == m].set_index("part")
        actual = t.issued.reindex(reg).fillna(0)
        price = fc.price.reindex(reg).fillna(0)
        stock = fc.stock.reindex(reg).fillna(0)
        rows = {name: pd.DataFrame([f(train.loc[p].to_numpy(float)) if p in train.index else (0.0, 0.0)
                                    for p in reg], index=reg, columns=["rate", "sigma"])
                for name, f in FORECASTERS.items()}
        zabc = abc_z(train, fc.price).reindex(reg).fillna(1.0)
        for name, z in policies:
            r = rows["tsb (current)" if z == "abc" else name]
            zz = zabc if z == "abc" else z
            available = np.maximum(stock, np.floor(r.rate + zz * r.sigma + 0.5))  # top up for one month
            a = acc[(name, z)]
            a["err"] += float((r.rate - actual).abs().sum())
            a["tot_err"] += abs(float(r.rate.sum() - actual.sum()))
            a["units"] += float(actual.sum())
            a["served"] += float(np.minimum(available, actual).sum())
            a["stock_value"] += float((available * price).sum())
    n = len(pairs)
    out = pd.DataFrame([{"method": name, "z": z, "wape": a["err"] / a["units"], "total_err": a["tot_err"] / a["units"],
                         "fill": a["served"] / a["units"], "avg_stock_value": a["stock_value"] / n}
                        for (name, z), a in acc.items()])
    return out, [m for _, m in pairs], len(reg)


if __name__ == "__main__":
    # Self-check: ADIDA on a part selling 3 every third month forecasts ~1/month.
    r, _ = ses_blocks([0, 0, 3] * 6, 3)
    assert abs(r - 1) < 1e-9, r
    assert sba([0, 0, 0]) == (0.0, 0.0) and abs(sba([2.0] * 10)[0] - 1.8) < 1e-9
    print("experiment checks ok")
    if len(sys.argv) > 1:
        res, months, n_reg = run(F.read_export(sys.argv[1]))
        print(f"test months {months}, {n_reg} regular parts (provisional: small sample)\n")
        print(res.round({"wape": 3, "total_err": 3, "fill": 3, "avg_stock_value": 0}).to_string(index=False))
