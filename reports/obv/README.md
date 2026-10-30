# BTC OBV momentum: improvement research

Generated 2026-10-30. Periods: DEV 2015-06-01→2020-05-31, VAL 2020-06-01→2025-11-04, HOLDOUT 2025-11-05→today.

Rule: keep a change only if Sharpe improves ≥0.05 in BOTH DEV and VAL (also at 2× costs) and max DD is not >5 pp worse. Dropping the OBV leg (a simplification) is kept if within 0.05.

## Summary

|                                             |   DEV Sharpe |   VAL Sharpe |   HOLDOUT Sharpe |   DEV Sharpe 2×cost |   DEV MaxDD |   DEV CAGR |   VAL Sharpe 2×cost |   VAL MaxDD |   VAL CAGR |   Trades/Yr (VAL) |   HOLDOUT Return % | Verdict   |
|:--------------------------------------------|-------------:|-------------:|-----------------:|--------------------:|------------:|-----------:|--------------------:|------------:|-----------:|------------------:|-------------------:|:----------|
| 0 Baseline (original)                       |         0.46 |         1.32 |             1.63 |                0.41 |      -99.24 |     -19.85 |                1.28 |      -37.91 |      74.07 |             10.14 |              61.81 | baseline  |
| 1 Drop OBV leg (pure momentum)              |         0.46 |         1.34 |             1.23 |                0.41 |      -99.24 |     -19.75 |                1.30 |      -37.91 |      76.03 |             10.87 |              42.86 | KEEP      |
| 2 OBV above its 20d mean                    |         0.48 |         1.36 |             1.24 |                0.43 |      -99.24 |     -18.10 |                1.33 |      -37.91 |      77.86 |              7.92 |              42.02 | revert    |
| 3 Symmetric volume confirmation             |         0.47 |         1.32 |             1.45 |                0.42 |      -99.24 |     -19.34 |                1.29 |      -40.22 |      74.71 |              9.95 |              52.73 | revert    |
| 4 Long-only                                 |         1.35 |         1.41 |             0.73 |                1.33 |      -66.75 |      92.03 |                1.39 |      -44.76 |      69.41 |              5.16 |              13.95 | revert    |
| 5 Momentum must hold 3 days                 |         0.76 |         0.99 |             0.30 |                0.75 |      -96.26 |      29.58 |                0.97 |      -45.52 |      47.28 |              5.71 |               4.36 | revert    |
| 6 Multi-horizon momentum (20/40/75/150/300) |         1.31 |         1.17 |             0.86 |                1.26 |      -56.29 |      76.73 |                1.09 |      -35.04 |      49.32 |             12.72 |              23.77 | revert    |
| 7 Vol target 60% (cap 1x)                   |         1.11 |         1.18 |             0.81 |                1.07 |      -74.95 |      62.06 |                1.14 |      -42.34 |      60.64 |             10.87 |              26.37 | revert    |
| 8 2% stop-loss                              |         1.33 |         1.43 |             1.56 |                1.25 |      -72.95 |      93.64 |                1.36 |      -34.09 |      81.97 |             18.61 |              55.96 | KEEP      |

## DEV detail (1× costs)

|                                             |   CAGR % |   Sharpe |   Max DD % |   Calmar |   Trades/Yr |   Win Rate % |   Exposure % |
|:--------------------------------------------|---------:|---------:|-----------:|---------:|------------:|-------------:|-------------:|
| 0 Baseline (original)                       |   -19.85 |     0.46 |     -99.24 |    -0.2  |        10.6 |        41.51 |       100    |
| 1 Drop OBV leg (pure momentum)              |   -19.75 |     0.46 |     -99.24 |    -0.2  |        11.4 |        38.6  |       100    |
| 2 OBV above its 20d mean                    |   -18.1  |     0.48 |     -99.24 |    -0.18 |        10.6 |        39.62 |       100    |
| 3 Symmetric volume confirmation             |   -19.34 |     0.47 |     -99.24 |    -0.19 |        10.4 |        42.31 |        98.8  |
| 4 Long-only                                 |    92.03 |     1.35 |     -66.75 |     1.38 |         5.2 |        53.85 |        60.26 |
| 5 Momentum must hold 3 days                 |    29.58 |     0.76 |     -96.26 |     0.31 |         5.4 |        55.56 |       100    |
| 6 Multi-horizon momentum (20/40/75/150/300) |    76.73 |     1.31 |     -56.29 |     1.36 |        11.6 |        31.03 |        97.59 |
| 7 Vol target 60% (cap 1x)                   |    62.06 |     1.11 |     -74.95 |     0.83 |        11.4 |        36.84 |       100    |
| 8 2% stop-loss                              |    93.64 |     1.33 |     -72.95 |     1.28 |        27.8 |        17.27 |        92.99 |

## VAL detail (1× costs)

|                                             |   CAGR % |   Sharpe |   Max DD % |   Calmar |   Trades/Yr |   Win Rate % |   Exposure % |
|:--------------------------------------------|---------:|---------:|-----------:|---------:|------------:|-------------:|-------------:|
| 0 Baseline (original)                       |    74.07 |     1.32 |     -37.91 |     1.95 |       10.14 |        43.64 |        99.95 |
| 1 Drop OBV leg (pure momentum)              |    76.03 |     1.34 |     -37.91 |     2.01 |       10.87 |        42.37 |       100    |
| 2 OBV above its 20d mean                    |    77.86 |     1.36 |     -37.91 |     2.05 |        7.92 |        44.19 |       100    |
| 3 Symmetric volume confirmation             |    74.71 |     1.32 |     -40.22 |     1.86 |        9.95 |        42.59 |        99.24 |
| 4 Long-only                                 |    69.41 |     1.41 |     -44.76 |     1.55 |        5.16 |        46.43 |        62.18 |
| 5 Momentum must hold 3 days                 |    47.28 |     0.99 |     -45.52 |     1.04 |        5.71 |        35.48 |        99.95 |
| 6 Multi-horizon momentum (20/40/75/150/300) |    49.32 |     1.17 |     -35.04 |     1.41 |       12.72 |        34.78 |       100    |
| 7 Vol target 60% (cap 1x)                   |    60.64 |     1.18 |     -42.34 |     1.43 |       10.87 |        42.37 |       100    |
| 8 2% stop-loss                              |    81.97 |     1.43 |     -34.09 |     2.4  |       18.61 |        28.71 |        95.21 |

## HOLDOUT detail (1× costs)

|                                             |   CAGR % |   Sharpe |   Max DD % |   Calmar |   Trades/Yr |   Win Rate % |   Exposure % |
|:--------------------------------------------|---------:|---------:|-----------:|---------:|------------:|-------------:|-------------:|
| 0 Baseline (original)                       |    63.18 |     1.63 |     -15.47 |     4.08 |        5.09 |        40    |       100    |
| 1 Drop OBV leg (pure momentum)              |    43.75 |     1.23 |     -18.23 |     2.4  |        7.12 |        42.86 |       100    |
| 2 OBV above its 20d mean                    |    42.89 |     1.24 |     -15.47 |     2.77 |        5.09 |        40    |       100    |
| 3 Symmetric volume confirmation             |    53.86 |     1.45 |     -15.47 |     3.48 |        6.1  |        50    |        99.44 |
| 4 Long-only                                 |    14.2  |     0.73 |     -10.67 |     1.33 |        2.03 |         0    |        31.94 |
| 5 Momentum must hold 3 days                 |     4.44 |     0.3  |     -33.88 |     0.13 |        3.05 |        33.33 |       100    |
| 6 Multi-horizon momentum (20/40/75/150/300) |    24.24 |     0.86 |     -21.2  |     1.14 |       16.28 |        43.75 |       100    |
| 7 Vol target 60% (cap 1x)                   |    26.89 |     0.81 |     -27.67 |     0.97 |        7.12 |        42.86 |       100    |
| 8 2% stop-loss                              |    57.17 |     1.56 |     -15.88 |     3.6  |        8.14 |        25    |        97.78 |

## Is mom_period = 75 special? (baseline logic, Sharpe by lookback)

|     |   DEV |   VAL |   HOLDOUT |
|----:|------:|------:|----------:|
|  20 |  1.53 |  0.78 |      0.39 |
|  30 |  1.35 |  0.78 |      0.31 |
|  45 |  0.88 |  0.73 |      1.48 |
|  60 |  1.33 |  0.97 |      0.79 |
|  75 |  0.46 |  1.32 |      1.63 |
|  90 |  0.41 |  0.99 |     -0.37 |
| 120 |  1.32 |  0.84 |      0.15 |
| 150 |  1.34 |  0.23 |      1.19 |
| 200 |  1.1  |  0.71 |      0.24 |
| 250 |  1.29 |  1.52 |     -0.73 |

## Combination of survivors ['1 Drop OBV leg (pure momentum)', '8 2% stop-loss']: revert

|         |   CAGR % |   Sharpe |   Max DD % |   Calmar |   Trades/Yr |   Win Rate % |   Exposure % |
|:--------|---------:|---------:|-----------:|---------:|------------:|-------------:|-------------:|
| DEV     |    91.27 |     1.31 |     -72.95 |     1.25 |       31.2  |        18.59 |        93.92 |
| VAL     |    79.16 |     1.4  |     -34.09 |     2.32 |       20.27 |        29.09 |        96.47 |
| HOLDOUT |    42.11 |     1.23 |     -17.99 |     2.34 |       12.21 |        33.33 |        98.06 |

## Survivors

1 Drop OBV leg (pure momentum), 8 2% stop-loss

## Decision (2026-10-30)

**Kept: a 2% stop-loss (now the default, `OBVMomentum(sl_stop=0.02)`). Everything else is reverted.**

- **The finding that matters:** with the original logic, 2015–2020 (before the window the strategy was built on) has a **−99% max drawdown**. In the March 2020 crash it was long from $8.9k to $5.0k (−44%), then went 100% short at the COVID low on 13 Mar and held while BTC doubled (−98% on that trade). The original backtest started in June 2020, just after.
- **The stop fixes it, and not by luck:** any stop from 1% to 8% lifts DEV Sharpe from 0.46 to 1.1–1.5. 2–3% is best and VAL is unchanged or better (1.32 → 1.43 at 2%). Holdout is a wash (1.63 → 1.55).
- **Dropping the OBV leg** passed as a simplification on its own, but combined with the stop it was worse than the stop alone, so the OBV leg stays.
- **Reverted:** OBV vs 20d mean, symmetric volume confirmation, 3-day confirmation, multi-horizon momentum, vol targeting. Long-only had better Sharpe but failed the drawdown rule in VAL (−45% vs −38%).
- **`mom_period = 75` looks fitted to 2020–25:** it's the worst lookback tested on 2015–20 (Sharpe 0.46 vs 0.9–1.5 for the others) and among the best on 2020–25. Results since 2025-11 jump around a lot by lookback. Treat the strategy's headline numbers as optimistic. A multi-lookback blend is the usual cure, but it didn't pass the rule here.
- **Remaining risk:** even with the stop, DEV max DD is −73% (all-in, always in the market, 2018 bear-market whipsaws).
