# Methods from research

Each entry: what the paper claims, and what **our** experiment (`research/experiments.py`) says on our data.
Adoption rule: a method replaces the current one only if it is not worse on per-part error, total-demand error,
or fill rate for the same stock value. Results on fewer than 12 test months are provisional.

## Papers

| Paper | Claim | Status here |
|---|---|---|
| Bridging Forecast Accuracy and Inventory KPIs (arXiv 2601.21844, 2026) | Better accuracy scores don't necessarily give better inventory results. Judge forecasts in a closed-loop inventory simulation. Open-source simulator: github.com/caisr-hh/TruckParts-Demand-Inventory-Simulator | **Adopted** as the evaluation approach: the fill rate against stock value columns in experiments.py |
| Accuracy Is Not Service (arXiv 2609.13840, 2026) | On real spare-parts orders across 38 methods, accuracy rank and service rank are *negatively* correlated (-0.555). Service follows the *direction of bias*, especially over-forecasting in zero months. | Adopted the same way. Still to do: report forecast bias per method |
| Intermittency and Obsolescence: Croston With Linear Decay (arXiv 1409.1609) | TSB decays exponentially for dead parts. A linear-decay variant reaches zero in finite time. | Not tested yet. Relevant to dead stock |
| Hyperbolic-Exponential Smoothing (arXiv 1307.6102) | A Croston/Bayesian hybrid, unbiased, that decays hyperbolically. | Not tested yet |
| Feature-based intermittent demand forecast combinations (arXiv 2204.08283) | Combining forecasts improves point and quantile accuracy, with inventory implications. | Partly tested: IMAPA is a combination |
| Combining Probabilistic Forecasts of Intermittent Demand (arXiv 2304.03092) | Combinations beat single methods, but there's a trade-off between forecast accuracy and inventory performance. | Not tested yet |
| Stock-keeping-oriented Prediction Error Costs (arXiv 2004.10537) | MAPE and RMSE are unsuitable for lumpy demand. Proposes a cost-based metric from the automotive aftermarket. | Not tested yet. A candidate extra score |
| Intelligent Routing for Sparse Demand (arXiv 2506.14810) | Picking a model per demand pattern (smooth, lumpy, intermittent) helps. | Not tested yet. Needs more data |

## Experiment log

### 2026-10-29 · real data 2018-10..2020-09 · test months 2020-02, 03, 06, 07, 08, 09 · 803 regular parts
| Method | Per-part error | Total error | Fill @ z=1.28 | Stock value @ z=1.28 |
|---|---|---|---|---|
| tsb (current) | 80.8% | 16.3% | 93.3% | ₹17.39 lakh |
| sba | 80.7% | 17.2% | 92.8% | ₹17.35 lakh |
| ses | 79.9% | 16.0% | 93.4% | ₹17.71 lakh |
| adida k=3 | 79.1% | 19.6% | 94.1% | ₹18.34 lakh |
| imapa | 78.9% | 15.4% | 93.9% | ₹18.01 lakh |
| avg_6m | 83.5% | 20.8% | 92.7% | ₹17.20 lakh |
| tsb + ABC safety (A 2.05 / B 1.65 / C 1.0) | 80.8% | 16.3% | 94.4% | ₹19.24 lakh |

**Reading:**
- IMAPA has the lowest errors but ties with TSB on fill rate for the same stock value: TSB interpolates to about 93.9% at ₹18.0 lakh.
- ABC safety levels cost about ₹90,000 more stock than TSB at z=1.65 (94.2% at ₹18.33 lakh) for nearly the same fill rate. Rejected for now.
- avg_6m is beaten on every score.

**Decision:** keep TSB, which also lets dying parts fade out. Re-run IMAPA on the 2024–26 export.
