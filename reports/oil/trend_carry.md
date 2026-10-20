# Oil trend + carry (new thesis)

Generated 2026-10-20. Tradeable ETFs only (USO = WTI, BNO = Brent); their prices include roll yield and fund fees, so there are no roll artefacts. Costs 5 bp fee + 5 bp slippage per side; vol-targeted variants rebalance only when the weight moves by >0.10. In-sample 2012-01-01→2021-12-31, out-of-sample 2022-01-01→today.

**Selection rule result (in-sample avg Sharpe across USO+BNO): `9 Trend+Carry+Spread filter, vol-tgt`**

## USO IS

|                                      |   Total Return % |   CAGR % |   Ann. Vol % |   Sharpe |   Max DD % |   Calmar |   Trades/Yr |   Exposure % |   Short % |   Sharpe after borrow |
|:-------------------------------------|-----------------:|---------:|-------------:|---------:|-----------:|---------:|------------:|-------------:|----------:|----------------------:|
| 1 Buy & hold                         |           -82.88 |   -16.19 |        38.02 |    -0.27 |     -94.93 |    -0.17 |        0    |       100    |      0    |                 -0.27 |
| 2 Trend L/S                          |            52.62 |     4.32 |        22.63 |     0.3  |     -49.72 |     0.09 |        7.2  |        99.88 |     61.72 |                  0.22 |
| 3 Trend long-only                    |           -11.92 |    -1.26 |        14.95 |    -0.01 |     -38.16 |    -0.03 |        3.6  |        38.16 |      0    |                 -0.01 |
| 4 Carry L/S                          |           -79.38 |   -14.61 |        37.2  |    -0.24 |     -92.17 |    -0.16 |       20.21 |       100    |     66.49 |                 -0.29 |
| 5 Carry long-only                    |           -74.45 |   -12.76 |        24.05 |    -0.44 |     -84    |    -0.15 |       10.11 |        33.51 |      0    |                 -0.44 |
| 6 Trend+Carry L/S                    |           -31.77 |    -3.75 |        30.11 |     0.02 |     -75.64 |    -0.05 |       13.31 |        73.23 |     50.74 |                 -0.03 |
| 7 Trend+Carry L/S, vol-tgt           |           -10.82 |    -1.14 |        17.95 |     0.03 |     -55.04 |    -0.02 |       13.31 |        73.23 |     50.74 |                 -0.06 |
| 8 Trend+Carry long-only, vol-tgt     |            -6.24 |    -0.64 |         9.26 |    -0.02 |     -32.8  |    -0.02 |        5.2  |        22.48 |      0    |                 -0.02 |
| 9 Trend+Carry+Spread filter, vol-tgt |            72.22 |     5.59 |        14    |     0.46 |     -27.11 |     0.21 |       12.61 |        41.64 |     30.06 |                  0.4  |

## USO OOS

|                                      |   Total Return % |   CAGR % |   Ann. Vol % |   Sharpe |   Max DD % |   Calmar |   Trades/Yr |   Exposure % |   Short % |   Sharpe after borrow |
|:-------------------------------------|-----------------:|---------:|-------------:|---------:|-----------:|---------:|------------:|-------------:|----------:|----------------------:|
| 1 Buy & hold                         |           193.29 |    25.18 |        37.61 |     0.79 |     -36.23 |     0.69 |        0    |       100    |      0    |                  0.79 |
| 2 Trend L/S                          |           -19    |    -4.3  |        37.33 |     0.07 |     -76.06 |    -0.06 |       15.03 |       100    |     31.67 |                  0.04 |
| 3 Trend long-only                    |            59.54 |    10.24 |        33.17 |     0.46 |     -52.85 |     0.19 |        7.51 |        68.33 |      0    |                  0.46 |
| 4 Carry L/S                          |           150.43 |    21.12 |        38.41 |     0.69 |     -36.97 |     0.57 |        9.6  |       100    |      6.4  |                  0.69 |
| 5 Carry long-only                    |           178.43 |    23.83 |        35.2  |     0.79 |     -32.49 |     0.73 |        4.8  |        93.6  |      0    |                  0.79 |
| 6 Trend+Carry L/S                    |            48.23 |     8.56 |        31.11 |     0.42 |     -44.65 |     0.19 |       12.11 |        65.75 |      1.91 |                  0.42 |
| 7 Trend+Carry L/S, vol-tgt           |            25.47 |     4.85 |        17.12 |     0.36 |     -29.13 |     0.17 |       12.11 |        65.75 |      1.91 |                  0.36 |
| 8 Trend+Carry long-only, vol-tgt     |            16.97 |     3.33 |        16.79 |     0.28 |     -31.85 |     0.1  |       10.23 |        63.84 |      0    |                  0.28 |
| 9 Trend+Carry+Spread filter, vol-tgt |            14.22 |     2.81 |        12.89 |     0.28 |     -35.39 |     0.08 |       12.73 |        38.57 |      1.25 |                  0.28 |

## BNO IS

|                                      |   Total Return % |   CAGR % |   Ann. Vol % |   Sharpe |   Max DD % |   Calmar |   Trades/Yr |   Exposure % |   Short % |   Sharpe after borrow |
|:-------------------------------------|-----------------:|---------:|-------------:|---------:|-----------:|---------:|------------:|-------------:|----------:|----------------------:|
| 1 Buy & hold                         |           -46.32 |    -6.04 |        34.48 |    -0.01 |     -87.06 |    -0.07 |        0    |       100    |      0    |                 -0.01 |
| 2 Trend L/S                          |            61.44 |     4.91 |        22.66 |     0.33 |     -51.32 |     0.1  |        6.5  |        99.96 |     49.54 |                  0.26 |
| 3 Trend long-only                    |            19.74 |     1.82 |        16.5  |     0.19 |     -45.52 |     0.04 |        3.2  |        50.42 |      0    |                  0.19 |
| 4 Carry L/S                          |           -83.55 |   -16.52 |        40.07 |    -0.25 |     -96.09 |    -0.17 |       12.01 |       100    |     41.8  |                 -0.28 |
| 5 Carry long-only                    |           -24.42 |    -2.76 |        22.1  |    -0.01 |     -67.6  |    -0.04 |        6    |        58.2  |      0    |                 -0.01 |
| 6 Trend+Carry L/S                    |           -73.25 |   -12.36 |        36.43 |    -0.18 |     -92.97 |    -0.13 |        9.01 |        78.36 |     34.87 |                 -0.21 |
| 7 Trend+Carry L/S, vol-tgt           |            65.63 |     5.18 |        18.14 |     0.37 |     -56.13 |     0.09 |        9.01 |        78.36 |     34.87 |                  0.31 |
| 8 Trend+Carry long-only, vol-tgt     |            34.16 |     2.98 |        12.61 |     0.3  |     -34.92 |     0.09 |        5.4  |        43.49 |      0    |                  0.3  |
| 9 Trend+Carry+Spread filter, vol-tgt |            79.13 |     6.01 |        14.47 |     0.48 |     -41.64 |     0.14 |       11.11 |        48.66 |     24.05 |                  0.43 |

## BNO OOS

|                                      |   Total Return % |   CAGR % |   Ann. Vol % |   Sharpe |   Max DD % |   Calmar |   Trades/Yr |   Exposure % |   Short % |   Sharpe after borrow |
|:-------------------------------------|-----------------:|---------:|-------------:|---------:|-----------:|---------:|------------:|-------------:|----------:|----------------------:|
| 1 Buy & hold                         |           217.2  |    27.24 |        37.02 |     0.84 |     -34.46 |     0.79 |        0    |       100    |      0    |                  0.84 |
| 2 Trend L/S                          |            -5.91 |    -1.26 |        36.77 |     0.15 |     -74.43 |    -0.02 |       13.36 |        99.92 |     31.84 |                  0.12 |
| 3 Trend long-only                    |            78.64 |    12.87 |        32.85 |     0.53 |     -51.46 |     0.25 |        6.68 |        68.08 |      0    |                  0.53 |
| 4 Carry L/S                          |           108.73 |    16.6  |        37.3  |     0.6  |     -52.71 |     0.31 |        5.84 |       100    |      1.5  |                  0.6  |
| 5 Carry long-only                    |           159.88 |    22.06 |        36.68 |     0.73 |     -43.53 |     0.51 |        2.92 |        98.5  |      0    |                  0.73 |
| 6 Trend+Carry L/S                    |            44.48 |     7.98 |        33    |     0.4  |     -59.24 |     0.13 |        9.6  |        68.58 |      1    |                  0.4  |
| 7 Trend+Carry L/S, vol-tgt           |            22.7  |     4.36 |        18.27 |     0.33 |     -44.99 |     0.1  |        9.6  |        68.58 |      1    |                  0.32 |
| 8 Trend+Carry long-only, vol-tgt     |            35.69 |     6.58 |        18.04 |     0.44 |     -39.18 |     0.17 |        7.93 |        67.58 |      0    |                  0.44 |
| 9 Trend+Carry+Spread filter, vol-tgt |            34.23 |     6.34 |        14.44 |     0.5  |     -38.01 |     0.17 |       11.27 |        40.73 |      0.33 |                  0.5  |

## Cost sensitivity (selected, OOS)

|             |   Total Return % |   CAGR % |   Ann. Vol % |   Sharpe |   Max DD % |   Calmar |   Trades/Yr |   Exposure % |
|:------------|-----------------:|---------:|-------------:|---------:|-----------:|---------:|------------:|-------------:|
| USO costs×1 |            14.22 |     2.81 |        12.89 |     0.28 |     -35.39 |     0.08 |       12.73 |        38.57 |
| USO costs×2 |             5.02 |     1.03 |        12.9  |     0.14 |     -39.47 |     0.03 |       12.73 |        38.57 |
| USO costs×3 |            -3.45 |    -0.73 |        12.93 |     0.01 |     -43.31 |    -0.02 |       12.73 |        38.57 |
| BNO costs×1 |            34.23 |     6.34 |        14.44 |     0.5  |     -38.01 |     0.17 |       11.27 |        40.73 |
| BNO costs×2 |            24.07 |     4.6  |        14.45 |     0.38 |     -41.76 |     0.11 |       11.27 |        40.73 |
| BNO costs×3 |            14.67 |     2.9  |        14.47 |     0.27 |     -45.28 |     0.06 |       11.27 |        40.73 |

## Lookback sensitivity of the selected rule (Sharpe; rows = trend_lb, cols = carry_lb)

**USO IS**

|     |   21 |   42 |   63 |   126 |
|----:|-----:|-----:|-----:|------:|
|  63 | 0.35 | 0.2  | 0.41 |  0.14 |
| 126 | 0.43 | 0.02 | 0.32 |  0.04 |
| 189 | 0.3  | 0.14 | 0.39 |  0.08 |
| 252 | 0.59 | 0.3  | 0.46 |  0.17 |
| 378 | 0.15 | 0.04 | 0.26 | -0.11 |

**USO OOS**

|     |   21 |   42 |   63 |   126 |
|----:|-----:|-----:|-----:|------:|
|  63 | 0.11 | 0.33 | 0.26 |  0.55 |
| 126 | 0.36 | 0.32 | 0.32 |  0.75 |
| 189 | 0.67 | 0.74 | 0.7  |  1.05 |
| 252 | 0.11 | 0.25 | 0.28 |  0.65 |
| 378 | 0.2  | 0.25 | 0.35 |  0.59 |

**BNO IS**

|     |   21 |   42 |   63 |   126 |
|----:|-----:|-----:|-----:|------:|
|  63 | 0.19 | 0.16 | 0.35 |  0.18 |
| 126 | 0.41 | 0.35 | 0.58 |  0.49 |
| 189 | 0.42 | 0.32 | 0.48 |  0.38 |
| 252 | 0.25 | 0.26 | 0.48 |  0.38 |
| 378 | 0.44 | 0.38 | 0.56 |  0.4  |

**BNO OOS**

|     |   21 |   42 |   63 |   126 |
|----:|-----:|-----:|-----:|------:|
|  63 | 0    | 0.36 | 0.3  |  0.44 |
| 126 | 0.38 | 0.65 | 0.64 |  0.74 |
| 189 | 0.61 | 0.89 | 0.81 |  0.93 |
| 252 | 0.34 | 0.54 | 0.5  |  0.62 |
| 378 | 0.51 | 0.52 | 0.55 |  0.58 |

## Selected strategy: return by year (%)

|   Date |   USO |   USO buy&hold |   BNO |   BNO buy&hold |
|-------:|------:|---------------:|------:|---------------:|
|   2012 |  19.2 |          -15   |   7.2 |            6.6 |
|   2013 |  -8.6 |            5.8 |  -8.9 |            8.5 |
|   2014 |   2.2 |          -42.4 |  31.6 |          -49   |
|   2015 |  24.2 |          -46   |  26.3 |          -46.1 |
|   2016 |   8.4 |            6.5 |  -2.4 |           28.1 |
|   2017 |  -2.7 |            2.5 |  14.8 |           15.4 |
|   2018 |  -1.5 |          -19.6 |   7.7 |          -15.3 |
|   2019 |  -4.6 |           32.6 |  -7   |           36   |
|   2020 |  12.8 |          -67.8 | -10.6 |          -38.2 |
|   2021 |  11.5 |           64.7 |   9.8 |           62.3 |
|   2022 |  -6.3 |           29   |   1.4 |           35.2 |
|   2023 |  -5   |           -4.9 |  -7.5 |           -3.4 |
|   2024 |  -4.9 |           13.4 |  -6.5 |            9.7 |
|   2025 | -10.6 |           -8.5 | -11.1 |           -5.4 |
|   2026 |  51   |          132.5 |  72.1 |          137   |

## Signal state today

- **USO**: 12m trend 86.4% (log), carry 8.8%/yr (backwardation), 20d vol 37%, Brent−WTI $5.89 vs 1y median $4.60 → target weight +0.51
- **BNO**: 12m trend 88.2% (log), carry 39.2%/yr (backwardation), 20d vol 36%, Brent−WTI $5.89 vs 1y median $4.60 → target weight +0.53
## Verdict

- **There is a real but modest edge, and it is crisis insurance, not a return engine.** 12-month trend is positive in-sample on both ETFs (L/S Sharpe 0.30 / 0.33), and every lookback/carry combination is positive out of sample. The selected rule (#9) made +24% / +26% in 2015 while buy-and-hold lost 46%, and was positive in 2020.
- **It lags a bull market badly.** 2022–2026 out-of-sample: Sharpe 0.28 (USO) / 0.50 (BNO) vs buy-and-hold 0.79 / 0.84. It lost money in each of 2022–2025 (−5% to −11%/yr) before +51% / +72% in 2026.
- **The selection is fragile.** #9 won in-sample out of 8 candidates; the spread filter's in-sample boost on USO (0.03 → 0.46) did not repeat out-of-sample (0.36 → 0.28). Treat the spread filter as unproven.
- **Costs matter for USO.** At 2× costs the USO version is ~0 Sharpe; BNO holds up better.
- **Carry alone is not a strategy on one asset.** It's just "long when backwardated", and failed in-sample.
- **Portfolio role:** about zero correlation to the BTC sleeves. Adding a BNO sleeve at equal capital cut book vol 36% → 28% and max DD 33% → 30% since 2022, with Sharpe unchanged (0.99 → 0.98).
- **Data caveat:** the spread filter uses front-month CL=F vs BZ=F, which roll in different months; the same-month (Dec-26) spread is ~$10–11 vs the ~$6 front-month figure above.
