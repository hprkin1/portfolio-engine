# portfolio-engine

Multi-strategy backtesting engine. It replaces `Portfolio/` in
[Algorithmic-Trading-Repository](https://github.com/hprkin1/Algorithmic-Trading-Repository).
It's the base for strategy improvement and, later, a backtest + paper-trading dashboard.

## Layout

```
engine/
  data.py        yfinance loader, parquet cache, cleaning (drops non-positive futures prints)
  costs.py       fee + slippage presets per asset class (taker-conservative)
  strategy.py    BaseStrategy contract + Signals; strategies are pure signal logic
  portfolio.py   backtest_strategy() for one sleeve, PortfolioManager for a weighted book
  metrics.py     metrics from the equity curve (correct annualisation, no column averaging)
strategies/      ac_momentum.py, obv_momentum.py, corr_reversion.py  (faithful ports)
scripts/run_baseline.py   re-baseline: shows the effect of each fix, plus out-of-sample
tests/           offline tests: no look-ahead, next-bar fills, costs, book accounting
reports/         baseline.md, CSVs, equity chart
```

## The timing contract

A strategy's signal on bar *t* may use data up to the **close of bar t**.
The engine fills it on bar *t+1* (open by default). Strategies never shift
their own signals. `tests/test_engine.py::test_no_lookahead` checks this for
every strategy in `strategies.REGISTRY`.

## Quick start

```bash
pip install -r requirements.txt
python scripts/run_baseline.py                 # writes reports/baseline.md
python -m pytest -q
```

```python
from engine import backtest_strategy, PortfolioManager, Sleeve, REALISTIC, LEGACY
from strategies import ACMomentum, OBVMomentum

r = backtest_strategy(OBVMomentum(mom_period=60), capital=100_000, start="2020-06-01")
r.metrics, r.equity, r.positions

book = PortfolioManager([Sleeve(ACMomentum(), 1), Sleeve(OBVMomentum(), 2)],
                        capital=300_000, start="2020-06-01").run()
book.metrics_table(); book.contribution(); book.correlation()
```

`ExecConfig(execution="next_open"|"next_close"|"same_close", intrabar_stops=True, costs="auto")`.
`LEGACY` reproduces the old assumptions so you can compare.

## What was fixed (vs `Portfolio/`)

| # | Old behaviour | Fix |
|---|---|---|
| 1 | Book = one vbt portfolio, no `group_by`. Every column got the full init cash, so $1.2M was really deployed against a stated $300k | Each strategy is a sleeve with `weight × capital`; sleeves combine at equity level |
| 2 | `stats()` averaged columns (Sharpe, DD, win rate, "48.25 trades") | Metrics computed on the real book equity curve |
| 3 | `plot()` started at +300% | Uses `sleeve_equity()` / book equity |
| 4 | Two BTC strategies → duplicate `BTC-USD` columns | Unique sleeve names enforced |
| 5 | Signal on the close, filled at the same close | Filled at next bar's open |
| 6 | 2% stop checked against close only | Stops checked against High/Low |
| 7 | Zero fees on BTC runs and the book | Taker fee + slippage per asset class |
| 8 | CL=F −$37 print fed into returns | Non-positive bars dropped and logged |
| 9 | Crypto and futures calendars mixed in one frame | Each sleeve trades its own calendar |
| 10 | Wrong stat keys → annual return / trades = None; yfinance MultiIndex leaked | Fixed; columns flattened |
| 11 | Re-downloaded BTC per strategy, with sleeps | Parquet cache |

## Not modelled yet

- Perp funding (matters for always-in-market long/short BTC)
- Futures roll yield/cost on continuous `=F` contracts
- Position sizing other than 1× sleeve notional (no vol targeting yet)
