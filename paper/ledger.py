"""Forward paper trading: replay-and-append.

Each tick re-runs every sleeve through the SAME engine used for backtests (so fills, stops and costs are
identical), from the paper start date up to the latest COMPLETED daily bar, then APPENDS only the new days
to an append-only ledger in paper/state/. Rows already written are never rewritten (frozen record);
if a replay disagrees with what was recorded (e.g. Yahoo revised a price), the difference is stored as drift.

Timing: a decision made at a bar's close is filled at the next bar's open (engine contract). The tick
stores the latest decision as the "next open" order for each sleeve.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from engine import backtest_strategy
from engine.costs import infer_asset_class
from engine.data import load_panel

STATE = Path(os.environ.get("PAPER_STATE", Path(__file__).resolve().parent / "state"))
US_CLOSE_UTC_HOUR = 21  # 4pm New York (EST); in US summer time the close is 20:00 UTC, so this is conservative


def _now() -> datetime:
    return datetime.now(timezone.utc)


def complete_bars(panel: dict, now: datetime) -> dict:
    """Drop today's still-forming bar. Crypto bars close at 00:00 UTC; US-listed bars after the US close."""
    today = pd.Timestamp(now.date())
    syms = list(panel["Close"].columns)
    crypto = all(infer_asset_class(s).startswith("crypto") for s in syms)
    cutoff = today if (crypto or now.hour < US_CLOSE_UTC_HOUR) else today + pd.Timedelta(days=1)
    return {k: v.loc[v.index < cutoff] for k, v in panel.items()}


# ---------- state ----------
def _paths(state: Path):
    return {"meta": state / "meta.json", "equity": state / "equity.csv", "fills": state / "fills.csv",
            "orders": state / "orders.csv"}


def load_meta(state: Path = STATE) -> dict | None:
    p = _paths(state)["meta"]
    return json.loads(p.read_text()) if p.exists() else None


def _append(path: Path, df: pd.DataFrame):
    if df.empty:
        return
    df.to_csv(path, mode="a", header=not path.exists(), index=False)


def read_csv(name: str, state: Path = STATE) -> pd.DataFrame:
    p = _paths(state)[name]
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


# ---------- extraction ----------
def _fills(r) -> pd.DataFrame:
    rows = []
    if r.portfolio is not None:
        o = r.portfolio.orders.records_readable
        for _, x in o.iterrows():
            rows.append({"date": x["Timestamp"], "symbol": x.get("Column", r.strategy.symbols[0]),
                         "action": "Buy" if str(x["Side"]).startswith("Buy") else "Sell",
                         "price": float(x["Price"]), "size": float(x["Size"]), "reason": "signal"})
    else:
        for _, p in r.positions.iterrows():
            long_ = p["Direction"] == "Long"
            rows.append({"date": p["Entry Timestamp"], "symbol": p["Column"], "action": "Buy" if long_ else "Sell short",
                         "price": float(p["Avg Entry Price"]), "size": np.nan, "reason": "signal"})
            if p["Status"] == "Closed":
                rows.append({"date": p["Exit Timestamp"], "symbol": p["Column"],
                             "action": "Sell (exit long)" if long_ else "Buy (cover short)",
                             "price": float(p["Avg Exit Price"]), "size": np.nan, "reason": p.get("Exit Reason", "signal")})
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def current_position(r) -> dict[str, str]:
    """Position held at the last bar's close, per symbol: 'long 0.62', 'short', 'flat'."""
    out = {}
    if r.portfolio is not None:
        val = r.portfolio.value()
        val = val.iloc[-1] if np.ndim(val.iloc[-1]) == 0 else val.iloc[-1].sum()
        av = r.portfolio.asset_value(group_by=False) if len(r.strategy.symbols) > 1 else r.portfolio.asset_value()
        av = av.to_frame(r.strategy.symbols[0]) if isinstance(av, pd.Series) else av
        for s in r.strategy.symbols:
            w = float(av[s].iloc[-1] / val) if val else 0.0
            out[s] = "flat" if abs(w) < 1e-6 else f"{'long' if w > 0 else 'short'} {abs(w):.0%}"
    else:
        open_ = r.positions[r.positions["Status"] == "Open"] if len(r.positions) else r.positions
        for s in r.strategy.symbols:
            o = open_[open_["Column"] == s] if len(open_) else open_
            out[s] = "flat" if len(o) == 0 else ("long 100%" if o.iloc[-1]["Direction"] == "Long" else "short 100%")
    return out


def next_open_order(strategy, panel) -> dict[str, str]:
    """The decision taken at the last completed bar's close, executed at the next open."""
    _, sig = strategy.run(panel)
    out = {}
    for s in strategy.symbols:
        if sig.is_target:
            t = sig.target[s].dropna()
            w = float(t.iloc[-1]) if len(t) else 0.0
            out[s] = "flat" if abs(w) < 1e-6 else f"{'long' if w > 0 else 'short'} {abs(w):.0%} target"
        else:
            if bool(sig.entries[s].iloc[-1]):
                out[s] = "long"
            elif bool(sig.short_entries[s].iloc[-1]):
                out[s] = "short"
            elif bool(sig.exits[s].iloc[-1]) or bool(sig.short_exits[s].iloc[-1]):
                out[s] = "exit"
            else:
                out[s] = "no new signal (keep current position)"
    return out


# ---------- tick ----------
def tick(sleeves, capital_by_sleeve: dict[str, float], state: Path = STATE, now: datetime | None = None,
         force: bool = False, refresh: bool = True, loader=load_panel) -> dict:
    now = now or _now()
    state.mkdir(parents=True, exist_ok=True)
    P = _paths(state)
    meta = load_meta(state)
    if meta is None:
        start = (now + timedelta(days=1)).date().isoformat()
        meta = {"start": start, "created_utc": now.isoformat(timespec="seconds"),
                "capital": capital_by_sleeve, "last_bar": {}, "drift_pct": {}, "ticks": 0}
    start = meta["start"]
    summary = {"start": start, "sleeves": {}}
    new_orders = []
    for sl in sleeves:
        strat = sl.make()
        warm = (pd.Timestamp(start) - pd.Timedelta(days=int(strat.WARMUP_BARS * 1.6) + 30)).strftime("%Y-%m-%d")
        panel = complete_bars(loader(strat.all_symbols, warm, refresh=refresh), now)
        last_bar = panel["Close"].index[-1]
        prev = meta["last_bar"].get(sl.name)
        info = {"last_bar": str(last_bar.date()), "new_days": 0}
        if prev is not None and pd.Timestamp(prev) >= last_bar and not force:
            kept = dict((meta.get("latest") or {}).get(sl.name) or info)   # keep last positions/orders
            kept["status"] = "up to date"
            summary["sleeves"][sl.name] = kept
            continue
        order = next_open_order(strat, panel)
        decided = last_bar.date().isoformat()
        logged = read_csv("orders", state)
        if logged.empty or not ((logged.decided_at_close == decided) & (logged.sleeve == sl.name)).any():
            new_orders.append({"decided_at_close": decided, "sleeve": sl.name,
                               "order": "; ".join(f"{k}: {v}" for k, v in order.items())})
        info["next_open"] = order
        if last_bar >= pd.Timestamp(start):
            r = backtest_strategy(sl.make(), capital_by_sleeve[sl.name], start, config=sl.config, panel=panel)
            eq = r.equity
            cut = pd.Timestamp(prev) if prev else pd.Timestamp(start) - pd.Timedelta(days=1)
            # drift: replayed value vs frozen record on the last recorded day
            old = read_csv("equity", state)
            if prev and not old.empty:
                rec = old[(old.sleeve == sl.name) & (old.date == prev)]
                if len(rec) and pd.Timestamp(prev) in eq.index:
                    meta["drift_pct"][sl.name] = round(100 * (eq.loc[pd.Timestamp(prev)] / rec.equity.iloc[-1] - 1), 4)
            new_eq = eq[eq.index > cut]
            _append(P["equity"], pd.DataFrame({"date": new_eq.index.strftime("%Y-%m-%d"), "sleeve": sl.name,
                                               "equity": new_eq.values.round(2)}))
            f = _fills(r)
            if not f.empty:
                f = f[f.date > cut]
                f.insert(1, "sleeve", sl.name)
                f["date"] = f.date.dt.strftime("%Y-%m-%d")
                _append(P["fills"], f)
            info["new_days"] = int(len(new_eq))
            info["equity"] = round(float(eq.iloc[-1]), 2)
            info["position"] = current_position(r)
        else:
            info["position"] = {s: "flat (paper trading starts " + start + ")" for s in strat.symbols}
        info["status"] = "updated"
        meta["last_bar"][sl.name] = last_bar.date().isoformat()
        summary["sleeves"][sl.name] = info
    _append(P["orders"], pd.DataFrame(new_orders))
    meta["ticks"] = meta.get("ticks", 0) + 1
    meta["last_tick_utc"] = now.isoformat(timespec="seconds")
    meta["latest"] = summary["sleeves"]
    P["meta"].write_text(json.dumps(meta, indent=1, default=str))
    return summary
