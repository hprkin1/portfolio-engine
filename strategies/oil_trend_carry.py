"""Outright oil: trend + carry, optionally conditioned on the Brent–WTI spread.

Thesis (replaces Brent–WTI spread mean reversion, see reports/oil/README.md)
---------------------------------------------------------------------------
Two of the best-documented commodity return drivers, applied to oil ETFs:

* TREND (time-series momentum, Moskowitz–Ooi–Pedersen 2012): the sign of the
  past `trend_lb`-day *total* return of the ETF (which includes roll yield)
  predicts the next month's sign.
* CARRY (Koijen–Moskowitz–Pedersen–Vrugt 2018): in backwardation a long
  futures holder earns roll yield; in contango they pay it. Measured here from
  the data we have: roll yield ≈ ETF return − front-month futures price return
  over `carry_lb` days (the ETF captures the roll, the continuous price series
  doesn't). Positive = backwardation.
* SPREAD regime (optional): a wide Brent–WTI spread (vs its 1y median) flags a
  seaborne-supply stress regime. Longs are only allowed in that regime and
  shorts only outside it.

Stabilisers (added 2026-10-30, see reports/oil/stabilise.md):
    spread_smooth  average the (noisy, front-month) spread over N days first
    confirm_days   each of trend sign / carry sign / spread regime only switches
                   once the new value has held N consecutive days (debounce)

Rules → target weight w in [-max_lev, +max_lev] of sleeve equity:
    rule="trend":  w = sign(trend)
    rule="carry":  w = sign(carry)
    rule="both":   +1 if trend>0 and carry>0, -1 if both <0, else 0
    long_only:     clip negative weights to 0
    vol_target>0:  scale |w| to vol_target / realised vol (vol_lb days), capped at max_lev

Symbols: traded = [ETF]; signal_symbols = [front future of that ETF, other
grade's front future] e.g. USO -> ["CL=F", "BZ=F"], BNO -> ["BZ=F", "CL=F"].
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine.strategy import BaseStrategy, Panel, Signals

FRONT = {"USO": "CL=F", "BNO": "BZ=F"}


def debounce(x: pd.Series, n: int) -> pd.Series:
    """Causal debounce: the output switches to a new value only after the input has
    shown that value for n consecutive bars. n<=1 returns x unchanged. NaN passes through."""
    if n <= 1:
        return x
    v = x.to_numpy(dtype=float)
    out = np.full(len(v), np.nan)
    state, cand, cnt = np.nan, np.nan, 0
    for i, xi in enumerate(v):
        if np.isnan(xi):
            out[i] = state
            continue
        if np.isnan(state):
            state = xi
        elif xi == state:
            cnt = 0
        elif xi == cand:
            cnt += 1
            if cnt >= n:
                state, cnt = xi, 0
        else:
            cand, cnt = xi, 1
            if n == 1:
                state = xi
        out[i] = state
    return pd.Series(out, index=x.index)


class OilTrendCarry(BaseStrategy):
    DEFAULT_SYMBOLS = ["USO"]
    DEFAULT_SIGNAL_SYMBOLS = ["CL=F", "BZ=F"]
    DEFAULT_PARAMS = {
        "rule": "both",          # "trend" | "carry" | "both" | "hold"
        "trend_lb": 252,
        "carry_lb": 63,
        "long_only": False,
        "vol_target": 0.0,       # annualised, 0 = off (fixed ±1 weight)
        "vol_lb": 20,
        "max_lev": 1.0,
        "spread_filter": False,
        "spread_lb": 252,
        "spread_smooth": 1,      # days to average the Brent-WTI spread before comparing to its median
        "confirm_days": 1,       # a trend/carry/spread state only switches after holding this many days
    }
    WARMUP_BARS = 400

    def __init__(self, name=None, symbols=None, signal_symbols=None, **params):
        symbols = symbols or self.DEFAULT_SYMBOLS
        if signal_symbols is None:
            front = FRONT.get(symbols[0], "CL=F")
            signal_symbols = [front] + [s for s in ("CL=F", "BZ=F") if s != front]
        super().__init__(name or f"Oil Trend/Carry {symbols[0]}", symbols, signal_symbols=signal_symbols, **params)
        if self.params["rule"] not in ("trend", "carry", "both", "hold"):
            raise ValueError("rule must be trend|carry|both|hold")

    def indicators(self, panel: Panel) -> pd.DataFrame:
        p = self.params
        etf, front = self.symbols[0], self.signal_symbols[0]
        c = panel["Close"]
        lc = np.log(c)
        trend = lc[etf].diff(p["trend_lb"])
        carry = (lc[etf].diff(p["carry_lb"]) - lc[front].diff(p["carry_lb"])) * 252 / p["carry_lb"]
        vol = lc[etf].diff().rolling(p["vol_lb"]).std() * np.sqrt(252)
        out = {"trend": trend, "carry": carry, "vol": vol}
        if "BZ=F" in c and "CL=F" in c:
            spread = (c["BZ=F"] - c["CL=F"]).rolling(p["spread_smooth"]).mean()
            out["bw_spread"] = spread
            out["bw_spread_med"] = spread.rolling(p["spread_lb"]).median()
        return pd.DataFrame(out, index=c.index)

    def signals(self, panel: Panel, ind: pd.DataFrame) -> Signals:
        p = self.params
        n = p["confirm_days"]
        t, k = debounce(np.sign(ind["trend"]), n), debounce(np.sign(ind["carry"]), n)
        if p["rule"] == "hold":
            w = pd.Series(1.0, index=ind.index)
        elif p["rule"] == "trend":
            w = t
        elif p["rule"] == "carry":
            w = k
        else:
            w = pd.Series(np.where((t > 0) & (k > 0), 1.0, np.where((t < 0) & (k < 0), -1.0, 0.0)), index=ind.index)
            w[t.isna() | k.isna()] = np.nan
        if p["spread_filter"] and "bw_spread" in ind:
            raw = (ind["bw_spread"] > ind["bw_spread_med"]).astype(float).where(ind["bw_spread_med"].notna())
            stress = debounce(raw, n) == 1
            w = w.where(~((w > 0) & ~stress), 0.0).where(~((w < 0) & stress), 0.0)
        if p["long_only"]:
            w = w.clip(lower=0)
        if p["vol_target"] > 0:
            scale = (p["vol_target"] / ind["vol"]).clip(upper=p["max_lev"])
            w = w * scale
        else:
            w = w * p["max_lev"]
        w = w.fillna(0.0)
        return Signals(target=w.to_frame(self.symbols[0]))
