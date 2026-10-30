from .ac_momentum import ACMomentum
from .corr_reversion import CorrReversion
from .obv_momentum import OBVMomentum
from .oil_spread import OilSpreadReversion
from .oil_trend_carry import OilTrendCarry
from .pairs_reversion import PairsReversion
from .pairs_portfolio import PairsPortfolio

REGISTRY = {cls.__name__: cls for cls in (ACMomentum, OBVMomentum, CorrReversion, OilSpreadReversion, OilTrendCarry, PairsReversion, PairsPortfolio)}
__all__ = ["ACMomentum", "OBVMomentum", "CorrReversion", "OilSpreadReversion", "OilTrendCarry", "PairsReversion", "PairsPortfolio", "REGISTRY"]
