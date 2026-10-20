from .ac_momentum import ACMomentum
from .corr_reversion import CorrReversion
from .obv_momentum import OBVMomentum
from .oil_spread import OilSpreadReversion
from .oil_trend_carry import OilTrendCarry

REGISTRY = {cls.__name__: cls for cls in (ACMomentum, OBVMomentum, CorrReversion, OilSpreadReversion, OilTrendCarry)}
__all__ = ["ACMomentum", "OBVMomentum", "CorrReversion", "OilSpreadReversion", "OilTrendCarry", "REGISTRY"]
