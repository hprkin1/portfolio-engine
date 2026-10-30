"""Can the BTC OBV momentum strategy be improved? Keep a change only if it clearly helps.

Periods
  DEV      2015-06-01 .. 2020-05-31   (before the original strategy's own backtest window)
  VAL      2020-06-01 .. 2025-11-04   (the window the original was built on - baseline has home advantage)
  HOLDOUT  2025-11-05 .. today        (looked at once, never used for decisions)

Acceptance rule (declared before running):
  A variant is KEPT only if, vs the baseline, in BOTH DEV and VAL:
    Sharpe >= baseline + 0.05, Max DD not worse by more than 5 pp,
    and Sharpe at 2x costs is also >= baseline (2x costs) + 0.05.
  Simplification (dropping the OBV leg) is kept if Sharpe is within 0.05 of baseline in both.
  Survivors are then combined and the combination must pass the same rule.

Usage: python scripts/research_obv.py
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
from strategies import OBVMomentum  # noqa: E402

PERIODS = {"DEV": ("2015-06-01", "2020-05-31"), "VAL": ("2020-06-01", "2025-11-04"), "HOLDOUT": ("2025-11-05", None)}
OUT = ROOT / "reports" / "obv"
VARIANTS = {
    "0 Baseline (original)": dict(),
    "1 Drop OBV leg (pure momentum)": dict(obv_mode="none"),
    "2 OBV above its 20d mean": dict(obv_mode="sma"),
    "3 Symmetric volume confirmation": dict(symmetric=True),
    "4 Long-only": dict(long_only=True),
    "5 Momentum must hold 3 days": dict(confirm_days=3),
    "6 Multi-horizon momentum (20/40/75/150/300)": dict(obv_mode="none", lookbacks=(20, 40, 75, 150, 300)),
    "7 Vol target 60% (cap 1x)": dict(obv_mode="none", vol_target=0.60),
    "8 2% stop-loss": dict(_sl=0.02),
}
CFG = {1: ExecConfig(rebalance_band=0.10), 2: ExecConfig(costs=CostModel(0.001, 0.001), rebalance_band=0.10)}


def make(prm):
    prm = dict(prm)
    sl = prm.pop("_sl", None)
    s = OBVMomentum(**prm)
    s.sl_stop = sl
    return s


def run(prm, panel, period, mult=1):
    start, end = PERIODS[period]
    p = {k: v.loc[:end] for k, v in panel.items()} if end else panel
    return backtest_strategy(make(prm), 100_000, start, config=CFG[mult], panel=p)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    panel = load_panel(["BTC-USD"], "2014-09-01")
    cols = ["CAGR %", "Sharpe", "Max DD %", "Calmar", "Trades/Yr", "Win Rate %", "Exposure %"]
    res = {}
    for name, prm in VARIANTS.items():
        for per in PERIODS:
            for mult in (1, 2):
                if per == "HOLDOUT" and mult == 2:
                    continue
                res[(name, per, mult)] = run(prm, panel, per, mult).metrics

    def verdict(name, simplification=False):
        base = "0 Baseline (original)"
        checks = []
        for per in ("DEV", "VAL"):
            d_sh = res[(name, per, 1)]["Sharpe"] - res[(base, per, 1)]["Sharpe"]
            d_sh2 = res[(name, per, 2)]["Sharpe"] - res[(base, per, 2)]["Sharpe"]
            d_dd = res[(name, per, 1)]["Max DD %"] - res[(base, per, 1)]["Max DD %"]  # negative = worse
            if simplification:
                checks.append(d_sh >= -0.05 and d_sh2 >= -0.05 and d_dd >= -5)
            else:
                checks.append(d_sh >= 0.05 and d_sh2 >= 0.05 and d_dd >= -5)
        return all(checks)

    L = ["# BTC OBV momentum: improvement research", "",
         f"Generated {pd.Timestamp.now():%Y-%m-%d}. Periods: " +
         ", ".join(f"{k} {a}→{b or 'today'}" for k, (a, b) in PERIODS.items()) + ".", "",
         "Rule: keep a change only if Sharpe improves ≥0.05 in BOTH DEV and VAL (also at 2× costs) and max DD "
         "is not >5 pp worse. Dropping the OBV leg (a simplification) is kept if within 0.05.", ""]
    summary = {}
    for name in VARIANTS:
        row = {}
        for per in PERIODS:
            row[f"{per} Sharpe"] = res[(name, per, 1)]["Sharpe"]
        for per in ("DEV", "VAL"):
            row[f"{per} Sharpe 2×cost"] = res[(name, per, 2)]["Sharpe"]
            row[f"{per} MaxDD"] = res[(name, per, 1)]["Max DD %"]
            row[f"{per} CAGR"] = res[(name, per, 1)]["CAGR %"]
        row["Trades/Yr (VAL)"] = res[(name, "VAL", 1)]["Trades/Yr"]
        row["HOLDOUT Return %"] = res[(name, "HOLDOUT", 1)]["Total Return %"]
        if name.startswith("0"):
            row["Verdict"] = "baseline"
        else:
            row["Verdict"] = "KEEP" if verdict(name, simplification=name.startswith("1")) else "revert"
        summary[name] = row
    st = pd.DataFrame(summary).T
    L += ["## Summary", "", st.to_markdown(floatfmt=".2f"), ""]
    print(st[["DEV Sharpe", "VAL Sharpe", "HOLDOUT Sharpe", "DEV MaxDD", "VAL MaxDD", "Trades/Yr (VAL)", "Verdict"]]
          .to_string(float_format=lambda x: f"{x:.2f}"))

    for per in PERIODS:
        t = pd.DataFrame({n: res[(n, per, 1)] for n in VARIANTS}).T.reindex(columns=cols).astype(float)
        L += [f"## {per} detail (1× costs)", "", t.round(2).to_markdown(), ""]

    # Is mom_period=75 a lucky pick?
    lbs = [20, 30, 45, 60, 75, 90, 120, 150, 200, 250]
    sens = pd.DataFrame({per: {lb: run(dict(mom_period=lb), panel, per).metrics["Sharpe"] for lb in lbs}
                         for per in PERIODS})
    L += ["## Is mom_period = 75 special? (baseline logic, Sharpe by lookback)", "", sens.round(2).to_markdown(), ""]
    print("\nmom_period sensitivity\n", sens.round(2).to_string())

    # Combination of survivors (if any)
    keep = [n for n in VARIANTS if summary[n]["Verdict"] == "KEEP"]
    if len(keep) >= 2:
        combo = {}
        for n in keep:
            combo.update({k: v for k, v in VARIANTS[n].items()})
        VARIANTS["9 Combination of survivors"] = combo
        for per in PERIODS:
            for mult in (1, 2):
                if per == "HOLDOUT" and mult == 2:
                    continue
                res[("9 Combination of survivors", per, mult)] = run(combo, panel, per, mult).metrics
        ok = verdict("9 Combination of survivors")
        L += [f"## Combination of survivors {keep}: {'KEEP' if ok else 'revert'}", "",
              pd.DataFrame({per: res[("9 Combination of survivors", per, 1)] for per in PERIODS}).T
              .reindex(columns=cols).astype(float).round(2).to_markdown(), ""]
        print("combination", combo, "->", "KEEP" if ok else "revert")
    L += ["## Survivors", "", (", ".join(keep) if keep else "None: the original strategy stays as is."), ""]
    (OUT / "README.md").write_text("\n".join(L))
    st.to_csv(OUT / "summary.csv")
    _plot(panel, sens)


def _plot(panel, sens):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), gridspec_kw={"height_ratios": [2, 1]})
    for name in ("0 Baseline (original)", "1 Drop OBV leg (pure momentum)", "6 Multi-horizon momentum (20/40/75/150/300)",
                 "7 Vol target 60% (cap 1x)", "8 2% stop-loss"):
        e = backtest_strategy(make(VARIANTS[name]), 100_000, "2015-06-01", config=CFG[1], panel=panel).equity
        axes[0].plot(e.index, e / 1e5, lw=1.1 if name.startswith("0") else 0.8, label=name,
                     color="black" if name.startswith("0") else None)
    for d in ("2020-06-01", "2025-11-05"):
        axes[0].axvline(pd.Timestamp(d), color="grey", lw=0.7)
    axes[0].set_yscale("log"); axes[0].legend(fontsize=7); axes[0].set_title("Growth of $1 (log). Lines: DEV | VAL | HOLDOUT")
    sens.plot(ax=axes[1], marker="o"); axes[1].axvline(75, color="grey", ls=":"); axes[1].set_xlabel("mom_period")
    axes[1].set_ylabel("Sharpe")
    fig.tight_layout(); fig.savefig(OUT / "obv.png", dpi=110)


if __name__ == "__main__":
    main()
