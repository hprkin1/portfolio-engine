"""What gets paper traded. Edit here; the daily tick reads this file.

Each sleeve gets `weight / sum(weights)` of CAPITAL, fixed (no rebalancing between sleeves).
Changing strategies or settings after paper trading has started changes the replay: the tick reports
the difference as "drift" so it's visible. Start a fresh book (python -m paper.tick --reset) for a clean record.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from engine import ExecConfig
from engine.strategy import BaseStrategy
from strategies import ACMomentum, OBVMomentum, OilTrendCarry

CAPITAL = 30_000.0


@dataclass
class PaperSleeve:
    name: str
    make: Callable[[], BaseStrategy]
    config: ExecConfig
    weight: float = 1.0


SLEEVES: list[PaperSleeve] = [
    PaperSleeve("BTC OBV Momentum", lambda: OBVMomentum(), ExecConfig()),
    PaperSleeve("BTC AC Momentum", lambda: ACMomentum(), ExecConfig()),
    PaperSleeve("Oil Trend/Carry BNO",
                lambda: OilTrendCarry(name="Oil Trend/Carry BNO", symbols=["BNO"], rule="both", spread_filter=True,
                                      vol_target=0.20, max_lev=1.0, confirm_days=10, spread_smooth=5),
                ExecConfig(rebalance_band=0.10)),
]


def sleeve_capital() -> dict[str, float]:
    tot = sum(s.weight for s in SLEEVES)
    return {s.name: CAPITAL * s.weight / tot for s in SLEEVES}
