"""Outright oil trend/carry research on tradeable ETFs (USO = WTI, BNO = Brent).

Protocol (declared before looking at results):
  * Fixed candidate list with literature-default parameters (no grid search for the headline).
  * In-sample 2012-01-01 .. 2021-12-31. Selection rule: highest in-sample Sharpe, excluding buy & hold.
  * Out-of-sample 2022-01-01 .. today, reported for EVERY candidate (no hiding losers).
  * Sensitivity of the selected rule to trend/carry lookbacks: in-sample heatmap first,
    out-of-sample heatmap shown alongside so a lucky parameter is visible.

Usage: python scripts/research_oil_trend_carry.py
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

from engine import CostModel, ExecConfig, backtest_strategy  # noqa: E402
from engine.data import load_panel  # noqa: E402
from strategies import OilTrendCarry  # noqa: E402

IS_START, IS_END, OOS_START = "2012-01-01", "2021-12-31", "2022-01-01"
OUT = ROOT / "reports" / "oil"
CFG = ExecConfig(rebalance_band=0.10)
VT = dict(vol_target=0.20, max_lev=1.0)
CANDIDATES = {
    "1 Buy & hold": dict(rule="hold"),
    "2 Trend L/S": dict(rule="trend"),
    "3 Trend long-only": dict(rule="trend", long_only=True),
    "4 Carry L/S": dict(rule="carry"),
    "5 Carry long-only": dict(rule="carry", long_only=True),
    "6 Trend+Carry L/S": dict(rule="both"),
    "7 Trend+Carry L/S, vol-tgt": dict(rule="both", **VT),
    "8 Trend+Carry long-only, vol-tgt": dict(rule="both", long_only=True, **VT),
    "9 Trend+Carry+Spread filter, vol-tgt": dict(rule="both", spread_filter=True, **VT),
}
COLS = ["Total Return %", "CAGR %", "Ann. Vol %", "Sharpe", "Max DD %", "Calmar", "Trades/Yr", "Exposure %"]
BORROW = 0.03  # assumed annual cost of shorting an oil ETF (not in the engine)


def run(params, etf, panel, start, end=None, cfg=CFG):
    p = {k: v.loc[:end] for k, v in panel.items()} if end else panel
    return backtest_strategy(OilTrendCarry(symbols=[etf], **params), 100_000, start, config=cfg, panel=p)


def short_share(r):
    w = r.signals.target.iloc[:, 0].ffill().fillna(0)
    return float((w < 0).mean())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    panels = {etf: load_panel([etf, "CL=F", "BZ=F"], "2010-01-01") for etf in ("USO", "BNO")}
    L = ["# Oil trend + carry (new thesis)", "",
         f"Generated {pd.Timestamp.now():%Y-%m-%d}. Tradeable ETFs only (USO = WTI, BNO = Brent); their prices "
         "include roll yield and fund fees, so there are no roll artefacts. Costs 5 bp fee + 5 bp slippage per side; "
         f"vol-targeted variants rebalance only when the weight moves by >0.10. In-sample {IS_START}→{IS_END}, "
         f"out-of-sample {OOS_START}→today.", ""]
    tables, runs = {}, {}
    for etf, panel in panels.items():
        for per, (s, e) in {"IS": (IS_START, IS_END), "OOS": (OOS_START, None)}.items():
            rows = {}
            for name, prm in CANDIDATES.items():
                r = run(prm, etf, panel, s, e)
                m = dict(r.metrics)
                sh = short_share(r)
                m["Short %"] = 100 * sh
                m["Sharpe after borrow"] = (r.returns.mean() * 252 - sh * BORROW) / (r.returns.std() * np.sqrt(252))
                rows[name] = m
                runs[(etf, per, name)] = r
            tables[(etf, per)] = pd.DataFrame(rows).T.reindex(columns=COLS + ["Short %", "Sharpe after borrow"])

    # Selection on in-sample only (pooled across both ETFs = average Sharpe)
    is_sh = (tables[("USO", "IS")]["Sharpe"] + tables[("BNO", "IS")]["Sharpe"]) / 2
    pick = is_sh.drop("1 Buy & hold").astype(float).idxmax()
    L += [f"**Selection rule result (in-sample avg Sharpe across USO+BNO): `{pick}`**", ""]
    for etf in panels:
        for per in ("IS", "OOS"):
            L += [f"## {etf} {per}", "", tables[(etf, per)].astype(float).round(2).to_markdown(), ""]
            print(f"\n{etf} {per}")
            print(tables[(etf, per)][["CAGR %", "Sharpe", "Max DD %", "Short %", "Sharpe after borrow"]].astype(float).round(2))
    print("\nSELECTED:", pick)

    # Cost sensitivity, selected
    L += ["## Cost sensitivity (selected, OOS)", ""]
    ct = {}
    for etf, panel in panels.items():
        for mult in (1, 2, 3):
            cfg = ExecConfig(costs=CostModel(0.0005 * mult, 0.0005 * mult), rebalance_band=0.10)
            ct[f"{etf} costs×{mult}"] = run(CANDIDATES[pick], etf, panel, OOS_START, cfg=cfg).metrics
    L += [pd.DataFrame(ct).T.reindex(columns=COLS).astype(float).round(2).to_markdown(), ""]

    # Lookback sensitivity heatmaps for the selected rule
    tl, cl = [63, 126, 189, 252, 378], [21, 42, 63, 126]
    L += ["## Lookback sensitivity of the selected rule (Sharpe; rows = trend_lb, cols = carry_lb)", ""]
    base = {k: v for k, v in CANDIDATES[pick].items() if k not in ("trend_lb", "carry_lb")}
    for etf, panel in panels.items():
        for per, (s, e) in {"IS": (IS_START, IS_END), "OOS": (OOS_START, None)}.items():
            h = pd.DataFrame(index=tl, columns=cl, dtype=float)
            for a in tl:
                for b in cl:
                    h.loc[a, b] = run({**base, "trend_lb": a, "carry_lb": b}, etf, panel, s, e).metrics["Sharpe"]
            L += [f"**{etf} {per}**", "", h.round(2).to_markdown(), ""]
            print(f"{etf} {per} lookback grid: median {np.nanmedian(h.values):.2f}, share>0 {(h.values>0).mean():.0%}")

    # By-year and current state
    L += ["## Selected strategy: return by year (%)", ""]
    yr = {}
    for etf, panel in panels.items():
        full = run(CANDIDATES[pick], etf, panel, IS_START)
        bh = run(CANDIDATES["1 Buy & hold"], etf, panel, IS_START)
        for lab, rr in ((etf, full), (f"{etf} buy&hold", bh)):
            e = rr.equity.resample("YE").last()
            yr[lab] = 100 * (e / e.shift(1).fillna(100_000) - 1)
        runs[(etf, "FULL", pick)] = full
        runs[(etf, "FULL", "hold")] = bh
    yt = pd.DataFrame(yr); yt.index = yt.index.year
    L += [yt.round(1).to_markdown(), ""]

    L += ["## Signal state today", ""]
    for etf in panels:
        ind = runs[(etf, "FULL", pick)].indicators.iloc[-1]
        w = runs[(etf, "FULL", pick)].signals.target.iloc[-1, 0]
        L.append(f"- **{etf}**: 12m trend {100*ind['trend']:.1f}% (log), carry {100*ind['carry']:.1f}%/yr "
                 f"({'backwardation' if ind['carry']>0 else 'contango'}), 20d vol {100*ind['vol']:.0f}%, "
                 f"Brent−WTI ${ind['bw_spread']:.2f} vs 1y median ${ind['bw_spread_med']:.2f} → target weight {w:+.2f}")
        print(etf, "today:", {k: round(float(ind[k]), 3) for k in ind.index}, "w", round(w, 2))
    (OUT / "trend_carry.md").write_text("\n".join(L))
    _plot(runs, pick)


def _plot(runs, pick):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True, gridspec_kw={"height_ratios": [2.2, 1, 1]})
    for etf, col in (("USO", "tab:blue"), ("BNO", "tab:orange")):
        s = runs[(etf, "FULL", pick)]
        b = runs[(etf, "FULL", "hold")]
        axes[0].plot(s.equity.index, s.equity / 1e5, color=col, label=f"{etf} {pick[2:]}")
        axes[0].plot(b.equity.index, b.equity / 1e5, color=col, ls=":", lw=1, label=f"{etf} buy & hold")
    axes[0].set_yscale("log"); axes[0].axvline(pd.Timestamp(OOS_START), color="grey", lw=0.8)
    axes[0].legend(fontsize=8); axes[0].set_title("Growth of $1 (log). Grey line = start of out-of-sample")
    s = runs[("BNO", "FULL", pick)]
    axes[1].plot(s.signals.target.index, s.signals.target.iloc[:, 0], lw=0.8, color="tab:orange")
    axes[1].set_ylabel("BNO weight")
    axes[2].plot(s.indicators.index, 100 * s.indicators["carry"], lw=0.7, color="black")
    axes[2].axhline(0, lw=0.5); axes[2].set_ylabel("carry proxy %/yr")
    fig.tight_layout(); fig.savefig(OUT / "trend_carry.png", dpi=110)


if __name__ == "__main__":
    main()
