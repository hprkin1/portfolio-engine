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
    rebalance_band: float = 0.0         # target-weight mode: skip rebalances smaller than this (abs weight)

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
    portfolio: vbt.Portfolio | None   # None when the stop simulator (engine/stopsim.py) was used
    signals: Signals
    indicators: pd.DataFrame
    positions: pd.DataFrame
    metrics: dict
    config: ExecConfig

    @property
    def returns(self) -> pd.Series:
        return self.equity.pct_change().fillna(0)


def _apply_band(target: pd.DataFrame, band: float) -> pd.DataFrame:
    """Only re-send a target when it moved more than `band` from the last one sent
    (or crossed to/from zero). Cuts turnover from small vol-targeting adjustments."""
    out = target.copy() * float("nan")
    for c in target:
        last = 0.0
        vals = target[c].to_numpy()
        res = out[c].to_numpy().copy()
        for i, v in enumerate(vals):
            if v != v:  # NaN
                continue
            if abs(v - last) > band or (v == 0) != (last == 0) or (v * last < 0):
                res[i] = v
                last = v
        out[c] = res
    return out


def _warmup_start(start: str, bars: int) -> str:
    return (pd.Timestamp(start) - pd.Timedelta(days=int(bars * 1.6) + 10)).strftime("%Y-%m-%d")


def backtest_strategy(strategy: BaseStrategy, capital: float = 100_000, start: str = "2019-01-01",
                      end: str | None = None, config: ExecConfig = REALISTIC,
                      panel: Panel | None = None) -> SleeveResult:
    if config.execution not in EXECUTION_MODES:
        raise ValueError(f"execution must be one of {EXECUTION_MODES}")
    syms = strategy.symbols
    if panel is None:
        panel = load_panel(strategy.all_symbols, _warmup_start(start, strategy.WARMUP_BARS), end)

    ind, sig = strategy.run(panel)
    if config.execution != "same_close":
        sig = sig.shifted(1)

    # trim warm-up period only AFTER indicators/signals are computed; trade only `syms`
    keep = panel["Close"].index >= pd.Timestamp(start)
    p = {k: v.loc[keep, syms] for k, v in panel.items()}
    sig = sig.subset(keep)

    costs = config.cost_model(syms)
    n = len(syms)
    exec_price = p["Open"] if config.execution == "next_open" else p["Close"]
    if sig.is_target:
        # only trade when the target changes (by more than the band) - never drift-rebalance
        target = _apply_band(sig.target, config.rebalance_band)
        kwargs = dict(close=p["Close"], size=target, size_type="targetpercent", price=exec_price,
                      fees=costs.fee, slippage=costs.slippage, init_cash=capital,
                      cash_sharing=True, group_by=True if n > 1 else None,
                      call_seq="auto" if n > 1 else None, freq="1D")
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        pf = vbt.Portfolio.from_orders(**kwargs)
        ungrouped = vbt.Portfolio.from_orders(**{**kwargs, "group_by": None, "cash_sharing": False,
                                                 "call_seq": None, "init_cash": capital}) if n > 1 else pf
    elif config.execution == "next_open" and (strategy.sl_stop or strategy.tp_stop):
        # vbt mis-orders stops vs open fills; use the purpose-built simulator (see engine/stopsim.py)
        from .stopsim import simulate
        equity, positions, fees_paid, exposure = simulate(
            p, sig, capital, costs.fee, costs.slippage, strategy.sl_stop, strategy.tp_stop, config.intrabar_stops)
        equity = equity.rename(strategy.name)
        close = p["Close"]
        bench = (close / close.iloc[0]).mean(axis=1) * capital
        metrics = compute_metrics(equity, positions=positions, ppy=periods_per_year(close.index),
                                  fees_paid=fees_paid, exposure=exposure, benchmark=bench)
        return SleeveResult(strategy.name, strategy, capital, equity, bench.rename("Benchmark"), None,
                            sig, ind, positions, metrics, config)
    else:
        kwargs = dict(
            close=p["Close"],
            entries=sig.entries, exits=sig.exits,
            short_entries=sig.short_entries, short_exits=sig.short_exits,
            price=exec_price,
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
        if strategy.sl_stop or strategy.tp_stop:
            kwargs["stop_entry_price"] = "fillprice"   # vbt default is the entry bar's close
        pf = vbt.Portfolio.from_signals(**kwargs)
        ungrouped = vbt.Portfolio.from_signals(**{**kwargs, "group_by": None}) if n > 1 else pf
    equity = pf.value()
    if isinstance(equity, pd.DataFrame):
        equity = equity.iloc[:, 0]
    equity = equity.rename(strategy.name)

    close = p["Close"]
    bench = (close / close.iloc[0]).mean(axis=1) * capital
    positions = ungrouped.positions.records_readable
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
    start: str | None = None            # per-sleeve override
    config: ExecConfig | None = None    # per-sleeve execution/costs override (default: the manager's)


@dataclass
class BookResult:
    sleeves: dict[str, SleeveResult]
    equity: pd.Series
    metrics: dict
    capital: float
    weights: dict[str, float] = field(default_factory=dict)   # risk budgets (normalised)
    weight_history: pd.DataFrame | None = None                # actual capital weights after each rebalance
    _sleeve_equity: pd.DataFrame | None = None

    def sleeve_equity(self) -> pd.DataFrame:
        """Dollar value held in each sleeve over time (sums to book equity)."""
        if self._sleeve_equity is not None:
            return self._sleeve_equity
        idx = self.equity.index
        return pd.DataFrame({n: r.equity.reindex(idx).ffill().fillna(r.capital) for n, r in self.sleeves.items()})

    def sleeve_pnl(self) -> pd.Series:
        """Cumulative $ P&L earned by each sleeve (excludes transfers between sleeves)."""
        return self._pnl if getattr(self, "_pnl", None) is not None else \
            self.sleeve_equity().iloc[-1] - self.sleeve_equity().iloc[0]

    def contribution(self) -> pd.Series:
        """P&L contribution of each sleeve as % of total book capital."""
        return 100 * self.sleeve_pnl() / self.capital

    def correlation(self) -> pd.DataFrame:
        return pd.DataFrame({n: r.returns for n, r in self.sleeves.items()}).corr()

    def metrics_table(self) -> pd.DataFrame:
        cols = {n: r.metrics for n, r in self.sleeves.items()}
        cols["BOOK"] = self.metrics
        return pd.DataFrame(cols)


WEIGHTINGS = ("capital", "inverse_vol")


class PortfolioManager:
    """Runs several strategies as sleeves and combines them into one book.

    weighting="capital"      fixed capital split by Sleeve.weight, never rebalanced (original behaviour).
    weighting="inverse_vol"  Sleeve.weight is a RISK budget: each sleeve gets capital proportional to
                             budget / trailing realised vol (vol_lookback days of its own returns, its
                             own calendar, floored at vol_floor), rebalanced every `rebalance` period
                             ("ME" = month end). A sleeve that was flat for the whole window falls back
                             to the vol of its full history so far (a 0-vol reading would be meaningless).
                             Weights use only data up to the rebalance close (no look-ahead) and a
                             transfer cost `transfer_cost` is charged on capital moved between sleeves.
                             `max_weight` caps any one sleeve's capital share (excess spread pro-rata).
    """

    def __init__(self, sleeves: list[Sleeve | BaseStrategy], capital: float = 100_000,
                 start: str = "2020-06-01", end: str | None = None, config: ExecConfig = REALISTIC,
                 weighting: str = "capital", vol_lookback: int = 252, rebalance: str = "ME",
                 max_weight: float | None = None, transfer_cost: float = 0.001, vol_floor: float = 0.05):
        if not sleeves:
            raise ValueError("Need at least one sleeve")
        if weighting not in WEIGHTINGS:
            raise ValueError(f"weighting must be one of {WEIGHTINGS}")
        self.sleeves = [s if isinstance(s, Sleeve) else Sleeve(s) for s in sleeves]
        names = [s.strategy.name for s in self.sleeves]
        if len(set(names)) != len(names):
            raise ValueError(f"Sleeve names must be unique: {names}")
        total_w = sum(s.weight for s in self.sleeves)
        self.weights = {s.strategy.name: s.weight / total_w for s in self.sleeves}
        self.capital, self.start, self.end, self.config = capital, start, end, config
        self.weighting, self.vol_lookback, self.rebalance = weighting, vol_lookback, rebalance
        self.max_weight, self.transfer_cost, self.vol_floor = max_weight, transfer_cost, vol_floor
        self.result: BookResult | None = None

    def run(self) -> BookResult:
        results = {}
        for s in self.sleeves:
            name = s.strategy.name
            cap = self.capital * (self.weights[name] if self.weighting == "capital" else 1.0)
            results[name] = backtest_strategy(s.strategy, cap, s.start or self.start, self.end, s.config or self.config)
        idx = pd.DatetimeIndex(sorted(set().union(*(r.equity.index for r in results.values()))))
        all_pos = pd.concat([r.positions for r in results.values()], ignore_index=True)
        costs = sum(r.metrics.get("Costs Paid", 0) for r in results.values())

        if self.weighting == "capital":
            book = sum(r.equity.reindex(idx).ffill().fillna(r.capital) for r in results.values()).rename("BOOK")
            bench = sum(r.benchmark.reindex(idx).ffill().fillna(r.capital) for r in results.values())
            m = compute_metrics(book, positions=all_pos, ppy=periods_per_year(idx), fees_paid=costs, benchmark=bench)
            self.result = BookResult(results, book, m, self.capital, self.weights)
            return self.result

        book, sleeve_val, pnl, wh, moved = self._combine_inverse_vol(results, idx)
        m = compute_metrics(book, positions=all_pos, ppy=periods_per_year(idx),
                            fees_paid=None, benchmark=None)
        m["Avg Weights"] = {k: round(v, 3) for k, v in wh.mean().items()}
        m["Transfer Costs"] = moved
        res = BookResult(results, book, m, self.capital, self.weights, wh, sleeve_val)
        res._pnl = pnl
        self.result = res
        return res

    def target_weights(self, results: dict[str, SleeveResult], asof: pd.Timestamp) -> pd.Series:
        """Inverse-vol capital weights using each sleeve's returns up to and including `asof`."""
        raw = {}
        for n, r in results.items():
            hist = r.returns.loc[:asof]
            ppy = periods_per_year(r.equity.index)
            vol = hist.iloc[-self.vol_lookback:].std() * np.sqrt(ppy)
            if not (vol > 0) and len(hist) > 20:     # sleeve flat for the whole window: use its own longer history
                vol = hist.std() * np.sqrt(ppy)
            if not (vol > 0) or len(hist) < 20:
                raw[n] = np.nan
            else:
                raw[n] = self.weights[n] / max(vol, self.vol_floor)
        w = pd.Series(raw)
        if w.isna().any():                       # not enough history yet -> fall back to budgets
            w = pd.Series(self.weights)
        w = w / w.sum()
        if self.max_weight:
            for _ in range(len(w)):
                over = w > self.max_weight
                if not over.any():
                    break
                excess = (w[over] - self.max_weight).sum()
                w[over] = self.max_weight
                w[~over] += excess * w[~over] / w[~over].sum()
        return w

    def _combine_inverse_vol(self, results, idx):
        names = list(results)
        rets = pd.DataFrame({n: results[n].returns.reindex(idx).fillna(0.0) for n in names})
        reb_dates = set(pd.Series(idx, index=idx).resample(self.rebalance).last().dropna())
        vals = (self.target_weights(results, idx[0]) * self.capital).reindex(names).to_numpy()
        pnl = np.zeros(len(names))
        book, sv, wh_rows, wh_idx, moved = [], [], [], [], 0.0
        R = rets.to_numpy()
        for i, d in enumerate(idx):
            if i > 0:
                gain = vals * R[i]
                pnl += gain
                vals = vals + gain
            if d in reb_dates and i < len(idx) - 1:
                tot = vals.sum()
                tw = self.target_weights(results, d).reindex(names).to_numpy()
                new = tw * tot
                cost = np.abs(new - vals).sum() / 2 * self.transfer_cost
                moved += cost
                vals = new * (tot - cost) / tot
                wh_rows.append(tw); wh_idx.append(d)
            book.append(vals.sum()); sv.append(vals.copy())
        book = pd.Series(book, index=idx, name="BOOK")
        sleeve_val = pd.DataFrame(sv, index=idx, columns=names)
        wh = pd.DataFrame(wh_rows, index=wh_idx, columns=names)
        return book, sleeve_val, pd.Series(pnl, index=names), wh, moved
