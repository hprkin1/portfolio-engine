from .ac_momentum import ACMomentum
from .corr_reversion import CorrReversion
from .obv_momentum import OBVMomentum
from .oil_spread import OilSpreadReversion

REGISTRY = {cls.__name__: cls for cls in (ACMomentum, OBVMomentum, CorrReversion, OilSpreadReversion)}
__all__ = ["ACMomentum", "OBVMomentum", "CorrReversion", "OilSpreadReversion", "REGISTRY"]
