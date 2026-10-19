"""BTC momentum + On-Balance-Volume (port of Portfolio/momentum_obv_strategy.py).

Logic is unchanged from the original:
    long  when Close - Close[t-75] > 0 AND OBV rising
    short when Close - Close[t-75] < 0
    an entry in one direction exits the other.

Note for the strategy-review phase: OBV[t] > OBV[t-1] is exactly
"today's close > yesterday's close" (whenever volume > 0), so the OBV leg
adds no volume information - it is a 1-day up-close filter on long entries.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine.strategy import BaseStrategy, Panel, Signals


class OBVMomentum(BaseStrategy):
    DEFAULT_SYMBOLS = ["BTC-USD"]
    DEFAULT_PARAMS = {"mom_period": 75}
    WARMUP_BARS = 100

    def __init__(self, name="BTC OBV Momentum", symbols=None, **params):
        super().__init__(name, symbols, **params)

    def indicators(self, panel: Panel) -> pd.DataFrame:
        s = self.symbols[0]
        close, vol = panel["Close"][s], panel["Volume"][s]
        obv = (np.sign(close.diff()) * vol).cumsum().fillna(0)
        mom = close.diff(self.params["mom_period"])
        return pd.DataFrame({"OBV": obv, "Momentum": mom})

    def signals(self, panel: Panel, ind: pd.DataFrame) -> Signals:
        s = self.symbols[0]
        entries = (ind["Momentum"] > 0) & (ind["OBV"] > ind["OBV"].shift(1))
        short_entries = ind["Momentum"] < 0
        return Signals(entries=entries.to_frame(s), exits=short_entries.to_frame(s),
                       short_entries=short_entries.to_frame(s), short_exits=entries.to_frame(s))
