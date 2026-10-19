"""Offline tests on synthetic data (no network)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import LEGACY, REALISTIC, CostModel, ExecConfig, PortfolioManager, Sleeve, backtest_strategy  # noqa: E402
from engine.data import clean_ohlcv  # noqa: E402
from engine.strategy import BaseStrategy, Signals  # noqa: E402
from strategies import REGISTRY  # noqa: E402


def synthetic_panel(symbols=("AAA-USD",), n=600, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    base = rng.normal(0, 0.02, (n, 1))
    out = {f: {} for f in ["Open", "High", "Low", "Close", "Volume"]}
    for i, s in enumerate(symbols):
        r = 0.8 * base[:, 0] + 0.6 * rng.normal(0, 0.02, n)  # correlated legs
        close = 100 * np.exp(np.cumsum(r))
        open_ = close * np.exp(rng.normal(0, 0.005, n))
        out["Close"][s], out["Open"][s] = close, open_
        out["High"][s] = np.maximum(open_, close) * (1 + abs(rng.normal(0, 0.01, n)))
        out["Low"][s] = np.minimum(open_, close) * (1 - abs(rng.normal(0, 0.01, n)))
        out["Volume"][s] = rng.uniform(1e6, 2e6, n)
    return {f: pd.DataFrame(v, index=idx) for f, v in out.items()}


def make(name):
    cls = REGISTRY[name]
    syms = ["AAA-USD", "BBB-USD"] if name in ("CorrReversion", "OilSpreadReversion") else ["AAA-USD"]
    kw = {"entry_corr_low": 0.95} if name == "CorrReversion" else {}  # make it trade on synthetic data
    return cls(symbols=syms, **kw), syms


@pytest.mark.parametrize("name", list(REGISTRY))
def test_no_lookahead(name):
    """Signals at bar t must not change when future bars are removed."""
    strat, syms = make(name)
    panel = synthetic_panel(tuple(syms))
    _, full = strat.run(panel)
    for cut in (200, 350, 500):
        trunc = {k: v.iloc[:cut] for k, v in panel.items()}
        _, part = strat.run(trunc)
        for attr in ("entries", "exits", "short_entries", "short_exits"):
            pd.testing.assert_frame_equal(getattr(part, attr), getattr(full, attr).iloc[:cut], check_freq=False)


class OneShot(BaseStrategy):
    """Buys on bar 10, sells on bar 20."""
    DEFAULT_SYMBOLS = ["AAA-USD"]
    WARMUP_BARS = 0

    def indicators(self, panel):
        return pd.DataFrame(index=panel["Close"].index)

    def signals(self, panel, ind):
        idx = panel["Close"].index
        e = pd.DataFrame(False, index=idx, columns=self.symbols); x = e.copy()
        e.iloc[10] = True; x.iloc[20] = True
        return Signals(e, x, e & False, e & False)


def test_next_open_fill_and_costs():
    panel = synthetic_panel()
    cfg = ExecConfig("next_open", intrabar_stops=False, costs=CostModel(fee=0.001, slippage=0.0))
    r = backtest_strategy(OneShot(), 10_000, "2020-01-01", config=cfg, panel=panel)
    orders = r.portfolio.orders.records_readable
    assert list(orders["Timestamp"]) == [panel["Close"].index[11], panel["Close"].index[21]]
    assert np.allclose(orders["Price"], [panel["Open"].iloc[11, 0], panel["Open"].iloc[21, 0]])
    gross = panel["Open"].iloc[21, 0] / panel["Open"].iloc[11, 0]
    expected = 10_000 / (1 + 0.001) * gross * (1 - 0.001)  # entry fee is charged on top of notional
    assert r.equity.iloc[-1] == pytest.approx(expected, rel=1e-9)


def test_legacy_fills_same_close():
    panel = synthetic_panel()
    r = backtest_strategy(OneShot(), 10_000, "2020-01-01", config=LEGACY, panel=panel)
    orders = r.portfolio.orders.records_readable
    assert orders["Timestamp"].iloc[0] == panel["Close"].index[10]
    assert orders["Price"].iloc[0] == pytest.approx(panel["Close"].iloc[10, 0])


def test_book_accounting(monkeypatch):
    panels = {"AAA-USD": synthetic_panel(("AAA-USD",), seed=1), "BBB-USD": synthetic_panel(("BBB-USD",), seed=2)}
    monkeypatch.setattr("engine.portfolio.load_panel", lambda syms, *a, **k: panels[syms[0]])
    s1, s2 = REGISTRY["ACMomentum"](name="a", symbols=["AAA-USD"]), REGISTRY["OBVMomentum"](name="b", symbols=["BBB-USD"])
    book = PortfolioManager([Sleeve(s1, 2), Sleeve(s2, 1)], capital=90_000, start="2020-01-01").run()
    assert book.weights == pytest.approx({"a": 2 / 3, "b": 1 / 3})
    assert book.equity.iloc[0] == pytest.approx(90_000, rel=0.01)  # first bar may already include a fill cost
    se = book.sleeve_equity()
    assert np.allclose(se.sum(axis=1), book.equity)
    assert book.contribution().sum() == pytest.approx(100 * (book.equity.iloc[-1] - 90_000) / 90_000)


def test_duplicate_sleeve_names_rejected():
    with pytest.raises(ValueError):
        PortfolioManager([REGISTRY["ACMomentum"](), REGISTRY["ACMomentum"]()])


def test_clean_drops_negative_prices():
    df = synthetic_panel()
    one = pd.DataFrame({f: df[f].iloc[:, 0] for f in df})
    one.iloc[5, one.columns.get_loc("Close")] = -37.6
    assert len(clean_ohlcv(one)) == len(one) - 1


def test_unknown_param_rejected():
    with pytest.raises(ValueError):
        REGISTRY["ACMomentum"](long_sma=10)
