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
strategies/      ac_momentum.py, obv_momentum.py (BTC), oil_trend_carry.py (oil sleeve)
scripts/run_baseline.py   re-baseline: shows the effect of each fix, plus out-of-sample
scripts/research_*.py     OBV improvement, oil trend-carry and stabilisation research (reports/obv, reports/oil)
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

`ExecConfig(execution="next_open"|"next_close"|"same_close", intrabar_stops=True, costs="auto", rebalance_band=0.0)`.

Strategies can return **event signals** (entries/exits) or **target weights**
(`Signals(target=...)`, for position sizing / vol targeting; only traded when the
target moves by more than `rebalance_band`). `signal_symbols` are loaded for the
strategy to read but never traded (e.g. CL=F feeding a USO strategy).

Book weighting: `PortfolioManager(..., weighting="capital"|"inverse_vol", vol_lookback=252,
rebalance="ME", max_weight=None, vol_floor=0.05, transfer_cost=0.001)`. In `inverse_vol`,
`Sleeve.weight` is a risk budget and capital is re-split month-end by 1/trailing vol.
`LEGACY` reproduces the old assumptions so you can compare.

## Strategy status (2026-10-30)

| Strategy | Status |
|---|---|
| `OBVMomentum` (BTC) | Live candidate · 2% stop added (reports/obv) |
| `ACMomentum` (BTC) | Live candidate · 2% stop |
| `OilTrendCarry` (USO/BNO) | Live candidate · modest, crash-protection role (reports/oil) |

Failed and retired research (original WTI/Brent correlation, Brent–WTI spread, equity pairs v1 and v2,
multi-asset ETF trend) lives with its results in
[Algorithmic-Trading-Repository/Development/portfolio_engine_research](https://github.com/hprkin1/Algorithmic-Trading-Repository/tree/main/Development/portfolio_engine_research).

## Correction: stop-losses with next-open fills (2026-10-30)

The first version of this engine under-stated the BTC AC strategy (reported +1,503%, Sharpe 0.94;
corrected: +5,654%, Sharpe 1.26 from 2019). With next-open execution, vectorbt (1) measured the stop
from the entry bar's *close* instead of the fill price, and (2) evaluated the stop *before* the
open signal on the same bar, booking a full stop-loss and re-entering a day late on days the
signal flipped. Strategies with stops and `execution="next_open"` now run through
`engine/stopsim.py` (signals at the open → intraday stop from the fill price → mark at close).
It matches vectorbt exactly when there are no stops (tested). Strategies without stops were
never affected.

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
