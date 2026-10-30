# Baseline re-run of the original strategies

Generated 2026-10-30 12:54. Capital $100k per sleeve. Out-of-sample window starts 2025-11-05.

## BTC AC Momentum  (from 2019-01-07)

|                               |   Total Return % |   CAGR % |   Sharpe |   Max DD % |   Calmar |   Trades |   Win Rate % |   Exposure % |     Costs Paid |   Benchmark Return % |   Benchmark Sharpe |
|:------------------------------|-----------------:|---------:|---------:|-----------:|---------:|---------:|-------------:|-------------:|---------------:|---------------------:|-------------------:|
| A Legacy                      |          4762    |    64.42 |     1.2  |     -40.4  |     1.59 |      182 |        32.97 |        96.29 |    0           |              1819    |               0.93 |
| B +Next-bar open              |          3577    |    58.64 |     1.12 |     -47.02 |     1.25 |      203 |        33    |        95.8  |    0           |              1819    |               0.93 |
| C +Intrabar stops             |         10111    |    80.8  |     1.41 |     -37.81 |     2.14 |      287 |        22.3  |        92.54 |    0           |              1819    |               0.93 |
| D +Costs (FIXED)              |          5654    |    68    |     1.26 |     -41.32 |     1.65 |      287 |        22.3  |        92.54 |    1.43738e+06 |              1819    |               0.93 |
| E Fixed, OOS since 2025-11-05 |            36.21 |    36.94 |     1.07 |     -20.62 |     1.79 |       32 |        21.88 |        93.89 | 7468           |               -25.65 |              -0.46 |

## BTC OBV Momentum  (from 2020-06-01)

|                               |   Total Return % |   CAGR % |   Sharpe |   Max DD % |   Calmar |   Trades |   Win Rate % |   Exposure % |   Costs Paid |   Benchmark Return % |   Benchmark Sharpe |
|:------------------------------|-----------------:|---------:|---------:|-----------:|---------:|---------:|-------------:|-------------:|-------------:|---------------------:|-------------------:|
| A Legacy                      |          3383    |    73.97 |     1.36 |     -37.47 |     1.97 |       60 |        43.33 |       100    |            0 |               659.76 |               0.84 |
| B +Next-bar open              |          3372    |    73.89 |     1.36 |     -37.49 |     1.97 |       60 |        43.33 |        99.96 |            0 |               659.76 |               0.84 |
| C +Intrabar stops             |          3372    |    73.89 |     1.36 |     -37.49 |     1.97 |       60 |        43.33 |        99.96 |            0 |               659.76 |               0.84 |
| D +Costs (FIXED)              |          2979    |    70.66 |     1.32 |     -37.91 |     1.86 |       60 |        43.33 |        99.96 |       125863 |               659.76 |               0.84 |
| E Fixed, OOS since 2025-11-05 |            61.47 |    62.82 |     1.63 |     -15.47 |     4.06 |        5 |        40    |       100    |         1254 |               -25.65 |              -0.46 |

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
| BTC AC Momentum    |             1429 |    53.01 | 1.13     |     -41.32 | 1.28     |      241 | 21.58        | 92.36        |       410524 |               659.76 |               0.84 |
| BTC OBV Momentum   |             2979 |    70.66 | 1.32     |     -37.91 | 1.86     |       60 | 43.33        | 99.96        |       125863 |               659.76 |               0.84 |
| Oil Corr Reversion |                0 |     0    | –        |       0    | –        |        0 | –            | 0.00         |            0 |               194.12 |               0.63 |
| BOOK               |             1469 |    53.62 | 1.31     |     -28.19 | 1.90     |      301 | 25.91        | –            |       536387 |               504.55 |               0.84 |

Sleeve return correlation:

|                    |   BTC AC Momentum |   BTC OBV Momentum |   Oil Corr Reversion |
|:-------------------|------------------:|-------------------:|---------------------:|
| BTC AC Momentum    |              1    |               0.48 |                  nan |
| BTC OBV Momentum   |              0.48 |               1    |                  nan |
| Oil Corr Reversion |            nan    |             nan    |                  nan |

P&L contribution (% of book):

|                    |      % |
|:-------------------|-------:|
| BTC AC Momentum    | 511.38 |
| BTC OBV Momentum   | 993.12 |
| Oil Corr Reversion |   0    |

## Combined book (OOS, from 2025-11-05, equal weight, $300k)

|                    |   Total Return % |   CAGR % | Sharpe   |   Max DD % | Calmar   |   Trades | Win Rate %   | Exposure %   |   Costs Paid |   Benchmark Return % |   Benchmark Sharpe |
|:-------------------|-----------------:|---------:|:---------|-----------:|:---------|---------:|:-------------|:-------------|-------------:|---------------------:|-------------------:|
| BTC AC Momentum    |            36.21 |    36.94 | 1.07     |     -20.62 | 1.79     |       32 | 21.88        | 93.89        |         7468 |               -25.65 |              -0.46 |
| BTC OBV Momentum   |            61.47 |    62.82 | 1.63     |     -15.47 | 4.06     |        5 | 40.00        | 100.00       |         1254 |               -25.65 |              -0.46 |
| Oil Corr Reversion |             0    |     0    | –        |       0    | –        |        0 | –            | 0.00         |            0 |                76.17 |               1.34 |
| BOOK               |            32.3  |    32.95 | 1.48     |      -7.86 | 4.19     |       37 | 24.32        | –            |         8721 |                 8.29 |               0.41 |

Sleeve return correlation:

|                    |   BTC AC Momentum |   BTC OBV Momentum |   Oil Corr Reversion |
|:-------------------|------------------:|-------------------:|---------------------:|
| BTC AC Momentum    |              1    |               0.44 |                  nan |
| BTC OBV Momentum   |              0.44 |               1    |                  nan |
| Oil Corr Reversion |            nan    |             nan    |                  nan |

P&L contribution (% of book):

|                    |    % |
|:-------------------|-----:|
| BTC AC Momentum    | 11.8 |
| BTC OBV Momentum   | 20   |
| Oil Corr Reversion |  0   |

## Original code, run unchanged on today's data

|                                |   Total Return % | Sharpe   | Max DD %   | Win Rate %   | Trades   |
|:-------------------------------|-----------------:|:---------|:-----------|:-------------|:---------|
| BTC AC Momentum                |          5772    | 1.25     | -40.40     | 33.90        | 178.00   |
| BTC OBV Momentum               |          3041    | 1.36     | -37.66     | 43.10        | 59.00    |
| Oil Corr Reversion             |           166.71 | 0.71     | -18.01     | 100.00       | 1.00     |
| OLD BOOK (as reported)         |          2334    | 0.86     | -28.47     | 69.25        | 59.75    |
| OLD BOOK (plot start value)    |           300    | –        | –          | –            | –        |
| OLD BOOK (true sum of columns) |          2334    | –        | -29.50     | –            | –        |
