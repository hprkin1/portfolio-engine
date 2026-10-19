"""BTC Accelerator-Oscillator momentum (port of Portfolio/CTSI_Class.py).

Logic is unchanged from the original:
    long  while AO > AC
    short while AO < AC
with a 2% stop loss.

Note for the strategy-review phase: since AC = AO - SMA(AO), the rule
"AO > AC" is algebraically "SMA(AO, ao_sma_period) > 0". It is a smoothed
Awesome-Oscillator sign filter, not an acceleration signal.
"""
from __future__ import annotations

import pandas as pd

from engine.strategy import BaseStrategy, Panel, Signals


class ACMomentum(BaseStrategy):
    DEFAULT_SYMBOLS = ["BTC-USD"]
    DEFAULT_PARAMS = {"short_sma_period": 5, "long_sma_period": 34, "ao_sma_period": 5}
    WARMUP_BARS = 60

    def __init__(self, name="BTC AC Momentum", symbols=None, sl_stop=0.02, **params):
        super().__init__(name, symbols, sl_stop=sl_stop, **params)

    def indicators(self, panel: Panel) -> pd.DataFrame:
        s = self.symbols[0]
        p = self.params
        median = (panel["High"][s] + panel["Low"][s]) / 2
        ao = median.rolling(p["short_sma_period"]).mean() - median.rolling(p["long_sma_period"]).mean()
        sma_ao = ao.rolling(p["ao_sma_period"]).mean()
        return pd.DataFrame({"AO": ao, "SMA_AO": sma_ao, "AC": ao - sma_ao})

    def signals(self, panel: Panel, ind: pd.DataFrame) -> Signals:
        s = self.symbols[0]
        long_ = (ind["AO"] > ind["AC"]).to_frame(s)
        short = (ind["AO"] < ind["AC"]).to_frame(s)
        return Signals(entries=long_, exits=short, short_entries=short, short_exits=long_)
