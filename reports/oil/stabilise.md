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
|  1 | 0.56 | 0.69 | 0.55 |
|  3 | 1.14 | 0.66 | 0.51 |
|  5 | 0.69 | 0.57 | 0.41 |
| 10 | 0.27 | 0.24 | 0.23 |
| 20 | 0.34 | 0.39 | 0.38 |

**BNO OOS Sharpe (2× costs)**

|    |    1 |    5 |   10 |
|---:|-----:|-----:|-----:|
|  1 | 0.45 | 0.6  | 0.47 |
|  3 | 1.09 | 0.61 | 0.46 |
|  5 | 0.65 | 0.53 | 0.38 |
| 10 | 0.25 | 0.22 | 0.21 |
| 20 | 0.33 | 0.38 | 0.37 |

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
| BNO OOS before costs×1 |     7.31 |        14.45 |     0.56 |     -38.01 |     0.19 |       11.2  |        41.17 |
| BNO OOS before costs×2 |     5.57 |        14.46 |     0.45 |     -41.76 |     0.13 |       11.2  |        41.17 |
| BNO OOS before costs×3 |     3.85 |        14.48 |     0.33 |     -45.28 |     0.09 |       11.2  |        41.17 |
| BNO IS after costs×1   |     8.84 |        14.34 |     0.67 |     -32    |     0.28 |        1.7  |        48.98 |
| BNO IS after costs×2   |     8.48 |        14.34 |     0.64 |     -32.42 |     0.26 |        1.7  |        48.98 |
| BNO OOS after costs×1  |     2.27 |        12.57 |     0.24 |     -24.95 |     0.09 |        1.24 |        36.8  |
| BNO OOS after costs×2  |     2.02 |        12.58 |     0.22 |     -25.54 |     0.08 |        1.24 |        36.8  |
| BNO OOS after costs×3  |     1.77 |        12.58 |     0.2  |     -26.12 |     0.07 |        1.24 |        36.8  |

## B. Book weighting (BTC OBV + BTC AC + stabilised BNO oil)

capital = equal dollars, never rebalanced. inverse_vol = equal risk budget per sleeve, capital ∝ 1/trailing 252-day vol (floor 5%), rebalanced month-end, 10 bp charged on capital moved.

**From 2020-06-01**

|                                 |   CAGR % |   Ann. Vol % |   Sharpe |   Sortino |   Max DD % |   Calmar |   Max DD Days |
|:--------------------------------|---------:|-------------:|---------:|----------:|-----------:|---------:|--------------:|
| BTC only, capital               |    66.65 |        41.69 |     1.43 |      2.14 |     -25.59 |     2.6  |           237 |
| BTC only, inverse-vol           |    68.97 |        41.61 |     1.47 |      2.17 |     -25.41 |     2.71 |           240 |
| BTC + oil, capital              |    57.37 |        38.08 |     1.38 |      2.05 |     -23.35 |     2.46 |           237 |
| BTC + oil, inverse-vol          |    28.41 |        17.34 |     1.53 |      2.18 |     -13.96 |     2.04 |           382 |
| BTC + oil, inverse-vol, cap 50% |    36.02 |        22.35 |     1.49 |      2.18 |     -17.06 |     2.11 |           360 |

- BTC + oil, inverse-vol: average capital weights {'BTC OBV Momentum': 0.175, 'BTC AC Momentum': 0.169, 'Oil Trend/Carry BNO': 0.656}; latest {'BTC OBV Momentum': 0.27, 'BTC AC Momentum': 0.24, 'Oil Trend/Carry BNO': 0.49}; P&L contribution % of book {'BTC OBV Momentum': 182.4, 'BTC AC Momentum': 132.7, 'Oil Trend/Carry BNO': 82.8}
- BTC + oil, inverse-vol, cap 50%: average capital weights {'BTC OBV Momentum': 0.253, 'BTC AC Momentum': 0.247, 'Oil Trend/Carry BNO': 0.499}; latest {'BTC OBV Momentum': 0.27, 'BTC AC Momentum': 0.24, 'Oil Trend/Carry BNO': 0.49}; P&L contribution % of book {'BTC OBV Momentum': 317.5, 'BTC AC Momentum': 213.6, 'Oil Trend/Carry BNO': 88.6}

**From 2022-01-01**

|                                 |   CAGR % |   Ann. Vol % |   Sharpe |   Sortino |   Max DD % |   Calmar |   Max DD Days |
|:--------------------------------|---------:|-------------:|---------:|----------:|-----------:|---------:|--------------:|
| BTC only, capital               |    43.37 |        35.35 |     1.19 |      1.79 |     -24.66 |     1.76 |           238 |
| BTC only, inverse-vol           |    45.08 |        35.32 |     1.23 |      1.83 |     -25.22 |     1.79 |           240 |
| BTC + oil, capital              |    34.25 |        29.17 |     1.15 |      1.73 |     -21.59 |     1.59 |           238 |
| BTC + oil, inverse-vol          |    17.97 |        15.21 |     1.16 |      1.63 |     -17.04 |     1.06 |           382 |
| BTC + oil, inverse-vol, cap 50% |    24.74 |        19.39 |     1.24 |      1.82 |     -17.06 |     1.45 |           360 |

- BTC + oil, inverse-vol: average capital weights {'BTC OBV Momentum': 0.178, 'BTC AC Momentum': 0.17, 'Oil Trend/Carry BNO': 0.652}; latest {'BTC OBV Momentum': 0.27, 'BTC AC Momentum': 0.24, 'Oil Trend/Carry BNO': 0.49}; P&L contribution % of book {'BTC OBV Momentum': 59.1, 'BTC AC Momentum': 40.4, 'Oil Trend/Carry BNO': 22.9}
- BTC + oil, inverse-vol, cap 50%: average capital weights {'BTC OBV Momentum': 0.258, 'BTC AC Momentum': 0.249, 'Oil Trend/Carry BNO': 0.493}; latest {'BTC OBV Momentum': 0.27, 'BTC AC Momentum': 0.24, 'Oil Trend/Carry BNO': 0.49}; P&L contribution % of book {'BTC OBV Momentum': 100.5, 'BTC AC Momentum': 64.0, 'Oil Trend/Carry BNO': 26.4}

Sleeve return correlation (from 2020-06):

|                     |   BTC OBV Momentum |   BTC AC Momentum |   Oil Trend/Carry BNO |
|:--------------------|-------------------:|------------------:|----------------------:|
| BTC OBV Momentum    |               1    |              0.5  |                 -0.06 |
| BTC AC Momentum     |               0.5  |              1    |                 -0.01 |
| Oil Trend/Carry BNO |              -0.06 |             -0.01 |                  1    |
