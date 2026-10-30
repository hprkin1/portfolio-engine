"""Dashboard logic without Streamlit (so it can be tested and reused)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import pandas as pd

from engine import CostModel, ExecConfig, PortfolioManager, Sleeve, backtest_strategy
from engine.costs import costs_for
from engine.metrics import compute_metrics, drawdown
from strategies import ACMomentum, OBVMomentum, OilTrendCarry


@dataclass
class Param:
    name: str
    label: str
    kind: str              # "int" | "float" | "bool" | "choice"
    default: Any
    lo: float | None = None
    hi: float | None = None
    step: float | None = None
    choices: list | None = None
    help: str = ""


@dataclass
class Spec:
    key: str
    title: str
    blurb: str
    default_start: str
    params: list[Param]
    build: Callable[[dict], Any]
    rebalance_band: float = 0.0
    sweepable: list[str] = field(default_factory=list)


def _obv(p):
    return OBVMomentum(mom_period=int(p["mom_period"]), sl_stop=(p["sl_stop"] or None))


def _ac(p):
    return ACMomentum(short_sma_period=int(p["short_sma_period"]), long_sma_period=int(p["long_sma_period"]),
                      ao_sma_period=int(p["ao_sma_period"]), sl_stop=(p["sl_stop"] or None))


def _oil(p):
    return OilTrendCarry(name=f"Oil Trend/Carry {p['etf']}", symbols=[p["etf"]], rule=p["rule"],
                         spread_filter=bool(p["spread_filter"]), vol_target=float(p["vol_target"]), max_lev=1.0,
                         confirm_days=int(p["confirm_days"]), spread_smooth=int(p["spread_smooth"]),
                         trend_lb=int(p["trend_lb"]), carry_lb=int(p["carry_lb"]))


SPECS: dict[str, Spec] = {
    "obv": Spec("obv", "BTC OBV Momentum",
                "Long when 75-day momentum is positive and today closed up; short when momentum is negative. 2% stop.",
                "2020-06-01",
                [Param("mom_period", "Momentum lookback (days)", "int", 75, 10, 300, 5),
                 Param("sl_stop", "Stop-loss (0 = off)", "float", 0.02, 0.0, 0.10, 0.005)],
                _obv, sweepable=["mom_period", "sl_stop"]),
    "ac": Spec("ac", "BTC AC Momentum",
               "Accelerator Oscillator: long while AO > AC, short while AO < AC. 2% stop.",
               "2019-01-07",
               [Param("short_sma_period", "Short SMA (days)", "int", 5, 2, 20, 1),
                Param("long_sma_period", "Long SMA (days)", "int", 34, 10, 100, 1),
                Param("ao_sma_period", "AO smoothing (days)", "int", 5, 2, 20, 1),
                Param("sl_stop", "Stop-loss (0 = off)", "float", 0.02, 0.0, 0.10, 0.005)],
               _ac, sweepable=["short_sma_period", "long_sma_period", "ao_sma_period", "sl_stop"]),
    "oil": Spec("oil", "Oil Trend/Carry",
                "Outright oil ETF: long when 12-month trend and curve carry agree (short when both negative), "
                "longs only in a wide Brent–WTI spread regime; 20% vol target.",
                "2012-01-01",
                [Param("etf", "ETF", "choice", "BNO", choices=["BNO", "USO"]),
                 Param("rule", "Rule", "choice", "both", choices=["both", "trend", "carry", "hold"]),
                 Param("spread_filter", "Brent–WTI spread filter", "bool", True),
                 Param("vol_target", "Vol target", "float", 0.20, 0.05, 0.60, 0.05),
                 Param("confirm_days", "Signal confirmation (days)", "int", 10, 1, 30, 1),
                 Param("spread_smooth", "Spread smoothing (days)", "int", 5, 1, 20, 1),
                 Param("trend_lb", "Trend lookback (days)", "int", 252, 21, 400, 21),
                 Param("carry_lb", "Carry lookback (days)", "int", 63, 21, 252, 21)],
                _oil, rebalance_band=0.10, sweepable=["confirm_days", "spread_smooth", "trend_lb", "carry_lb", "vol_target"]),
}


def defaults(key: str) -> dict:
    return {p.name: p.default for p in SPECS[key].params}


def exec_config(key: str, cost_mult: float, strategy) -> ExecConfig:
    base = costs_for(strategy.symbols)
    return ExecConfig(costs=CostModel(base.fee * cost_mult, base.slippage * cost_mult),
                      rebalance_band=SPECS[key].rebalance_band)


def run_sleeve(key: str, params: dict, start: str, end: str | None = None, capital: float = 100_000,
               cost_mult: float = 1.0):
    s = SPECS[key].build(params)
    return backtest_strategy(s, capital, start, end, config=exec_config(key, cost_mult, s))


def run_book(selection: dict[str, dict], start: str, end: str | None, capital: float, weighting: str,
             weights: dict[str, float] | None = None, cost_mult: float = 1.0, max_weight: float | None = None):
    """selection = {spec_key: params}. Each sleeve keeps its own execution config (costs, rebalance band)."""
    weights = weights or {k: 1.0 for k in selection}
    sleeves = []
    for k, p in selection.items():
        st = SPECS[k].build(p)
        sleeves.append(Sleeve(st, weights.get(k, 1.0), config=exec_config(k, cost_mult, st)))
    return PortfolioManager(sleeves, capital=capital, start=start, end=end, weighting=weighting,
                            max_weight=max_weight).run()


def metrics_frame(book) -> pd.DataFrame:
    keep = ["Total Return %", "CAGR %", "Ann. Vol %", "Sharpe", "Sortino", "Max DD %", "Max DD Days", "Calmar",
            "Trades", "Trades/Yr", "Win Rate %", "Exposure %", "Costs Paid"]
    t = book.metrics_table().T
    t = t.reindex(columns=[c for c in keep if c in t.columns])
    return t.apply(pd.to_numeric, errors="coerce")


def monthly_returns(equity: pd.Series) -> pd.DataFrame:
    m = equity.resample("ME").last()
    r = m.pct_change()
    r.iloc[0] = m.iloc[0] / equity.iloc[0] - 1
    df = pd.DataFrame({"year": r.index.year, "month": r.index.month, "ret": 100 * r.values})
    t = df.pivot(index="year", columns="month", values="ret").reindex(columns=range(1, 13))
    t.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    y = equity.resample("YE").last()
    t["Year"] = (100 * (y / y.shift(1).fillna(equity.iloc[0]) - 1)).values
    return t


def sweep(key: str, params: dict, p1: str, v1: list, start: str, end: str | None, cost_mult: float = 1.0,
          p2: str | None = None, v2: list | None = None, metric: str = "Sharpe") -> pd.DataFrame:
    rows = {}
    for a in v1:
        if p2 is None:
            rows[a] = {metric: run_sleeve(key, {**params, p1: a}, start, end, cost_mult=cost_mult).metrics.get(metric)}
        else:
            rows[a] = {b: run_sleeve(key, {**params, p1: a, p2: b}, start, end, cost_mult=cost_mult).metrics.get(metric)
                       for b in v2}
    return pd.DataFrame(rows).T


def cost_stress(key: str, params: dict, start: str, end: str | None, mults=(0, 1, 2, 3, 5)) -> pd.DataFrame:
    return pd.DataFrame({m: {k: run_sleeve(key, params, start, end, cost_mult=m).metrics.get(k)
                             for k in ("Sharpe", "CAGR %", "Max DD %")} for m in mults}).T


def yearly_sharpe(equity: pd.Series) -> pd.Series:
    out = {}
    for y, e in equity.groupby(equity.index.year):
        if len(e) > 20:
            out[y] = compute_metrics(e)["Sharpe"]
    return pd.Series(out)


def book_drawdown(equity: pd.Series) -> pd.Series:
    return 100 * drawdown(equity)


# ---------- paper ----------
def paper_book(equity_rows: pd.DataFrame) -> pd.DataFrame:
    """Wide frame of sleeve equity (forward-filled across calendars) + BOOK column."""
    if equity_rows.empty:
        return pd.DataFrame()
    w = equity_rows.pivot_table(index="date", columns="sleeve", values="equity")
    w.index = pd.to_datetime(w.index)
    w = w.sort_index().ffill()
    w["BOOK"] = w.sum(axis=1, min_count=1)
    return w


def expected_band(book_equity_backtest: pd.Series, days: int, q=(0.05, 0.5, 0.95)) -> dict:
    """Distribution of `days`-calendar-day returns of the backtest book (for comparing paper results)."""
    e = book_equity_backtest
    if days < 2 or len(e) < days + 30:
        return {}
    idx = e.index
    later = e.reindex(idx + pd.Timedelta(days=days), method="ffill").to_numpy()
    r = pd.Series(later / e.to_numpy() - 1, index=idx).loc[: idx[-1] - pd.Timedelta(days=days)]
    return {f"p{int(x * 100)}": float(100 * r.quantile(x)) for x in q}
