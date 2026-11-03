"""Dashboard helpers (offline)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard.core import SPECS, defaults, expected_band, monthly_returns, paper_book  # noqa: E402


def test_monthly_returns_compound_to_year():
    idx = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    eq = pd.Series(np.linspace(100, 121, len(idx)), index=idx)
    t = monthly_returns(eq)
    months = t.drop(columns="Year").iloc[0] / 100
    assert np.prod(1 + months) - 1 == pytest.approx(t["Year"].iloc[0] / 100, rel=1e-9)


def test_paper_book_ffills_calendars():
    rows = pd.DataFrame({"date": ["2026-11-01", "2026-11-02", "2026-11-02", "2026-11-03"],
                         "sleeve": ["btc", "btc", "etf", "btc"], "equity": [10_100, 10_200, 9_900, 10_300]})
    b = paper_book(rows)
    assert b.loc["2026-11-03", "etf"] == 9_900                       # ETF carried over a non-trading day
    assert b.loc["2026-11-03", "BOOK"] == 10_300 + 9_900


def test_expected_band_ordering():
    idx = pd.date_range("2020-01-01", periods=800, freq="D")
    eq = pd.Series(100 * np.exp(np.cumsum(np.random.default_rng(1).normal(0.001, 0.02, 800))), index=idx)
    b = expected_band(eq, 30)
    assert b["p5"] < b["p50"] < b["p95"]


def test_specs_build_with_defaults():
    for k in SPECS:
        s = SPECS[k].build(defaults(k))
        assert s.symbols


def test_paper_book_counts_sleeves_before_their_first_day():
    rows = pd.DataFrame({"date": ["2026-10-31", "2026-11-01", "2026-11-02", "2026-11-02"],
                         "sleeve": ["btc", "btc", "btc", "etf"], "equity": [10_000, 10_100, 10_050, 9_900]})
    b = paper_book(rows, {"btc": 10_000, "etf": 10_000})
    assert b.loc["2026-10-31", "BOOK"] == 20_000          # ETF not trading yet -> still its starting capital
    assert b.loc["2026-11-02", "BOOK"] == 10_050 + 9_900
