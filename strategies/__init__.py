from .ac_momentum import ACMomentum
from .corr_reversion import CorrReversion
from .obv_momentum import OBVMomentum
from .oil_spread import OilSpreadReversion
from .oil_trend_carry import OilTrendCarry
from .pairs_reversion import PairsReversion

REGISTRY = {cls.__name__: cls for cls in (ACMomentum, OBVMomentum, CorrReversion, OilSpreadReversion, OilTrendCarry, PairsReversion)}
__all__ = ["ACMomentum", "OBVMomentum", "CorrReversion", "OilSpreadReversion", "OilTrendCarry", "PairsReversion", "REGISTRY"]
