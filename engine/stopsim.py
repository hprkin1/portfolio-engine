"""Event-signal simulator with correct stop handling for next-open execution.

Why this exists
---------------
vectorbt's from_signals (v1.x) has two behaviours that are wrong when orders fill
at the OPEN and stops are checked against intraday High/Low:
  1. stop levels are measured from the entry bar's CLOSE by default (not the fill);
  2. within a bar, stops are evaluated BEFORE the user's signal order, so on a day
     the signal flips at the open, vbt books a full stop-loss first and re-enters a
     day late instead of simply reversing at the open.
With same-close execution neither matters (that's why the original code was fine).

Order of events on each bar n (signals are already shifted: they were decided at close n-1):
  1. at the OPEN: act on signals (exit / reverse / enter), all-in sizing
  2. INTRADAY: check stop-loss / take-profit against Low/High (or Close if intrabar_stops=False),
     stop measured from the actual fill price; if the bar opens beyond the stop, fill at the open
  3. mark to market at the CLOSE
After a stop exit the position stays flat until the next signal-driven entry (next bar's open
at the earliest), exactly like vbt.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_column(o, h, l, c, entries, exits, short_entries, short_exits, capital, fee, slippage,
                    sl_stop=None, tp_stop=None, intrabar=True):
    n = len(c)
    equity = np.empty(n)
    pos = 0          # +1 long, -1 short
    units = 0.0      # signed
    e_entry = capital  # equity right after the entry fill (fees deducted)
    px_entry = 0.0     # effective entry price incl. slippage
    cash = capital
    trades, costs = [], 0.0
    t_entry = None

    def enter(direction, px, i):
        nonlocal pos, units, e_entry, px_entry, cash, costs, t_entry
        eff = px * (1 + slippage * direction)
        u = cash / (eff * (1 + fee))
        f = u * eff * fee
        costs += f + u * px * slippage
        pos, units, px_entry, t_entry = direction, direction * u, eff, i
        e_entry = cash - f

    def leave(px, i, reason):
        nonlocal pos, units, cash, costs
        eff = px * (1 - slippage * pos)
        f = abs(units) * eff * fee
        costs += f + abs(units) * px * slippage
        pnl = units * (eff - px_entry) - f
        cash = e_entry + units * (eff - px_entry) - f
        notional = abs(units) * px_entry
        trades.append((t_entry, i, pos, px_entry, eff, None, pnl, pnl / notional if notional else 0.0, reason))
        pos, units = 0, 0.0

    for i in range(n):
        # 1. open: signals
        if pos > 0 and (exits[i] or short_entries[i]) and not entries[i]:
            leave(o[i], i, "signal")
            if short_entries[i] and not short_exits[i]:
                enter(-1, o[i], i)
        elif pos < 0 and (short_exits[i] or entries[i]) and not short_entries[i]:
            leave(o[i], i, "signal")
            if entries[i] and not exits[i]:
                enter(1, o[i], i)
        elif pos == 0:
            if entries[i] and not exits[i] and not short_entries[i]:
                enter(1, o[i], i)
            elif short_entries[i] and not short_exits[i] and not entries[i]:
                enter(-1, o[i], i)
        # 2. intraday stops (measured from the actual fill, slippage excluded)
        if pos != 0 and (sl_stop or tp_stop):
            ref = px_entry / (1 + slippage * pos)
            entered_today = t_entry == i
            if sl_stop:
                lvl = ref * (1 - sl_stop * pos)
                hit = (l[i] <= lvl if pos > 0 else h[i] >= lvl) if intrabar else (c[i] <= lvl if pos > 0 else c[i] >= lvl)
                if hit:
                    gap = (o[i] < lvl if pos > 0 else o[i] > lvl) and not entered_today
                    leave((o[i] if gap else lvl) if intrabar else c[i], i, "stop")
            if pos != 0 and tp_stop:
                lvl = ref * (1 + tp_stop * pos)
                hit = (h[i] >= lvl if pos > 0 else l[i] <= lvl) if intrabar else (c[i] >= lvl if pos > 0 else c[i] <= lvl)
                if hit:
                    gap = (o[i] > lvl if pos > 0 else o[i] < lvl) and not entered_today
                    leave((o[i] if gap else lvl) if intrabar else c[i], i, "take_profit")
        # 3. mark at close
        equity[i] = cash if pos == 0 else e_entry + units * (c[i] - px_entry)
    open_trade = None
    if pos != 0:
        open_trade = (t_entry, n - 1, pos, px_entry, c[-1], None, units * (c[-1] - px_entry),
                      (c[-1] / px_entry - 1) * pos, "open")
    return equity, trades, open_trade, costs


def simulate(panel_trade: dict[str, pd.DataFrame], sig, capital: float, fee: float, slippage: float,
             sl_stop=None, tp_stop=None, intrabar=True):
    """Run each traded column with an equal slice of capital; return equity, positions table, costs, exposure."""
    cols = list(panel_trade["Close"].columns)
    idx = panel_trade["Close"].index
    eq_total = np.zeros(len(idx))
    rows, costs, in_mkt = [], 0.0, np.zeros(len(idx), dtype=bool)
    for col in cols:
        g = lambda f: panel_trade[f][col].to_numpy(dtype=float)
        b = lambda x: x[col].to_numpy(dtype=bool)
        eq, tr, open_tr, cst = simulate_column(g("Open"), g("High"), g("Low"), g("Close"), b(sig.entries), b(sig.exits),
                                               b(sig.short_entries), b(sig.short_exits), capital / len(cols), fee,
                                               slippage, sl_stop, tp_stop, intrabar)
        eq_total += eq
        costs += cst
        for t in tr + ([open_tr] if open_tr else []):
            ei, xi, d, pe, px, _, pnl, ret, why = t
            rows.append({"Column": col, "Entry Timestamp": idx[ei], "Exit Timestamp": idx[xi],
                         "Direction": "Long" if d > 0 else "Short", "Avg Entry Price": pe, "Avg Exit Price": px,
                         "PnL": pnl, "Return": ret, "Exit Reason": why,
                         "Status": "Open" if why == "open" else "Closed"})
            in_mkt[ei:xi + (1 if why == "open" else 0)] = True
    positions = pd.DataFrame(rows)
    return pd.Series(eq_total, index=idx), positions, costs, float(in_mkt.mean())
