"""Market data loading with a local parquet cache.

Strategies never download data themselves: the engine loads it once per
symbol, caches it, and hands strategies an aligned OHLCV panel. This removes
the duplicate downloads / sleeps of the old PortfolioManager and makes runs
reproducible (re-running a backtest offline gives identical numbers).
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

FIELDS = ["Open", "High", "Low", "Close", "Volume"]
CACHE_DIR = Path(os.environ.get("ENGINE_CACHE", Path(__file__).resolve().parents[1] / "data_cache"))
MAX_CACHE_AGE_HOURS = 12


def _cache_path(symbol: str, interval: str) -> Path:
    safe = symbol.replace("/", "_").replace("=", "_").replace("^", "_")
    return CACHE_DIR / f"{safe}_{interval}.parquet"


def _download(symbol: str, start: str, interval: str, retries: int = 3) -> pd.DataFrame:
    import yfinance as yf

    last_err = None
    for attempt in range(retries):
        try:
            df = yf.download(symbol, start=start, interval=interval, auto_adjust=False,
                             progress=False, multi_level_index=False)
            if df.empty:
                raise ValueError(f"yfinance returned no data for {symbol}")
            # yfinance >=0.2.50 returns (Price, Ticker) MultiIndex columns even for a
            # single ticker - this is what produced the "Object has multiple columns"
            # warnings in the old code. Flatten defensively.
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df[FIELDS].astype(float)
            df.index = pd.DatetimeIndex(df.index).tz_localize(None).normalize()
            df.index.name = "Date"
            return df[~df.index.duplicated(keep="last")].sort_index()
        except Exception as e:  # network / rate limit
            last_err = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"Download failed for {symbol}: {last_err}")


def clean_ohlcv(df: pd.DataFrame, symbol: str = "") -> pd.DataFrame:
    """Drop bars that cannot be traded or would corrupt return maths.

    The main offender is continuous futures (CL=F printed -$37.63 on 2020-04-20):
    a non-positive price makes pct_change / log returns meaningless and lets a
    backtest "buy" at a negative price. Such bars are removed and logged.
    """
    bad = (df[["Open", "High", "Low", "Close"]] <= 0).any(axis=1) | df["Close"].isna()
    if bad.any():
        log.warning("%s: dropping %d untradeable bar(s): %s", symbol, int(bad.sum()),
                    [d.date().isoformat() for d in df.index[bad]][:5])
    df = df.loc[~bad].copy()
    # Repair inconsistent OHLC (occasional bad Yahoo prints)
    df["High"] = df[["Open", "High", "Low", "Close"]].max(axis=1)
    df["Low"] = df[["Open", "High", "Low", "Close"]].min(axis=1)
    return df


def load_ohlcv(symbol: str, start: str = "2014-01-01", end: str | None = None,
               interval: str = "1d", refresh: bool = False, offline: bool = False) -> pd.DataFrame:
    """Return cleaned OHLCV for one symbol, using/refreshing the parquet cache."""
    path = _cache_path(symbol, interval)
    df = None
    if path.exists() and not refresh:
        df = pd.read_parquet(path)
        stale = (time.time() - path.stat().st_mtime) / 3600 > MAX_CACHE_AGE_HOURS
        covers_start = df.index[0] <= pd.Timestamp(start) + pd.Timedelta(days=7)
        if (stale or not covers_start) and not offline:
            df = None
    if df is None:
        if offline:
            raise FileNotFoundError(f"No cached data for {symbol} and offline=True")
        dl_start = min(pd.Timestamp(start), pd.Timestamp("2014-01-01")).strftime("%Y-%m-%d")
        df = _download(symbol, dl_start, interval)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path)
    df = clean_ohlcv(df, symbol)
    df = df.loc[pd.Timestamp(start):]
    if end is not None:
        df = df.loc[:pd.Timestamp(end)]
    return df


def load_panel(symbols: list[str], start: str, end: str | None = None, interval: str = "1d",
               join: str = "inner", **kw) -> dict[str, pd.DataFrame]:
    """Aligned panel: {field: DataFrame(index=dates, columns=symbols)}.

    `join="inner"` keeps only dates where every symbol traded, which is what a
    multi-leg strategy (e.g. a pair) needs.
    """
    frames = {s: load_ohlcv(s, start, end, interval, **kw) for s in symbols}
    idx = None
    for f in frames.values():
        idx = f.index if idx is None else (idx.intersection(f.index) if join == "inner" else idx.union(f.index))
    return {field: pd.DataFrame({s: frames[s][field].reindex(idx) for s in symbols}) for field in FIELDS}
