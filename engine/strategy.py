"""Strategy contract.

A strategy is pure logic: given an aligned OHLCV panel it returns signals.
It never downloads data and never runs a backtest itself.

THE TIMING RULE: a signal on bar t may use information up to and including
the CLOSE of bar t. The engine executes it on the NEXT bar (open by default).
Strategies must therefore NOT shift their own signals - the engine does it once,
uniformly. `tests/test_no_lookahead.py` enforces this for every strategy.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

import pandas as pd

Panel = dict[str, pd.DataFrame]  # {"Open"|"High"|"Low"|"Close"|"Volume": DataFrame[dates x symbols]}


@dataclass
class Signals:
    entries: pd.DataFrame
    exits: pd.DataFrame
    short_entries: pd.DataFrame
    short_exits: pd.DataFrame

    def aligned(self, index: pd.Index, columns: list[str]) -> "Signals":
        def fix(x):
            if isinstance(x, pd.Series):
                x = x.to_frame(columns[0])
            return x.reindex(index=index, columns=columns).fillna(False).astype(bool)
        return Signals(fix(self.entries), fix(self.exits), fix(self.short_entries), fix(self.short_exits))

    def shifted(self, n: int = 1) -> "Signals":
        s = lambda x: x.shift(n).fillna(False).astype(bool)
        return Signals(s(self.entries), s(self.exits), s(self.short_entries), s(self.short_exits))


class BaseStrategy(ABC):
    DEFAULT_PARAMS: ClassVar[dict[str, Any]] = {}
    DEFAULT_SYMBOLS: ClassVar[list[str]] = []
    WARMUP_BARS: ClassVar[int] = 100  # history loaded before `start` so indicators are warm

    def __init__(self, name: str | None = None, symbols: list[str] | None = None,
                 sl_stop: float | None = None, tp_stop: float | None = None, **params):
        unknown = set(params) - set(self.DEFAULT_PARAMS)
        if unknown:
            raise ValueError(f"{type(self).__name__}: unknown params {sorted(unknown)}")
        self.name = name or type(self).__name__
        self.symbols = list(symbols or self.DEFAULT_SYMBOLS)
        self.params = {**self.DEFAULT_PARAMS, **params}
        self.sl_stop = sl_stop
        self.tp_stop = tp_stop

    @abstractmethod
    def indicators(self, panel: Panel) -> pd.DataFrame:
        """Return a DataFrame of indicator columns on the panel's index."""

    @abstractmethod
    def signals(self, panel: Panel, ind: pd.DataFrame) -> Signals:
        """Return raw (unshifted) signals."""

    def run(self, panel: Panel) -> tuple[pd.DataFrame, Signals]:
        ind = self.indicators(panel)
        sig = self.signals(panel, ind).aligned(panel["Close"].index, self.symbols)
        return ind, sig

    def __repr__(self):
        return f"{type(self).__name__}({self.symbols}, {self.params}, sl={self.sl_stop})"
