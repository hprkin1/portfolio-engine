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
    if name == "OilTrendCarry":
        s = cls(symbols=["AAA-USD"], signal_symbols=["BBB-USD"], trend_lb=60, carry_lb=20, vol_target=0.2,
                confirm_days=5)
        return s, ["AAA-USD", "BBB-USD"]
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
        for attr in ("entries", "exits", "short_entries", "short_exits", "target"):
            if getattr(full, attr) is None:
                continue
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


class HalfLong(BaseStrategy):
    """Target 50% long from bar 10, flat from bar 20."""
    DEFAULT_SYMBOLS = ["AAA-USD"]
    WARMUP_BARS = 0

    def indicators(self, panel):
        return pd.DataFrame(index=panel["Close"].index)

    def signals(self, panel, ind):
        w = pd.Series(0.0, index=panel["Close"].index); w.iloc[10:20] = 0.5
        return Signals(target=w.to_frame("AAA-USD"))


def test_target_weight_mode():
    panel = synthetic_panel()
    cfg = ExecConfig("next_open", intrabar_stops=False, costs=CostModel(fee=0.0, slippage=0.0))
    r = backtest_strategy(HalfLong(), 10_000, "2020-01-01", config=cfg, panel=panel)
    o = r.portfolio.orders.records_readable
    idx, op = panel["Close"].index, panel["Open"].iloc[:, 0]
    assert list(o["Timestamp"]) == [idx[11], idx[21]]
    assert o["Size"].iloc[0] * op.iloc[11] == pytest.approx(5_000, rel=1e-9)
    assert r.equity.iloc[-1] == pytest.approx(5_000 + 5_000 * op.iloc[21] / op.iloc[11], rel=1e-9)


def test_signal_symbols_not_traded():
    panel = synthetic_panel(("AAA-USD", "BBB-USD"))
    s = REGISTRY["OilTrendCarry"](symbols=["AAA-USD"], signal_symbols=["BBB-USD"], trend_lb=60, carry_lb=20)
    r = backtest_strategy(s, 10_000, "2020-01-01", panel=panel)
    assert list(r.portfolio.wrapper.columns) == ["AAA-USD"]


def test_debounce():
    from strategies.oil_trend_carry import debounce
    x = pd.Series([1, 1, -1, 1, -1, -1, -1, 1, 1, 1], dtype=float)
    assert list(debounce(x, 3)) == [1, 1, 1, 1, 1, 1, -1, -1, -1, 1]
    assert list(debounce(x, 1)) == list(x)


def test_inverse_vol_book(monkeypatch):
    panels = {"AAA-USD": synthetic_panel(("AAA-USD",), seed=1), "BBB-USD": synthetic_panel(("BBB-USD",), seed=2)}
    # make BBB 4x less volatile
    for f in ("Open", "High", "Low", "Close"):
        x = panels["BBB-USD"][f]
        panels["BBB-USD"][f] = 100 * (x / 100) ** 0.25
    monkeypatch.setattr("engine.portfolio.load_panel", lambda syms, *a, **k: panels[syms[0]])
    s1 = REGISTRY["OBVMomentum"](name="hi", symbols=["AAA-USD"], mom_period=20)
    s2 = REGISTRY["OBVMomentum"](name="lo", symbols=["BBB-USD"], mom_period=20)
    pm = PortfolioManager([s1, s2], capital=100_000, start="2020-01-01", weighting="inverse_vol", transfer_cost=0.0,
                          vol_lookback=60)
    book = pm.run()
    w = book.weight_history.iloc[-1]
    assert w["lo"] > 0.7 and w["hi"] < 0.3                       # low-vol sleeve gets more capital
    assert np.allclose(book.sleeve_equity().sum(axis=1), book.equity)
    assert book.sleeve_pnl().sum() == pytest.approx(book.equity.iloc[-1] - book.equity.iloc[0], rel=1e-6)
    # no look-ahead: weights chosen on date d only use returns up to d
    d = book.weight_history.index[3]
    trunc = {n: r for n, r in book.sleeves.items()}
    assert pm.target_weights(trunc, d).round(10).equals(book.weight_history.loc[d].round(10))


def _flip_strategy(sl=None):
    class Flip(BaseStrategy):
        DEFAULT_SYMBOLS = ["AAA-USD"]
        WARMUP_BARS = 0

        def indicators(self, panel):
            c = panel["Close"].iloc[:, 0]
            return pd.DataFrame({"m": c.diff(5)})

        def signals(self, panel, ind):
            up, dn = (ind["m"] > 0).to_frame("AAA-USD"), (ind["m"] < 0).to_frame("AAA-USD")
            return Signals(up, dn, dn, up)
    return Flip(sl_stop=sl)


def test_stopsim_matches_vbt_without_stops():
    """With no stops the purpose-built simulator must equal vectorbt exactly (fills, costs, shorts)."""
    from engine.stopsim import simulate
    panel = synthetic_panel(n=400)
    cfg = ExecConfig("next_open", intrabar_stops=True, costs=CostModel(fee=0.0007, slippage=0.0003))
    r = backtest_strategy(_flip_strategy(), 10_000, "2020-01-01", config=cfg, panel=panel)   # vbt path
    _, sig = _flip_strategy().run(panel)
    eq, pos, _, _ = simulate(panel, sig.shifted(1), 10_000, 0.0007, 0.0003)
    assert np.allclose(eq.to_numpy(), r.equity.to_numpy(), rtol=1e-9)
    assert len(pos[pos.Status == "Closed"]) == len(r.positions[r.positions.Status == "Closed"])


def test_stop_ordering_and_reference():
    """Signal at the open is processed before the intraday stop; stop is measured from the fill price."""
    from engine.stopsim import simulate_column
    #            bar0   bar1   bar2   bar3
    o = np.array([100., 100., 101., 100.])
    h = np.array([100., 101., 101., 100.])
    l = np.array([100.,  99.5, 95.,  100.])
    c = np.array([100., 100.5, 96., 100.])
    T, F = True, False
    ent = np.array([F, T, F, F]); ext = np.array([F, F, T, F])          # long at bar1 open, exit at bar2 open
    eq, tr, _, _ = simulate_column(o, h, l, c, ent, ext, np.zeros(4, bool), np.zeros(4, bool), 1000, 0, 0, sl_stop=0.02)
    # bar1 low 99.5 > 98 (2% below the 100 fill) -> no stop. bar2: exit signal at open 101 happens BEFORE the
    # intraday low of 95 -> trade closes at 101 via signal, not stopped at 98.
    assert len(tr) == 1 and tr[0][8] == "signal" and tr[0][4] == pytest.approx(101)
    assert eq[-1] == pytest.approx(1010)
    # Same path without the exit signal -> stopped at 98 on bar2 (opened at 101 > 98, so no gap)
    eq, tr, _, _ = simulate_column(o, h, l, c, ent, np.zeros(4, bool), np.zeros(4, bool), np.zeros(4, bool),
                                   1000, 0, 0, sl_stop=0.02)
    assert tr[0][8] == "stop" and tr[0][4] == pytest.approx(98)


def test_stop_strategy_uses_stopsim():
    panel = synthetic_panel(n=300)
    r = backtest_strategy(_flip_strategy(sl=0.02), 10_000, "2020-01-01", panel=panel)
    assert r.portfolio is None and "Exit Reason" in r.positions
    assert np.isfinite(r.equity).all() and r.metrics["Trades"] > 0
