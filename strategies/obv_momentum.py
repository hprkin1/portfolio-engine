"""BTC momentum + On-Balance-Volume (port of Portfolio/momentum_obv_strategy.py).

Signal logic is unchanged from the original:
    long  when Close - Close[t-75] > 0 AND OBV rising
    short when Close - Close[t-75] < 0
    an entry in one direction exits the other.

CHANGE (2026-10-30): default 2% stop-loss (sl_stop=0.02), the only variant that passed
scripts/research_obv.py. Without it the strategy lost 99% in Mar-May 2020 (all-in short
from the COVID low while BTC doubled). Pass sl_stop=None for the original behaviour.

Note: OBV[t] > OBV[t-1] is exactly "today's close > yesterday's close"
(whenever volume > 0), so the OBV leg is a 1-day up-close filter on long entries.

Optional variants (all OFF by default - with sl_stop=None these reproduce the original exactly,
see tests/test_engine.py::test_obv_defaults_unchanged). Researched in
scripts/research_obv.py / reports/obv/README.md:
    obv_mode       "rising" (original) | "sma" (OBV above its obv_sma-day mean) | "none"
    symmetric      shorts also need volume confirmation; exits on momentum sign only
    long_only      never short
    confirm_days   momentum sign must hold N days before it counts (debounce)
    lookbacks      tuple of momentum lookbacks -> position = average of their signs (target weights)
    vol_target     annualised vol target (target weights), capped at max_lev
                   (both target-weight variants require obv_mode='none')
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine.strategy import BaseStrategy, Panel, Signals
from strategies.oil_trend_carry import debounce


class OBVMomentum(BaseStrategy):
    DEFAULT_SYMBOLS = ["BTC-USD"]
    DEFAULT_PARAMS = {
        "mom_period": 75,
        "obv_mode": "rising",
        "obv_sma": 20,
        "symmetric": False,
        "long_only": False,
        "confirm_days": 1,
        "lookbacks": None,
        "vol_target": 0.0,
        "vol_lb": 30,
        "max_lev": 1.0,
    }
    WARMUP_BARS = 100

    def __init__(self, name="BTC OBV Momentum", symbols=None, sl_stop=0.02, **params):
        super().__init__(name, symbols, sl_stop=sl_stop, **params)
        if (self.params["lookbacks"] or self.params["vol_target"] > 0) and self.params["obv_mode"] != "none":
            raise ValueError("target-weight variants (lookbacks / vol_target) require obv_mode='none'")
        if self.params["lookbacks"]:
            self.WARMUP_BARS = max(self.params["lookbacks"]) + 30

    def indicators(self, panel: Panel) -> pd.DataFrame:
        p = self.params
        s = self.symbols[0]
        close, vol = panel["Close"][s], panel["Volume"][s]
        obv = (np.sign(close.diff()) * vol).cumsum().fillna(0)
        out = {"OBV": obv, "Momentum": close.diff(p["mom_period"]),
               "OBV_SMA": obv.rolling(p["obv_sma"]).mean(),
               "Vol": np.log(close).diff().rolling(p["vol_lb"]).std() * np.sqrt(365)}
        for lb in p["lookbacks"] or ():
            out[f"mom_{lb}"] = close.diff(lb)
        return pd.DataFrame(out)

    def _obv_up_down(self, ind):
        mode = self.params["obv_mode"]
        if mode == "rising":
            return ind["OBV"] > ind["OBV"].shift(1), ind["OBV"] < ind["OBV"].shift(1)
        if mode == "sma":
            return ind["OBV"] > ind["OBV_SMA"], ind["OBV"] < ind["OBV_SMA"]
        t = pd.Series(True, index=ind.index)
        return t, t

    def signals(self, panel: Panel, ind: pd.DataFrame) -> Signals:
        p = self.params
        s = self.symbols[0]
        target_mode = bool(p["lookbacks"]) or p["vol_target"] > 0

        if p["lookbacks"]:
            sig = sum(np.sign(ind[f"mom_{lb}"]) for lb in p["lookbacks"]) / len(p["lookbacks"])
        else:
            sig = np.sign(ind["Momentum"])
        if p["confirm_days"] > 1:
            sig = debounce(sig, p["confirm_days"])
        mom_pos, mom_neg = sig > 0, sig < 0
        obv_up, obv_dn = self._obv_up_down(ind)

        if not target_mode:
            entries = mom_pos & obv_up
            short_entries = (mom_neg & obv_dn) if p["symmetric"] else mom_neg
            if p["long_only"]:
                short_entries = short_entries & False
            if p["symmetric"]:
                exits, short_exits = mom_neg, mom_pos
            else:
                exits, short_exits = mom_neg, entries
            f = lambda x: x.to_frame(s)
            return Signals(entries=f(entries), exits=f(exits), short_entries=f(short_entries), short_exits=f(short_exits))

        # target-weight mode: hold the (ensemble) momentum direction (OBV filter not used here)
        w = sig.astype(float)
        if p["long_only"]:
            w = w.clip(lower=0)
        if p["vol_target"] > 0:
            w = w * (p["vol_target"] / ind["Vol"]).clip(upper=p["max_lev"])
        return Signals(target=w.fillna(0.0).to_frame(s))
