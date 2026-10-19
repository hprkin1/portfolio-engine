# Baseline re-run of the original strategies

Generated 2026-10-19 11:41. Capital $100k per sleeve. Out-of-sample window starts 2025-11-05.

## BTC AC Momentum  (from 2019-01-07)

|                               |   Total Return % |   CAGR % |   Sharpe |   Max DD % |   Calmar |   Trades |   Win Rate % |   Exposure % |   Costs Paid |   Benchmark Return % |   Benchmark Sharpe |
|:------------------------------|-----------------:|---------:|---------:|-----------:|---------:|---------:|-------------:|-------------:|-------------:|---------------------:|-------------------:|
| A Legacy                      |          4633    |    64.17 |     1.19 |     -40.4  |     1.59 |      181 |        33.15 |        96.31 |            0 |              1943    |               0.95 |
| B +Next-bar open              |          1697    |    44.96 |     0.95 |     -56.29 |     0.8  |      192 |        35.42 |        95.92 |            0 |              1943    |               0.95 |
| C +Intrabar stops             |          2389    |    51.15 |     1.05 |     -53.5  |     0.96 |      272 |        29.78 |        92.72 |            0 |              1943    |               0.95 |
| D +Costs (FIXED)              |          1503    |    42.85 |     0.94 |     -55.25 |     0.78 |      272 |        28.68 |        92.72 |       546556 |              1943    |               0.95 |
| E Fixed, OOS since 2025-11-05 |            16.19 |    17.06 |     0.61 |     -24.09 |     0.71 |       30 |        36.67 |        94.27 |         6820 |               -20.84 |              -0.33 |

## BTC OBV Momentum  (from 2020-06-01)

|                               |   Total Return % |   CAGR % |   Sharpe |   Max DD % |   Calmar |   Trades |   Win Rate % |   Exposure % |   Costs Paid |   Benchmark Return % |   Benchmark Sharpe |
|:------------------------------|-----------------:|---------:|---------:|-----------:|---------:|---------:|-------------:|-------------:|-------------:|---------------------:|-------------------:|
| A Legacy                      |          3608    |    76.14 |     1.38 |     -37.47 |     2.03 |       60 |        43.33 |       100    |            0 |               708.87 |               0.86 |
| B +Next-bar open              |          3597    |    76.06 |     1.38 |     -37.49 |     2.03 |       60 |        43.33 |        99.96 |            0 |               708.87 |               0.86 |
| C +Intrabar stops             |          3597    |    76.06 |     1.38 |     -37.49 |     2.03 |       60 |        43.33 |        99.96 |            0 |               708.87 |               0.86 |
| D +Costs (FIXED)              |          3178    |    72.78 |     1.34 |     -37.91 |     1.92 |       60 |        43.33 |        99.96 |       125863 |               708.87 |               0.86 |
| E Fixed, OOS since 2025-11-05 |            71.91 |    76.59 |     1.87 |     -15.47 |     4.95 |        5 |        40    |       100    |         1254 |               -20.84 |              -0.33 |

## Oil Corr Reversion  (from 2016-01-01)

|                               |   Total Return % |   CAGR % | Sharpe   |   Max DD % | Calmar   |   Trades | Win Rate %   |   Exposure % |   Costs Paid |   Benchmark Return % |   Benchmark Sharpe |
|:------------------------------|-----------------:|---------:|:---------|-----------:|:---------|---------:|:-------------|-------------:|-------------:|---------------------:|-------------------:|
| A Legacy                      |                0 |        0 | –        |          0 | –        |        0 | –            |            0 |            0 |               179.74 |               0.44 |
| B +Next-bar open              |                0 |        0 | –        |          0 | –        |        0 | –            |            0 |            0 |               179.74 |               0.44 |
| C +Intrabar stops             |                0 |        0 | –        |          0 | –        |        0 | –            |            0 |            0 |               179.74 |               0.44 |
| D +Costs (FIXED)              |                0 |        0 | –        |          0 | –        |        0 | –            |            0 |            0 |               179.74 |               0.44 |
| E Fixed, OOS since 2025-11-05 |                0 |        0 | –        |          0 | –        |        0 | –            |            0 |            0 |                68.04 |               1.28 |

## Combined book (full, from 2020-06-01, equal weight, $300k)

|                    |   Total Return % |   CAGR % | Sharpe   |   Max DD % | Calmar   |   Trades | Win Rate %   | Exposure %   |   Costs Paid |   Benchmark Return % |   Benchmark Sharpe |
|:-------------------|-----------------:|---------:|:---------|-----------:|:---------|---------:|:-------------|:-------------|-------------:|---------------------:|-------------------:|
| BTC AC Momentum    |            495.3 |    32.25 | 0.82     |     -50.03 | 0.64     |      235 | 27.23        | 92.24        |       216126 |               708.87 |               0.86 |
| BTC OBV Momentum   |           3178   |    72.78 | 1.34     |     -37.91 | 1.92     |       60 | 43.33        | 99.96        |       125863 |               708.87 |               0.86 |
| Oil Corr Reversion |              0   |     0    | –        |       0    | –        |        0 | –            | 0.00         |            0 |               180.54 |               0.61 |
| BOOK               |           1207   |    49.6  | 1.24     |     -31.25 | 1.59     |      295 | 30.51        | –            |       341988 |               532.76 |               0.86 |

Sleeve return correlation:

|                    |   BTC AC Momentum |   BTC OBV Momentum |   Oil Corr Reversion |
|:-------------------|------------------:|-------------------:|---------------------:|
| BTC AC Momentum    |              1    |               0.44 |                  nan |
| BTC OBV Momentum   |              0.44 |               1    |                  nan |
| Oil Corr Reversion |            nan    |             nan    |                  nan |

P&L contribution (% of book):

|                    |       % |
|:-------------------|--------:|
| BTC AC Momentum    |  177.2  |
| BTC OBV Momentum   | 1059.46 |
| Oil Corr Reversion |    0    |

## Combined book (OOS, from 2025-11-05, equal weight, $300k)

|                    |   Total Return % |   CAGR % | Sharpe   |   Max DD % | Calmar   |   Trades | Win Rate %   | Exposure %   |   Costs Paid |   Benchmark Return % |   Benchmark Sharpe |
|:-------------------|-----------------:|---------:|:---------|-----------:|:---------|---------:|:-------------|:-------------|-------------:|---------------------:|-------------------:|
| BTC AC Momentum    |            16.19 |    17.06 | 0.61     |     -24.09 | 0.71     |       30 | 36.67        | 94.27        |         6820 |               -20.84 |              -0.33 |
| BTC OBV Momentum   |            71.91 |    76.59 | 1.87     |     -15.47 | 4.95     |        5 | 40.00        | 100.00       |         1254 |               -20.84 |              -0.33 |
| Oil Corr Reversion |             0    |     0    | –        |       0    | –        |        0 | –            | 0.00         |            0 |                68.04 |               1.28 |
| BOOK               |            29.13 |    30.78 | 1.38     |      -8.4  | 3.66     |       35 | 37.14        | –            |         8074 |                 8.79 |               0.43 |

Sleeve return correlation:

|                    |   BTC AC Momentum |   BTC OBV Momentum |   Oil Corr Reversion |
|:-------------------|------------------:|-------------------:|---------------------:|
| BTC AC Momentum    |              1    |               0.47 |                  nan |
| BTC OBV Momentum   |              0.47 |               1    |                  nan |
| Oil Corr Reversion |            nan    |             nan    |                  nan |

P&L contribution (% of book):

|                    |     % |
|:-------------------|------:|
| BTC AC Momentum    |  5.27 |
| BTC OBV Momentum   | 23.4  |
| Oil Corr Reversion |  0    |

## Original code, run unchanged on today's data

|                                |   Total Return % | Sharpe   | Max DD %   | Win Rate %   | Trades   |
|:-------------------------------|-----------------:|:---------|:-----------|:-------------|:---------|
| BTC AC Momentum                |          5616    | 1.25     | -40.40     | 34.09        | 177.00   |
| BTC OBV Momentum               |          3246    | 1.38     | -37.66     | 43.10        | 59.00    |
| Oil Corr Reversion             |           166.71 | 0.72     | -18.01     | 100.00       | 1.00     |
| OLD BOOK (as reported)         |          2349    | 0.87     | -28.47     | 69.30        | 59.50    |
| OLD BOOK (plot start value)    |           300    | –        | –          | –            | –        |
| OLD BOOK (true sum of columns) |          2349    | –        | -29.50     | –            | –        |
