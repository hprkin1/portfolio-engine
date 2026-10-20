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
            spread = c["BZ=F"] - c["CL=F"]
            out["bw_spread"] = spread
            out["bw_spread_med"] = spread.rolling(p["spread_lb"]).median()
        return pd.DataFrame(out, index=c.index)

    def signals(self, panel: Panel, ind: pd.DataFrame) -> Signals:
        p = self.params
        t, k = np.sign(ind["trend"]), np.sign(ind["carry"])
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
            stress = ind["bw_spread"] > ind["bw_spread_med"]
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
