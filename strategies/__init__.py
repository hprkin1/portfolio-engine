from .ac_momentum import ACMomentum
from .corr_reversion import CorrReversion
from .obv_momentum import OBVMomentum

REGISTRY = {cls.__name__: cls for cls in (ACMomentum, OBVMomentum, CorrReversion)}
__all__ = ["ACMomentum", "OBVMomentum", "CorrReversion", "REGISTRY"]
