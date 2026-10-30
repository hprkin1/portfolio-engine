# Baseline re-run of the original strategies

Generated 2026-10-30 16:23. Capital $100k per sleeve. Out-of-sample window starts 2025-11-05.

## BTC AC Momentum  (from 2019-01-07)

|                               |   Total Return % |   CAGR % |   Sharpe |   Max DD % |   Calmar |   Trades |   Win Rate % |   Exposure % |     Costs Paid |   Benchmark Return % |   Benchmark Sharpe |
|:------------------------------|-----------------:|---------:|---------:|-----------:|---------:|---------:|-------------:|-------------:|---------------:|---------------------:|-------------------:|
| A Legacy                      |          4756    |    64.39 |     1.2  |     -40.4  |     1.59 |      182 |        32.97 |        96.29 |    0           |              1821    |               0.93 |
| B +Next-bar open              |          3573    |    58.62 |     1.12 |     -47.02 |     1.25 |      203 |        33    |        95.8  |    0           |              1821    |               0.93 |
| C +Intrabar stops             |         10101    |    80.78 |     1.41 |     -37.81 |     2.14 |      287 |        22.3  |        92.54 |    0           |              1821    |               0.93 |
| D +Costs (FIXED)              |          5648    |    67.98 |     1.26 |     -41.32 |     1.65 |      287 |        22.3  |        92.54 |    1.43738e+06 |              1821    |               0.93 |
| E Fixed, OOS since 2025-11-05 |            36.07 |    36.8  |     1.07 |     -20.62 |     1.79 |       32 |        21.88 |        93.89 | 7468           |               -25.56 |              -0.46 |

## BTC OBV Momentum  (from 2020-06-01)

|                               |   Total Return % |   CAGR % |   Sharpe |   Max DD % |   Calmar |   Trades |   Win Rate % |   Exposure % |   Costs Paid |   Benchmark Return % |   Benchmark Sharpe |
|:------------------------------|-----------------:|---------:|---------:|-----------:|---------:|---------:|-------------:|-------------:|-------------:|---------------------:|-------------------:|
| A Legacy                      |          3387    |    74    |     1.36 |     -37.47 |     1.98 |       60 |        43.33 |       100    |            0 |               660.65 |               0.84 |
| B +Next-bar open              |          3376    |    73.92 |     1.36 |     -37.49 |     1.97 |       60 |        43.33 |        99.96 |            0 |               660.65 |               0.84 |
| C +Intrabar stops             |          3376    |    73.92 |     1.36 |     -37.49 |     1.97 |       60 |        43.33 |        99.96 |            0 |               660.65 |               0.84 |
| D +Costs (FIXED)              |          2983    |    70.69 |     1.32 |     -37.91 |     1.86 |       60 |        43.33 |        99.96 |       125863 |               660.65 |               0.84 |
| E Fixed, OOS since 2025-11-05 |            61.66 |    63.02 |     1.63 |     -15.47 |     4.07 |        5 |        40    |       100    |         1254 |               -25.56 |              -0.46 |

## Oil Corr Reversion  (from 2016-01-01)

|                               |   Total Return % |   CAGR % | Sharpe   |   Max DD % | Calmar   |   Trades | Win Rate %   |   Exposure % |   Costs Paid |   Benchmark Return % |   Benchmark Sharpe |
|:------------------------------|-----------------:|---------:|:---------|-----------:|:---------|---------:|:-------------|-------------:|-------------:|---------------------:|-------------------:|
| A Legacy                      |                0 |        0 | –        |          0 | –        |        0 | –            |            0 |            0 |               193.22 |               0.45 |
| B +Next-bar open              |                0 |        0 | –        |          0 | –        |        0 | –            |            0 |            0 |               193.22 |               0.45 |
| C +Intrabar stops             |                0 |        0 | –        |          0 | –        |        0 | –            |            0 |            0 |               193.22 |               0.45 |
| D +Costs (FIXED)              |                0 |        0 | –        |          0 | –        |        0 | –            |            0 |            0 |               193.22 |               0.45 |
| E Fixed, OOS since 2025-11-05 |                0 |        0 | –        |          0 | –        |        0 | –            |            0 |            0 |                76.17 |               1.34 |

## Combined book (full, from 2020-06-01, equal weight, $300k)

|                    |   Total Return % |   CAGR % | Sharpe   |   Max DD % | Calmar   |   Trades | Win Rate %   | Exposure %   |   Costs Paid |   Benchmark Return % |   Benchmark Sharpe |
|:-------------------|-----------------:|---------:|:---------|-----------:|:---------|---------:|:-------------|:-------------|-------------:|---------------------:|-------------------:|
| BTC AC Momentum    |             1428 |    52.99 | 1.12     |     -41.32 | 1.28     |      241 | 21.58        | 92.36        |       410524 |               660.65 |               0.84 |
| BTC OBV Momentum   |             2983 |    70.69 | 1.32     |     -37.91 | 1.86     |       60 | 43.33        | 99.96        |       125863 |               660.65 |               0.84 |
| Oil Corr Reversion |                0 |     0    | –        |       0    | –        |        0 | –            | 0.00         |            0 |               194.12 |               0.63 |
| BOOK               |             1469 |    53.63 | 1.31     |     -28.19 | 1.90     |      301 | 25.91        | –            |       536387 |               505.14 |               0.84 |

Sleeve return correlation:

|                    |   BTC AC Momentum |   BTC OBV Momentum |   Oil Corr Reversion |
|:-------------------|------------------:|-------------------:|---------------------:|
| BTC AC Momentum    |              1    |               0.48 |                  nan |
| BTC OBV Momentum   |              0.48 |               1    |                  nan |
| Oil Corr Reversion |            nan    |             nan    |                  nan |

P&L contribution (% of book):

|                    |      % |
|:-------------------|-------:|
| BTC AC Momentum    | 510.83 |
| BTC OBV Momentum   | 994.32 |
| Oil Corr Reversion |   0    |

## Combined book (OOS, from 2025-11-05, equal weight, $300k)

|                    |   Total Return % |   CAGR % | Sharpe   |   Max DD % | Calmar   |   Trades | Win Rate %   | Exposure %   |   Costs Paid |   Benchmark Return % |   Benchmark Sharpe |
|:-------------------|-----------------:|---------:|:---------|-----------:|:---------|---------:|:-------------|:-------------|-------------:|---------------------:|-------------------:|
| BTC AC Momentum    |            36.07 |    36.8  | 1.07     |     -20.62 | 1.79     |       32 | 21.88        | 93.89        |         7468 |               -25.56 |              -0.46 |
| BTC OBV Momentum   |            61.66 |    63.02 | 1.63     |     -15.47 | 4.07     |        5 | 40.00        | 100.00       |         1254 |               -25.56 |              -0.46 |
| Oil Corr Reversion |             0    |     0    | –        |       0    | –        |        0 | –            | 0.00         |            0 |                76.17 |               1.34 |
| BOOK               |            32.32 |    32.96 | 1.48     |      -7.86 | 4.19     |       37 | 24.32        | –            |         8721 |                 8.35 |               0.41 |

Sleeve return correlation:

|                    |   BTC AC Momentum |   BTC OBV Momentum |   Oil Corr Reversion |
|:-------------------|------------------:|-------------------:|---------------------:|
| BTC AC Momentum    |              1    |               0.44 |                  nan |
| BTC OBV Momentum   |              0.44 |               1    |                  nan |
| Oil Corr Reversion |            nan    |             nan    |                  nan |

P&L contribution (% of book):

|                    |     % |
|:-------------------|------:|
| BTC AC Momentum    | 11.76 |
| BTC OBV Momentum   | 20.07 |
| Oil Corr Reversion |  0    |
