"""Trading-cost assumptions.

Same philosophy as HyperliquidStrat/core/costs.py: assume taker fills plus a
slippage haircut, so an edge that survives here has margin to spare.
Both numbers are charged per side (on entry and on exit).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostModel:
    fee: float       # proportional fee per side, e.g. 0.0005 = 5 bps
    slippage: float  # proportional price haircut per side

    @property
    def roundtrip(self) -> float:
        return 2 * (self.fee + self.slippage)


PRESETS: dict[str, CostModel] = {
    # Binance USD-M futures taker 5 bps (what Live_Futures_Bot trades). Funding is NOT modelled.
    "crypto_perp": CostModel(fee=0.0005, slippage=0.0005),
    "crypto_spot": CostModel(fee=0.0010, slippage=0.0005),
    # CME energy futures: commission is tiny vs notional; spread + roll friction dominates.
    "futures": CostModel(fee=0.0001, slippage=0.0003),
    "equity": CostModel(fee=0.0005, slippage=0.0005),
    "zero": CostModel(fee=0.0, slippage=0.0),
}


def infer_asset_class(symbol: str) -> str:
    s = symbol.upper()
    if s.endswith("-USD") or s.endswith("USDT") or "/USD" in s:
        return "crypto_perp"
    if s.endswith("=F"):
        return "futures"
    return "equity"


def costs_for(symbols: list[str]) -> CostModel:
    """Use the most expensive preset among a strategy's symbols."""
    models = [PRESETS[infer_asset_class(s)] for s in symbols]
    return max(models, key=lambda m: m.roundtrip)
