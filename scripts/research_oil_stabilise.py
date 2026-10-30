"""Stabilise the oil trend/carry/spread strategy, then test risk-based book weighting.

Part A - stabilisers (declared before running):
  grid  confirm_days in {1,3,5,10,20} x spread_smooth in {1,5,10}, on the selected rule
        (#9: trend+carry, spread filter, 20% vol target), USO and BNO.
  selection: highest in-sample (2012-21) Sharpe at 2x costs, averaged over USO+BNO,
        scored as the median of the cell and its grid neighbours (prefers plateaus).
  then: out-of-sample 2022+ for the full grid (nothing hidden), costs x1/x2/x3.

Part B - book weighting, BTC sleeves + stabilised BNO oil sleeve:
  capital (equal $) vs inverse-vol (equal risk), with and without a 50% cap per sleeve.

Usage: python scripts/research_oil_stabilise.py
"""
from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

from engine import CostModel, ExecConfig, PortfolioManager, Sleeve, backtest_strategy  # noqa: E402
from engine.data import load_panel  # noqa: E402
from strategies import ACMomentum, OBVMomentum, OilTrendCarry  # noqa: E402

IS_START, IS_END, OOS_START = "2012-01-01", "2021-12-31", "2022-01-01"
OUT = ROOT / "reports" / "oil"
BASE = dict(rule="both", spread_filter=True, vol_target=0.20, max_lev=1.0)
CONFIRM, SMOOTH = [1, 3, 5, 10, 20], [1, 5, 10]


def cfg(mult=1):
    return ExecConfig(costs=CostModel(0.0005 * mult, 0.0005 * mult), rebalance_band=0.10)


def run(params, etf, panel, start, end=None, mult=1):
    p = {k: v.loc[:end] for k, v in panel.items()} if end else panel
    return backtest_strategy(OilTrendCarry(symbols=[etf], **{**BASE, **params}), 100_000, start,
                             config=cfg(mult), panel=p)


def grid(panels, start, end, mult):
    out = {}
    for etf, panel in panels.items():
        h = {}
        for c in CONFIRM:
            for s in SMOOTH:
                m = run(dict(confirm_days=c, spread_smooth=s), etf, panel, start, end, mult).metrics
                h[(c, s)] = (m["Sharpe"], m["Trades/Yr"], m["CAGR %"], m["Max DD %"])
        out[etf] = h
    return out


def to_frame(h, i):
    return pd.DataFrame({s: {c: h[(c, s)][i] for c in CONFIRM} for s in SMOOTH})


def neighbourhood_median(df):
    out = df.copy()
    for a, c in enumerate(df.index):
        for b, s in enumerate(df.columns):
            vals = [df.iloc[a, b]] + [df.iloc[x, y] for x, y in ((a - 1, b), (a + 1, b), (a, b - 1), (a, b + 1))
                                      if 0 <= x < len(df.index) and 0 <= y < len(df.columns)]
            out.iloc[a, b] = np.median(vals)
    return out


def main():
    panels = {etf: load_panel([etf, "CL=F", "BZ=F"], "2010-01-01") for etf in ("USO", "BNO")}
    L = ["# Stabilising the oil strategy + risk-based book weights", "",
         f"Generated {pd.Timestamp.now():%Y-%m-%d}. Rows = confirm_days, columns = spread_smooth. "
         f"In-sample {IS_START}→{IS_END}; out-of-sample {OOS_START}→today.", ""]

    # ---------------- Part A ----------------
    g_is2 = grid(panels, IS_START, IS_END, 2)
    g_is1 = grid(panels, IS_START, IS_END, 1)
    score = sum(neighbourhood_median(to_frame(g_is2[e], 0)) for e in panels) / len(panels)
    c_sel, s_sel = score.stack().astype(float).idxmax()
    pick = dict(confirm_days=int(c_sel), spread_smooth=int(s_sel))
    L += ["## A. In-sample (selection data)", "",
          "Selection score = neighbourhood-median Sharpe at 2× costs, averaged over USO+BNO:", "",
          score.round(2).to_markdown(), "", f"**Selected: `{pick}`** (baseline = confirm 1, smooth 1)", ""]
    for e in panels:
        L += [f"**{e} IS Sharpe (1× costs)**", "", to_frame(g_is1[e], 0).round(2).to_markdown(), "",
              f"**{e} IS Sharpe (2× costs)**", "", to_frame(g_is2[e], 0).round(2).to_markdown(), "",
              f"**{e} IS trades/yr**", "", to_frame(g_is1[e], 1).round(1).to_markdown(), ""]
    print("selected", pick)

    g_oos1 = grid(panels, OOS_START, None, 1)
    g_oos2 = grid(panels, OOS_START, None, 2)
    L += ["## A. Out-of-sample (looked at once, after selection)", ""]
    for e in panels:
        L += [f"**{e} OOS Sharpe (1× costs)**", "", to_frame(g_oos1[e], 0).round(2).to_markdown(), "",
              f"**{e} OOS Sharpe (2× costs)**", "", to_frame(g_oos2[e], 0).round(2).to_markdown(), ""]

    cols = ["CAGR %", "Ann. Vol %", "Sharpe", "Max DD %", "Calmar", "Trades/Yr", "Exposure %"]
    rows = {}
    for e, panel in panels.items():
        for lab, prm in (("before", dict(confirm_days=1, spread_smooth=1)), ("after", pick)):
            for per, (s, en) in {"IS": (IS_START, IS_END), "OOS": (OOS_START, None)}.items():
                for mult in (1, 2, 3):
                    if per == "IS" and mult == 3:
                        continue
                    rows[f"{e} {per} {lab} costs×{mult}"] = run(prm, e, panel, s, en, mult).metrics
    comp = pd.DataFrame(rows).T.reindex(columns=cols).astype(float)
    L += ["## A. Before vs after stabilising", "", comp.round(2).to_markdown(), ""]
    print(comp[["Sharpe", "CAGR %", "Max DD %", "Trades/Yr"]].round(2))

    # ---------------- Part B ----------------
    oil = lambda: OilTrendCarry(symbols=["BNO"], name="Oil Trend/Carry BNO", **{**BASE, **pick})
    L += ["## B. Book weighting (BTC OBV + BTC AC + stabilised BNO oil)", "",
          "capital = equal dollars, never rebalanced. inverse_vol = equal risk budget per sleeve, capital ∝ "
          "1/trailing 252-day vol (floor 5%), rebalanced month-end, 10 bp charged on capital moved.", ""]
    bcols = ["CAGR %", "Ann. Vol %", "Sharpe", "Sortino", "Max DD %", "Calmar", "Max DD Days"]
    books = {}
    for start in ("2020-06-01", "2022-01-01"):
        rows = {}
        specs = {
            "BTC only, capital": ([Sleeve(OBVMomentum()), Sleeve(ACMomentum())], {}),
            "BTC only, inverse-vol": ([Sleeve(OBVMomentum()), Sleeve(ACMomentum())], dict(weighting="inverse_vol")),
            "BTC + oil, capital": ([Sleeve(OBVMomentum()), Sleeve(ACMomentum()), Sleeve(oil())], {}),
            "BTC + oil, inverse-vol": ([Sleeve(OBVMomentum()), Sleeve(ACMomentum()), Sleeve(oil())],
                                       dict(weighting="inverse_vol")),
            "BTC + oil, inverse-vol, cap 50%": ([Sleeve(OBVMomentum()), Sleeve(ACMomentum()), Sleeve(oil())],
                                                dict(weighting="inverse_vol", max_weight=0.5)),
        }
        for lab, (sl, kw) in specs.items():
            b = PortfolioManager(sl, capital=300_000, start=start, config=cfg(1), **kw).run()
            rows[lab] = b.metrics
            books[(start, lab)] = b
        t = pd.DataFrame(rows).T
        L += [f"**From {start}**", "", t.reindex(columns=bcols).astype(float).round(2).to_markdown(), ""]
        print(f"\nBOOK from {start}"); print(t.reindex(columns=bcols).astype(float).round(2))
        for lab in ("BTC + oil, inverse-vol", "BTC + oil, inverse-vol, cap 50%"):
            b = books[(start, lab)]
            L += [f"- {lab}: average capital weights {b.metrics['Avg Weights']}; latest "
                  f"{b.weight_history.iloc[-1].round(2).to_dict()}; P&L contribution % of book "
                  f"{b.contribution().round(1).to_dict()}"]
        L.append("")
    b = books[("2020-06-01", "BTC + oil, inverse-vol")]
    L += ["Sleeve return correlation (from 2020-06):", "", b.correlation().round(2).to_markdown(), ""]
    (OUT / "stabilise.md").write_text("\n".join(L))
    _plot(books, panels, pick)


def _plot(books, panels, pick):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), gridspec_kw={"height_ratios": [1, 1.6, 1]})
    a = run(dict(confirm_days=1, spread_smooth=1), "BNO", panels["BNO"], IS_START)
    b = run(pick, "BNO", panels["BNO"], IS_START)
    axes[0].plot(a.signals.target.index, a.signals.target.iloc[:, 0], lw=0.6, color="lightgrey", label="before")
    axes[0].plot(b.signals.target.index, b.signals.target.iloc[:, 0], lw=0.9, color="tab:orange",
                 label=f"after {pick}")
    axes[0].set_title("BNO target weight: before vs after stabilising"); axes[0].legend(fontsize=8)
    for lab, col in (("BTC only, capital", "grey"), ("BTC + oil, capital", "tab:blue"),
                     ("BTC + oil, inverse-vol", "tab:green"), ("BTC + oil, inverse-vol, cap 50%", "tab:purple")):
        e = books[("2020-06-01", lab)].equity
        axes[1].plot(e.index, e / e.iloc[0], label=lab, color=col, lw=1.2)
    axes[1].set_yscale("log"); axes[1].legend(fontsize=8); axes[1].set_title("Book growth of $1 from 2020-06 (log)")
    wh = books[("2020-06-01", "BTC + oil, inverse-vol")].weight_history
    axes[2].stackplot(wh.index, wh.T.values, labels=wh.columns, alpha=0.8)
    axes[2].legend(fontsize=7, loc="upper left"); axes[2].set_title("Inverse-vol capital weights (month-end)")
    fig.tight_layout(); fig.savefig(OUT / "stabilise.png", dpi=110)


if __name__ == "__main__":
    main()
