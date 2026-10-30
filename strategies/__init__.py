from .ac_momentum import ACMomentum
from .obv_momentum import OBVMomentum
from .oil_trend_carry import OilTrendCarry

# Failed / retired strategies (pairs v1/v2, WTI/Brent correlation, Brent-WTI spread, multi-asset trend) live in
# Algorithmic-Trading-Repository/Development/portfolio_engine_research.
REGISTRY = {cls.__name__: cls for cls in (ACMomentum, OBVMomentum, OilTrendCarry)}
__all__ = ["ACMomentum", "OBVMomentum", "OilTrendCarry", "REGISTRY"]
