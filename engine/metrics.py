"""Performance metrics computed from an equity curve.

Computed directly rather than via vbt.stats() so that:
 - multi-column portfolios are never silently averaged (old bug),
 - annualisation uses the right calendar (365 for crypto, 252 for futures/equities),
 - key names are stable (the old code read 'Annual Return [%]' / '# Trades',
   which vectorbt doesn't produce, so those came back as None).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def periods_per_year(index: pd.DatetimeIndex) -> int:
    years = max((index[-1] - index[0]).days / 365.25, 1e-9)
    density = len(index) / years
    return 365 if density > 300 else 252


def drawdown(equity: pd.Series) -> pd.Series:
    return equity / equity.cummax() - 1


def compute_metrics(equity: pd.Series, positions: pd.DataFrame | None = None,
                    ppy: int | None = None, fees_paid: float | None = None,
                    exposure: float | None = None, benchmark: pd.Series | None = None) -> dict:
    equity = equity.dropna()
    if len(equity) < 3:
        return {}
    ppy = ppy or periods_per_year(equity.index)
    rets = equity.pct_change().dropna()
    days = (equity.index[-1] - equity.index[0]).days
    total = equity.iloc[-1] / equity.iloc[0] - 1
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (365.25 / max(days, 1)) - 1 if equity.iloc[-1] > 0 else -1.0
    vol = rets.std() * np.sqrt(ppy)
    sharpe = rets.mean() / rets.std() * np.sqrt(ppy) if rets.std() > 0 else np.nan
    downside = rets[rets < 0].std()
    sortino = rets.mean() / downside * np.sqrt(ppy) if downside and downside > 0 else np.nan
    dd = drawdown(equity)
    max_dd = dd.min()
    # longest time spent below a previous peak
    underwater = dd < 0
    if underwater.any():
        groups = (~underwater).cumsum()
        spans = equity.index.to_series()[underwater].groupby(groups[underwater]).agg(["first", "last"])
        max_dd_days = int((spans["last"] - spans["first"]).dt.days.max())
    else:
        max_dd_days = 0

    m = {
        "Start": equity.index[0].date(),
        "End": equity.index[-1].date(),
        "Total Return %": 100 * total,
        "CAGR %": 100 * cagr,
        "Ann. Vol %": 100 * vol,
        "Sharpe": sharpe,
        "Sortino": sortino,
        "Max DD %": 100 * max_dd,
        "Max DD Days": max_dd_days,
        "Calmar": cagr / abs(max_dd) if max_dd < 0 else np.nan,
    }
    if positions is not None:
        closed = positions[positions["Status"] == "Closed"] if "Status" in positions else positions
        n = len(closed)
        wins = closed[closed["PnL"] > 0]
        losses = closed[closed["PnL"] <= 0]
        m.update({
            "Trades": n,
            "Trades/Yr": n / max(days / 365.25, 1e-9),
            "Win Rate %": 100 * len(wins) / n if n else np.nan,
            "Avg Win %": 100 * wins["Return"].mean() if len(wins) else np.nan,
            "Avg Loss %": 100 * losses["Return"].mean() if len(losses) else np.nan,
            "Profit Factor": wins["PnL"].sum() / -losses["PnL"].sum() if losses["PnL"].sum() < 0 else np.inf,
        })
    if exposure is not None:
        m["Exposure %"] = 100 * exposure
    if fees_paid is not None:
        m["Costs Paid"] = fees_paid
    if benchmark is not None:
        b = benchmark.reindex(equity.index).ffill().dropna()
        if len(b) > 2:
            m["Benchmark Return %"] = 100 * (b.iloc[-1] / b.iloc[0] - 1)
            br = b.pct_change().dropna()
            r = rets.reindex(br.index).dropna()
            m["Benchmark Sharpe"] = br.mean() / br.std() * np.sqrt(ppy) if br.std() > 0 else np.nan
            m["Corr to Benchmark"] = r.corr(br.reindex(r.index))
    return m


def metrics_table(results: dict[str, dict]) -> pd.DataFrame:
    return pd.DataFrame(results)
