"""Paper-trading ledger: append-only, idempotent, no incomplete bars, drift detection (offline)."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import ExecConfig  # noqa: E402
from paper.config import PaperSleeve  # noqa: E402
from paper.ledger import complete_bars, load_meta, read_csv, tick  # noqa: E402
from strategies import OBVMomentum  # noqa: E402


def panel_for(idx, seed=0, bump=None):
    rng = np.random.default_rng(seed)
    n = len(idx)
    c = 100 * np.exp(np.cumsum(rng.normal(0.001, 0.03, n)))
    if bump is not None:
        c = c.copy(); c[bump] *= 1.05            # a "revised" price
    o = c * np.exp(rng.normal(0, 0.003, n))
    f = lambda x: pd.DataFrame({"AAA-USD": x}, index=idx)
    return {"Open": f(o), "High": f(np.maximum(o, c) * 1.01), "Low": f(np.minimum(o, c) * 0.99),
            "Close": f(c), "Volume": f(rng.uniform(1e6, 2e6, n))}


IDX = pd.date_range("2024-01-01", "2026-03-01", freq="D")
SLEEVES = [PaperSleeve("OBV test", lambda: OBVMomentum(symbols=["AAA-USD"], mom_period=20), ExecConfig())]
CAP = {"OBV test": 10_000.0}


def loader_factory(**kw):
    p = panel_for(IDX, **kw)
    return lambda syms, start, refresh=True: {k: v.loc[start:] for k, v in p.items()}


def at(day, hour=0, minute=30):
    d = pd.Timestamp(day)
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=timezone.utc)


def test_complete_bars_drops_forming_bar():
    p = panel_for(IDX)
    out = complete_bars(p, at("2025-06-10"))
    assert out["Close"].index[-1] == pd.Timestamp("2025-06-09")


def test_ticks_append_only_and_idempotent(tmp_path):
    L = loader_factory()
    s1 = tick(SLEEVES, CAP, state=tmp_path, now=at("2025-06-10"), loader=L)
    assert s1["start"] == "2025-06-11" and read_csv("equity", tmp_path).empty
    assert len(read_csv("orders", tmp_path)) == 1                         # decision recorded for next open
    tick(SLEEVES, CAP, state=tmp_path, now=at("2025-06-20"), loader=L)
    e1 = read_csv("equity", tmp_path)
    assert e1.date.min() == "2025-06-11" and e1.date.max() == "2025-06-19"   # no bar from the forming day
    assert abs(e1.equity.iloc[0] - 10_000) < 10_000 * 0.2
    tick(SLEEVES, CAP, state=tmp_path, now=at("2025-06-20", 5), loader=L)   # same day again -> no-op
    assert read_csv("equity", tmp_path).equals(e1)
    tick(SLEEVES, CAP, state=tmp_path, now=at("2025-07-05"), loader=L)
    e2 = read_csv("equity", tmp_path)
    assert e2.date.is_unique and e2.iloc[: len(e1)].equals(e1)             # earlier rows untouched
    assert e2.date.max() == "2025-07-04"
    assert load_meta(tmp_path)["drift_pct"]["OBV test"] == 0.0


def test_revised_history_shows_drift_but_record_stays(tmp_path):
    tick(SLEEVES, CAP, state=tmp_path, now=at("2025-06-10"), loader=loader_factory())
    tick(SLEEVES, CAP, state=tmp_path, now=at("2025-06-20"), loader=loader_factory())
    before = read_csv("equity", tmp_path)
    bump = IDX.get_loc(pd.Timestamp("2025-06-19"))   # revise the last recorded close
    tick(SLEEVES, CAP, state=tmp_path, now=at("2025-06-25"), loader=loader_factory(bump=bump))
    after = read_csv("equity", tmp_path)
    assert after.iloc[: len(before)].equals(before)
    assert load_meta(tmp_path)["drift_pct"]["OBV test"] != 0.0


def test_up_to_date_keeps_orders_and_no_duplicate_decisions(tmp_path):
    L = loader_factory()
    tick(SLEEVES, CAP, state=tmp_path, now=at("2025-06-20"), loader=L)
    first = load_meta(tmp_path)["latest"]["OBV test"]
    tick(SLEEVES, CAP, state=tmp_path, now=at("2025-06-20", 6), loader=L)            # up to date
    again = load_meta(tmp_path)["latest"]["OBV test"]
    assert again["status"] == "up to date" and again["next_open"] == first["next_open"]
    tick(SLEEVES, CAP, state=tmp_path, now=at("2025-06-20", 7), loader=L, force=True)  # forced re-run
    o = read_csv("orders", tmp_path)
    assert not o.duplicated(["decided_at_close", "sleeve"]).any()
