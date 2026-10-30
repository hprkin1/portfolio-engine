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
| BTC only, capital               |    62.81 |        42.09 |     1.37 |      1.98 |     -30.66 |     2.05 |           529 |
| BTC only, inverse-vol           |    66.31 |        41.98 |     1.42 |      2.04 |     -30.05 |     2.21 |           507 |
| BTC + oil, capital              |    53.82 |        38.35 |     1.31 |      1.9  |     -28.08 |     1.92 |           530 |
| BTC + oil, inverse-vol          |    27.13 |        17.33 |     1.47 |      2.05 |     -15.27 |     1.78 |           461 |
| BTC + oil, inverse-vol, cap 50% |    34.74 |        22.53 |     1.44 |      2.05 |     -17.95 |     1.94 |           509 |

- BTC + oil, inverse-vol: average capital weights {'BTC OBV Momentum': 0.168, 'BTC AC Momentum': 0.17, 'Oil Trend/Carry BNO': 0.661}; latest {'BTC OBV Momentum': 0.27, 'BTC AC Momentum': 0.24, 'Oil Trend/Carry BNO': 0.49}; P&L contribution % of book {'BTC OBV Momentum': 161.0, 'BTC AC Momentum': 130.7, 'Oil Trend/Carry BNO': 75.3}
- BTC + oil, inverse-vol, cap 50%: average capital weights {'BTC OBV Momentum': 0.248, 'BTC AC Momentum': 0.253, 'Oil Trend/Carry BNO': 0.5}; latest {'BTC OBV Momentum': 0.27, 'BTC AC Momentum': 0.24, 'Oil Trend/Carry BNO': 0.49}; P&L contribution % of book {'BTC OBV Momentum': 284.8, 'BTC AC Momentum': 213.5, 'Oil Trend/Carry BNO': 79.1}

**From 2022-01-01**

|                                 |   CAGR % |   Ann. Vol % |   Sharpe |   Sortino |   Max DD % |   Calmar |   Max DD Days |
|:--------------------------------|---------:|-------------:|---------:|----------:|-----------:|---------:|--------------:|
| BTC only, capital               |    38.18 |        35.51 |     1.09 |      1.58 |     -26.07 |     1.46 |           513 |
| BTC only, inverse-vol           |    41.09 |        35.59 |     1.14 |      1.65 |     -26.88 |     1.53 |           506 |
| BTC + oil, capital              |    29.78 |        28.79 |     1.05 |      1.53 |     -24.22 |     1.23 |           531 |
| BTC + oil, inverse-vol          |    16.36 |        15.22 |     1.07 |      1.47 |     -17.29 |     0.95 |           461 |
| BTC + oil, inverse-vol, cap 50% |    22.79 |        19.54 |     1.15 |      1.65 |     -17.95 |     1.27 |           509 |

- BTC + oil, inverse-vol: average capital weights {'BTC OBV Momentum': 0.172, 'BTC AC Momentum': 0.171, 'Oil Trend/Carry BNO': 0.657}; latest {'BTC OBV Momentum': 0.27, 'BTC AC Momentum': 0.24, 'Oil Trend/Carry BNO': 0.49}; P&L contribution % of book {'BTC OBV Momentum': 49.5, 'BTC AC Momentum': 39.0, 'Oil Trend/Carry BNO': 19.6}
- BTC + oil, inverse-vol, cap 50%: average capital weights {'BTC OBV Momentum': 0.253, 'BTC AC Momentum': 0.254, 'Oil Trend/Carry BNO': 0.494}; latest {'BTC OBV Momentum': 0.27, 'BTC AC Momentum': 0.24, 'Oil Trend/Carry BNO': 0.49}; P&L contribution % of book {'BTC OBV Momentum': 85.4, 'BTC AC Momentum': 62.0, 'Oil Trend/Carry BNO': 22.2}

Sleeve return correlation (from 2020-06):

|                     |   BTC OBV Momentum |   BTC AC Momentum |   Oil Trend/Carry BNO |
|:--------------------|-------------------:|------------------:|----------------------:|
| BTC OBV Momentum    |               1    |              0.48 |                 -0.05 |
| BTC AC Momentum     |               0.48 |              1    |                 -0.01 |
| Oil Trend/Carry BNO |              -0.05 |             -0.01 |                  1    |


## Correction (2026-10-30, later the same day)

The book numbers in this file were regenerated after fixing a stop-loss bug in the engine (see
`engine/stopsim.py` and the README "Correction" section). The fix only affects the BTC AC sleeve
(the only strategy with a stop). The verdict text above was written before the fix; the tables
above are current. Updated reading: risk weighting still cuts book vol and drawdown, but with the
corrected (stronger) AC sleeve, adding oil now *lowers* book Sharpe rather than leaving it flat.
