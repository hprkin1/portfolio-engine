"""Strategy contract.

A strategy is pure logic: given an aligned OHLCV panel it returns signals.
It never downloads data and never runs a backtest itself.

THE TIMING RULE: a signal on bar t may use information up to and including
the CLOSE of bar t. The engine executes it on the NEXT bar (open by default).
Strategies must therefore NOT shift their own signals - the engine does it once,
uniformly. `tests/test_engine.py::test_no_lookahead` enforces this for every strategy.

Two signal styles
-----------------
1. Event signals: entries / exits / short_entries / short_exits (booleans).
   Each trade uses the leg's full capital.
2. Target weights: `target` = desired position as a fraction of sleeve equity
   (e.g. 1.0 = 100% long, -0.5 = 50% short, 0 = flat). Use this for
   position sizing / volatility targeting. NaN means "no change".

`symbols` are traded. `signal_symbols` are loaded into the panel for the
strategy to read (e.g. a futures series used to compute carry) but never traded.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import Any, ClassVar

import pandas as pd

Panel = dict[str, pd.DataFrame]  # {"Open"|"High"|"Low"|"Close"|"Volume": DataFrame[dates x symbols]}
_EVENT = ("entries", "exits", "short_entries", "short_exits")


@dataclass
class Signals:
    entries: pd.DataFrame | None = None
    exits: pd.DataFrame | None = None
    short_entries: pd.DataFrame | None = None
    short_exits: pd.DataFrame | None = None
    target: pd.DataFrame | None = None

    @property
    def is_target(self) -> bool:
        return self.target is not None

    def _map(self, fn_bool, fn_target) -> "Signals":
        out = {}
        for f in fields(self):
            x = getattr(self, f.name)
            out[f.name] = None if x is None else (fn_target(x) if f.name == "target" else fn_bool(x))
        return Signals(**out)

    def aligned(self, index: pd.Index, columns: list[str]) -> "Signals":
        def frame(x):
            if isinstance(x, pd.Series):
                x = x.to_frame(columns[0])
            return x.reindex(index=index, columns=columns)
        return self._map(lambda x: frame(x).fillna(False).astype(bool),
                         lambda x: frame(x).astype(float))

    def shifted(self, n: int = 1) -> "Signals":
        return self._map(lambda x: x.shift(n).fillna(False).astype(bool), lambda x: x.shift(n))

    def subset(self, mask) -> "Signals":
        return self._map(lambda x: x.loc[mask], lambda x: x.loc[mask])


class BaseStrategy(ABC):
    DEFAULT_PARAMS: ClassVar[dict[str, Any]] = {}
    DEFAULT_SYMBOLS: ClassVar[list[str]] = []
    DEFAULT_SIGNAL_SYMBOLS: ClassVar[list[str]] = []
    WARMUP_BARS: ClassVar[int] = 100  # history loaded before `start` so indicators are warm

    def __init__(self, name: str | None = None, symbols: list[str] | None = None,
                 sl_stop: float | None = None, tp_stop: float | None = None,
                 signal_symbols: list[str] | None = None, **params):
        unknown = set(params) - set(self.DEFAULT_PARAMS)
        if unknown:
            raise ValueError(f"{type(self).__name__}: unknown params {sorted(unknown)}")
        self.name = name or type(self).__name__
        self.symbols = list(symbols or self.DEFAULT_SYMBOLS)
        self.signal_symbols = list(signal_symbols if signal_symbols is not None else self.DEFAULT_SIGNAL_SYMBOLS)
        self.params = {**self.DEFAULT_PARAMS, **params}
        self.sl_stop = sl_stop
        self.tp_stop = tp_stop

    @property
    def all_symbols(self) -> list[str]:
        return self.symbols + [s for s in self.signal_symbols if s not in self.symbols]

    @abstractmethod
    def indicators(self, panel: Panel) -> pd.DataFrame:
        """Return a DataFrame of indicator columns on the panel's index."""

    @abstractmethod
    def signals(self, panel: Panel, ind: pd.DataFrame) -> Signals:
        """Return raw (unshifted) signals for self.symbols."""

    def run(self, panel: Panel) -> tuple[pd.DataFrame, Signals]:
        ind = self.indicators(panel)
        sig = self.signals(panel, ind).aligned(panel["Close"].index, self.symbols)
        return ind, sig

    def __repr__(self):
        return f"{type(self).__name__}({self.symbols}, {self.params}, sl={self.sl_stop})"
