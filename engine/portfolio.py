"""Backtesting a single strategy (a "sleeve") and a multi-strategy book.

Fixes vs the old Portfolio/Portfolio_Manager.py
------------------------------------------------
1. Each strategy is its own sleeve with its own capital (weight x book capital).
   The old code concatenated every strategy's prices into one vbt portfolio
   without group_by/cash_sharing, so EACH column got the full init cash, stats()
   silently averaged the columns, and plot() divided 4x the capital by 1x
   (curve started at +300%). Two BTC strategies also produced duplicate
   'BTC-USD' columns.
2. Signals are executed on the next bar (open by default). The old momentum
   strategies computed signals on the close and filled at that same close.
3. Stops are checked against intrabar High/Low (old code passed only Close, so
   a 2% stop could only trigger at the daily close).
4. Fees + slippage are charged (old BTC/combined runs used zero).
5. Each sleeve trades on its own calendar (crypto 7d, futures 5d); sleeves are
   only combined at the equity level, forward-filling closed-market days.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import vectorbt as vbt

from .costs import PRESETS, CostModel, costs_for
from .data import load_panel
from .metrics import compute_metrics, periods_per_year
from .strategy import BaseStrategy, Panel, Signals

EXECUTION_MODES = ("next_open", "next_close", "same_close")


@dataclass
class ExecConfig:
    execution: str = "next_open"        # "same_close" reproduces the old (look-ahead) behaviour
    intrabar_stops: bool = True         # check sl/tp against High/Low
    costs: CostModel | str = "auto"     # "auto" -> per asset class, or a preset name / CostModel

    def cost_model(self, symbols: list[str]) -> CostModel:
        if isinstance(self.costs, CostModel):
            return self.costs
        if self.costs == "auto":
            return costs_for(symbols)
        return PRESETS[self.costs]


LEGACY = ExecConfig(execution="same_close", intrabar_stops=False, costs="zero")
REALISTIC = ExecConfig()


@dataclass
class SleeveResult:
    name: str
    strategy: BaseStrategy
    capital: float
    equity: pd.Series
    benchmark: pd.Series
    portfolio: vbt.Portfolio
    signals: Signals
    indicators: pd.DataFrame
    positions: pd.DataFrame
    metrics: dict
    config: ExecConfig

    @property
    def returns(self) -> pd.Series:
        return self.equity.pct_change().fillna(0)


def _warmup_start(start: str, bars: int) -> str:
    return (pd.Timestamp(start) - pd.Timedelta(days=int(bars * 1.6) + 10)).strftime("%Y-%m-%d")


def backtest_strategy(strategy: BaseStrategy, capital: float = 100_000, start: str = "2019-01-01",
                      end: str | None = None, config: ExecConfig = REALISTIC,
                      panel: Panel | None = None) -> SleeveResult:
    if config.execution not in EXECUTION_MODES:
        raise ValueError(f"execution must be one of {EXECUTION_MODES}")
    syms = strategy.symbols
    if panel is None:
        panel = load_panel(syms, _warmup_start(start, strategy.WARMUP_BARS), end)

    ind, sig = strategy.run(panel)
    if config.execution != "same_close":
        sig = sig.shifted(1)

    # trim warm-up period only AFTER indicators/signals are computed
    keep = panel["Close"].index >= pd.Timestamp(start)
    p = {k: v.loc[keep] for k, v in panel.items()}
    sig = Signals(*(x.loc[keep] for x in (sig.entries, sig.exits, sig.short_entries, sig.short_exits)))

    costs = config.cost_model(syms)
    n = len(syms)
    kwargs = dict(
        close=p["Close"],
        entries=sig.entries, exits=sig.exits,
        short_entries=sig.short_entries, short_exits=sig.short_exits,
        price=p["Open"] if config.execution == "next_open" else p["Close"],
        fees=costs.fee, slippage=costs.slippage,
        init_cash=capital / n,      # each leg gets an equal slice of the sleeve
        cash_sharing=False,
        group_by=True if n > 1 else None,
        freq="1D",
    )
    if config.intrabar_stops:
        kwargs.update(open=p["Open"], high=p["High"], low=p["Low"])
    if strategy.sl_stop:
        kwargs["sl_stop"] = strategy.sl_stop
    if strategy.tp_stop:
        kwargs["tp_stop"] = strategy.tp_stop

    pf = vbt.Portfolio.from_signals(**kwargs)
    equity = pf.value()
    if isinstance(equity, pd.DataFrame):
        equity = equity.iloc[:, 0]
    equity = equity.rename(strategy.name)

    close = p["Close"]
    bench = (close / close.iloc[0]).mean(axis=1) * capital
    positions = pf.positions.records_readable if n == 1 else \
        vbt.Portfolio.from_signals(**{**kwargs, "group_by": None}).positions.records_readable
    av = pf.asset_value(group_by=False) if n > 1 else pf.asset_value()
    av = av.to_frame() if isinstance(av, pd.Series) else av
    exposure = float((av.abs().sum(axis=1) > 0).mean())
    fees_paid = float(np.nansum(pf.orders.records_readable["Fees"])) if pf.orders.count().sum() else 0.0
    # slippage is embedded in fill prices; estimate it from traded notional for reporting
    orders = pf.orders.records_readable
    if len(orders):
        fees_paid += float((orders["Size"] * orders["Price"]).sum() * costs.slippage / (1 + costs.slippage))

    metrics = compute_metrics(equity, positions=positions, ppy=periods_per_year(close.index),
                              fees_paid=fees_paid, exposure=exposure, benchmark=bench)
    return SleeveResult(strategy.name, strategy, capital, equity, bench.rename("Benchmark"), pf,
                        sig, ind, positions, metrics, config)


@dataclass
class Sleeve:
    strategy: BaseStrategy
    weight: float = 1.0
    start: str | None = None  # per-sleeve override


@dataclass
class BookResult:
    sleeves: dict[str, SleeveResult]
    equity: pd.Series
    metrics: dict
    capital: float
    weights: dict[str, float] = field(default_factory=dict)

    def sleeve_equity(self) -> pd.DataFrame:
        idx = self.equity.index
        out = {}
        for name, r in self.sleeves.items():
            out[name] = r.equity.reindex(idx).ffill().fillna(r.capital)
        return pd.DataFrame(out)

    def contribution(self) -> pd.Series:
        """P&L contribution of each sleeve as % of total book capital."""
        se = self.sleeve_equity()
        return 100 * (se.iloc[-1] - se.iloc[0]) / self.capital

    def correlation(self) -> pd.DataFrame:
        return self.sleeve_equity().pct_change().corr()

    def metrics_table(self) -> pd.DataFrame:
        cols = {n: r.metrics for n, r in self.sleeves.items()}
        cols["BOOK"] = self.metrics
        return pd.DataFrame(cols)


class PortfolioManager:
    """Runs several strategies as independently-capitalised sleeves and combines them."""

    def __init__(self, sleeves: list[Sleeve | BaseStrategy], capital: float = 100_000,
                 start: str = "2020-06-01", end: str | None = None, config: ExecConfig = REALISTIC):
        if not sleeves:
            raise ValueError("Need at least one sleeve")
        self.sleeves = [s if isinstance(s, Sleeve) else Sleeve(s) for s in sleeves]
        names = [s.strategy.name for s in self.sleeves]
        if len(set(names)) != len(names):
            raise ValueError(f"Sleeve names must be unique: {names}")
        total_w = sum(s.weight for s in self.sleeves)
        self.weights = {s.strategy.name: s.weight / total_w for s in self.sleeves}
        self.capital, self.start, self.end, self.config = capital, start, end, config
        self.result: BookResult | None = None

    def run(self) -> BookResult:
        results = {}
        for s in self.sleeves:
            name = s.strategy.name
            results[name] = backtest_strategy(s.strategy, self.capital * self.weights[name],
                                              s.start or self.start, self.end, self.config)
        idx = sorted(set().union(*(r.equity.index for r in results.values())))
        idx = pd.DatetimeIndex(idx)
        book = sum(r.equity.reindex(idx).ffill().fillna(r.capital) for r in results.values())
        book = book.rename("BOOK")
        bench = sum(r.benchmark.reindex(idx).ffill().fillna(r.capital) for r in results.values())
        all_pos = pd.concat([r.positions for r in results.values()], ignore_index=True)
        m = compute_metrics(book, positions=all_pos, ppy=periods_per_year(idx),
                            fees_paid=sum(r.metrics.get("Costs Paid", 0) for r in results.values()),
                            benchmark=bench)
        self.result = BookResult(results, book, m, self.capital, self.weights)
        return self.result
