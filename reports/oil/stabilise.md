# Stabilising the oil strategy + risk-based book weights

Generated 2026-10-30. Rows = confirm_days, columns = spread_smooth. In-sample 2012-01-01→2021-12-31; out-of-sample 2022-01-01→today.

## A. In-sample (selection data)

Selection score = neighbourhood-median Sharpe at 2× costs, averaged over USO+BNO:

|    |    1 |    5 |   10 |
|---:|-----:|-----:|-----:|
|  1 | 0.35 | 0.35 | 0.36 |
|  3 | 0.45 | 0.43 | 0.41 |
|  5 | 0.48 | 0.48 | 0.47 |
| 10 | 0.49 | 0.49 | 0.46 |
| 20 | 0.4  | 0.35 | 0.4  |

**Selected: `{'confirm_days': 10, 'spread_smooth': 5}`** (baseline = confirm 1, smooth 1)

**USO IS Sharpe (1× costs)**

|    |    1 |    5 |   10 |
|---:|-----:|-----:|-----:|
|  1 | 0.46 | 0.37 | 0.5  |
|  3 | 0.39 | 0.31 | 0.3  |
|  5 | 0.42 | 0.41 | 0.34 |
| 10 | 0.4  | 0.45 | 0.41 |
| 20 | 0.01 | 0.26 | 0.13 |

**USO IS Sharpe (2× costs)**

|    |     1 |    5 |   10 |
|---:|------:|-----:|-----:|
|  1 |  0.34 | 0.27 | 0.4  |
|  3 |  0.34 | 0.26 | 0.25 |
|  5 |  0.38 | 0.37 | 0.31 |
| 10 |  0.38 | 0.42 | 0.39 |
| 20 | -0.01 | 0.23 | 0.1  |

**USO IS trades/yr**

|    |    1 |   5 |   10 |
|---:|-----:|----:|-----:|
|  1 | 12.6 | 9.2 |  8.8 |
|  3 |  4   | 3.6 |  3.5 |
|  5 |  2.2 | 2.6 |  2.4 |
| 10 |  1.5 | 1.7 |  1.7 |
| 20 |  1   | 1.2 |  1.3 |

**BNO IS Sharpe (1× costs)**

|    |    1 |    5 |   10 |
|---:|-----:|-----:|-----:|
|  1 | 0.48 | 0.46 | 0.53 |
|  3 | 0.64 | 0.57 | 0.64 |
|  5 | 0.62 | 0.63 | 0.58 |
| 10 | 0.61 | 0.67 | 0.64 |
| 20 | 0.36 | 0.59 | 0.51 |

**BNO IS Sharpe (2× costs)**

|    |    1 |    5 |   10 |
|---:|-----:|-----:|-----:|
|  1 | 0.36 | 0.36 | 0.44 |
|  3 | 0.59 | 0.53 | 0.6  |
|  5 | 0.59 | 0.6  | 0.55 |
| 10 | 0.59 | 0.64 | 0.61 |
| 20 | 0.35 | 0.57 | 0.49 |

**BNO IS trades/yr**

|    |    1 |   5 |   10 |
|---:|-----:|----:|-----:|
|  1 | 11.1 | 8.1 |  7.2 |
|  3 |  3.5 | 3.2 |  2.7 |
|  5 |  2.2 | 2.7 |  2.5 |
| 10 |  1.5 | 1.7 |  1.8 |
| 20 |  1   | 1.3 |  1.4 |

## A. Out-of-sample (looked at once, after selection)

**USO OOS Sharpe (1× costs)**

|    |     1 |    5 |   10 |
|---:|------:|-----:|-----:|
|  1 |  0.32 | 0.44 | 0.44 |
|  3 |  1.02 | 0.52 | 0.35 |
|  5 |  0.59 | 0.51 | 0.33 |
| 10 |  0.29 | 0.34 | 0.34 |
| 20 | -0.01 | 0.11 | 0.08 |

**USO OOS Sharpe (2× costs)**

|    |     1 |    5 |   10 |
|---:|------:|-----:|-----:|
|  1 |  0.18 | 0.34 | 0.34 |
|  3 |  0.97 | 0.46 | 0.3  |
|  5 |  0.55 | 0.47 | 0.29 |
| 10 |  0.27 | 0.33 | 0.32 |
| 20 | -0.02 | 0.1  | 0.07 |

**BNO OOS Sharpe (1× costs)**

|    |    1 |    5 |   10 |
|---:|-----:|-----:|-----:|
|  1 | 0.54 | 0.67 | 0.53 |
|  3 | 1.12 | 0.64 | 0.49 |
|  5 | 0.66 | 0.55 | 0.39 |
| 10 | 0.24 | 0.22 | 0.2  |
| 20 | 0.32 | 0.37 | 0.36 |

**BNO OOS Sharpe (2× costs)**

|    |    1 |    5 |   10 |
|---:|-----:|-----:|-----:|
|  1 | 0.43 | 0.58 | 0.45 |
|  3 | 1.06 | 0.59 | 0.44 |
|  5 | 0.63 | 0.51 | 0.36 |
| 10 | 0.22 | 0.2  | 0.18 |
| 20 | 0.31 | 0.36 | 0.35 |

## A. Before vs after stabilising

|                        |   CAGR % |   Ann. Vol % |   Sharpe |   Max DD % |   Calmar |   Trades/Yr |   Exposure % |
|:-----------------------|---------:|-------------:|---------:|-----------:|---------:|------------:|-------------:|
| USO IS before costs×1  |     5.59 |        14    |     0.46 |     -27.11 |     0.21 |       12.61 |        41.64 |
| USO IS before costs×2  |     3.76 |        14.01 |     0.34 |     -29.09 |     0.13 |       12.61 |        41.64 |
| USO OOS before costs×1 |     3.33 |        12.93 |     0.32 |     -35.39 |     0.09 |       12.66 |        38.98 |
| USO OOS before costs×2 |     1.54 |        12.94 |     0.18 |     -39.47 |     0.04 |       12.66 |        38.98 |
| USO OOS before costs×3 |    -0.22 |        12.96 |     0.05 |     -43.31 |    -0.01 |       12.66 |        38.98 |
| USO IS after costs×1   |     5.17 |        13.45 |     0.45 |     -34.08 |     0.15 |        1.7  |        40.32 |
| USO IS after costs×2   |     4.83 |        13.45 |     0.42 |     -34.66 |     0.14 |        1.7  |        40.32 |
| USO OOS after costs×1  |     3.69 |        13.02 |     0.34 |     -17.6  |     0.21 |        1.45 |        39.97 |
| USO OOS after costs×2  |     3.44 |        13.03 |     0.33 |     -17.71 |     0.19 |        1.45 |        39.97 |
| USO OOS after costs×3  |     3.18 |        13.03 |     0.31 |     -17.83 |     0.18 |        1.45 |        39.97 |
| BNO IS before costs×1  |     6.01 |        14.47 |     0.48 |     -41.64 |     0.14 |       11.11 |        48.66 |
| BNO IS before costs×2  |     4.16 |        14.49 |     0.36 |     -44.23 |     0.09 |       11.11 |        48.66 |
| BNO OOS before costs×1 |     6.98 |        14.44 |     0.54 |     -38.01 |     0.18 |       11.21 |        41.12 |
| BNO OOS before costs×2 |     5.25 |        14.45 |     0.43 |     -41.76 |     0.13 |       11.21 |        41.12 |
| BNO OOS before costs×3 |     3.54 |        14.47 |     0.31 |     -45.28 |     0.08 |       11.21 |        41.12 |
| BNO IS after costs×1   |     8.84 |        14.34 |     0.67 |     -32    |     0.28 |        1.7  |        48.98 |
| BNO IS after costs×2   |     8.48 |        14.34 |     0.64 |     -32.42 |     0.26 |        1.7  |        48.98 |
| BNO OOS after costs×1  |     1.97 |        12.56 |     0.22 |     -24.95 |     0.08 |        1.25 |        36.75 |
| BNO OOS after costs×2  |     1.73 |        12.56 |     0.2  |     -25.54 |     0.07 |        1.25 |        36.75 |
| BNO OOS after costs×3  |     1.48 |        12.57 |     0.18 |     -26.12 |     0.06 |        1.25 |        36.75 |

## B. Book weighting (BTC OBV + BTC AC + stabilised BNO oil)

capital = equal dollars, never rebalanced. inverse_vol = equal risk budget per sleeve, capital ∝ 1/trailing 252-day vol (floor 5%), rebalanced month-end, 10 bp charged on capital moved.

**From 2020-06-01**

|                                 |   CAGR % |   Ann. Vol % |   Sharpe |   Sortino |   Max DD % |   Calmar |   Max DD Days |
|:--------------------------------|---------:|-------------:|---------:|----------:|-----------:|---------:|--------------:|
| BTC only, capital               |    57.12 |        42.44 |     1.28 |      1.85 |     -33.6  |     1.7  |           561 |
| BTC only, inverse-vol           |    56.5  |        41.62 |     1.28 |      1.81 |     -31.29 |     1.81 |           532 |
| BTC + oil, capital              |    48.6  |        38.48 |     1.22 |      1.77 |     -32.14 |     1.51 |           567 |
| BTC + oil, inverse-vol          |    24.78 |        17.14 |     1.38 |      1.92 |     -20.41 |     1.21 |           545 |
| BTC + oil, inverse-vol, cap 50% |    30.79 |        22.34 |     1.31 |      1.86 |     -21.61 |     1.42 |           579 |

- BTC + oil, inverse-vol: average capital weights {'BTC OBV Momentum': 0.168, 'BTC AC Momentum': 0.17, 'Oil Trend/Carry BNO': 0.662}; latest {'BTC OBV Momentum': 0.27, 'BTC AC Momentum': 0.23, 'Oil Trend/Carry BNO': 0.49}; P&L contribution % of book {'BTC OBV Momentum': 153.4, 'BTC AC Momentum': 92.1, 'Oil Trend/Carry BNO': 68.9}
- BTC + oil, inverse-vol, cap 50%: average capital weights {'BTC OBV Momentum': 0.248, 'BTC AC Momentum': 0.252, 'Oil Trend/Carry BNO': 0.499}; latest {'BTC OBV Momentum': 0.27, 'BTC AC Momentum': 0.23, 'Oil Trend/Carry BNO': 0.49}; P&L contribution % of book {'BTC OBV Momentum': 255.5, 'BTC AC Momentum': 137.3, 'Oil Trend/Carry BNO': 67.0}

**From 2022-01-01**

|                                 |   CAGR % |   Ann. Vol % |   Sharpe |   Sortino |   Max DD % |   Calmar |   Max DD Days |
|:--------------------------------|---------:|-------------:|---------:|----------:|-----------:|---------:|--------------:|
| BTC only, capital               |    32.93 |        36    |     0.97 |      1.41 |     -33.28 |     0.99 |           561 |
| BTC only, inverse-vol           |    33    |        35.79 |     0.97 |      1.39 |     -31.29 |     1.05 |           532 |
| BTC + oil, capital              |    25.38 |        28.59 |     0.93 |      1.36 |     -28.68 |     0.88 |           567 |
| BTC + oil, inverse-vol          |    13.93 |        15.21 |     0.93 |      1.29 |     -20.41 |     0.68 |           545 |
| BTC + oil, inverse-vol, cap 50% |    19.19 |        19.68 |     0.99 |      1.42 |     -21.62 |     0.89 |           579 |

- BTC + oil, inverse-vol: average capital weights {'BTC OBV Momentum': 0.173, 'BTC AC Momentum': 0.167, 'Oil Trend/Carry BNO': 0.66}; latest {'BTC OBV Momentum': 0.27, 'BTC AC Momentum': 0.23, 'Oil Trend/Carry BNO': 0.49}; P&L contribution % of book {'BTC OBV Momentum': 46.4, 'BTC AC Momentum': 24.3, 'Oil Trend/Carry BNO': 17.3}
- BTC + oil, inverse-vol, cap 50%: average capital weights {'BTC OBV Momentum': 0.256, 'BTC AC Momentum': 0.25, 'Oil Trend/Carry BNO': 0.494}; latest {'BTC OBV Momentum': 0.27, 'BTC AC Momentum': 0.23, 'Oil Trend/Carry BNO': 0.49}; P&L contribution % of book {'BTC OBV Momentum': 77.4, 'BTC AC Momentum': 37.6, 'Oil Trend/Carry BNO': 18.7}

Sleeve return correlation (from 2020-06):

|                     |   BTC OBV Momentum |   BTC AC Momentum |   Oil Trend/Carry BNO |
|:--------------------|-------------------:|------------------:|----------------------:|
| BTC OBV Momentum    |               1    |              0.44 |                 -0.05 |
| BTC AC Momentum     |               0.44 |              1    |                  0    |
| Oil Trend/Carry BNO |              -0.05 |              0    |                  1    |

## Verdict (2026-10-30)

**Stabilising: it fixed the problem it was meant to fix, at a cost.**
- Trades fell from ~12/yr to ~1.5/yr and cost sensitivity basically disappeared: USO out-of-sample Sharpe at 3× costs went from 0.05 to 0.31, and USO max DD halved (−35% → −18%).
- The declared selection (confirm 10 days, smooth 5) won in-sample by a hair (0.49 vs 0.48 for confirm 5). Out of sample, 10 days is too slow for BNO: Sharpe 0.54 → 0.22. Confirm 3–5 did better out of sample on both ETFs (0.5–1.1), but switching to it now would be choosing on test data. Settle this with a walk-forward selection (re-pick each year using only past data) rather than by eye.

**Risk-based weighting: mostly a risk dial, not a Sharpe boost.**
- An earlier version of this run showed Sharpe 1.50. That depended on a flaw: a 0-vol reading from the oil sleeve sitting flat reset all sleeves to equal weights. With the fix (252-day vol, fall back to the sleeve's own history, 5% floor) the result is:
- From 2020-06: inverse-vol book Sharpe 1.38 vs 1.28 BTC-only, vol 17% vs 42%, max DD −20% vs −34%, but CAGR 25% vs 57%.
- From 2022 (the oil sleeve's out-of-sample period): Sharpe flat (0.93–0.99 everywhere). Max DD drops from −33% to −20/−22%; CAGR drops from 33% to 14–19%.
- Inverse-vol gives oil ~66% of capital, because it's often flat and its realised vol looks low. The 50% cap is the more sensible version.
- A diversifier only lifts book Sharpe if its own Sharpe is decent. At ~0.2–0.5 the oil sleeve mainly lowers risk.
