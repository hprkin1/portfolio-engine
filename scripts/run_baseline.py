"""Re-baseline the three original strategies.

For each strategy, shows how the headline number moves as each fix is applied
(cumulative, in order):
  A  Legacy     - fill on the signal bar's close, stops vs close only, zero costs
  B  +Next open - execute on the next bar's open
  C  +Intrabar  - stops checked against High/Low
  D  +Costs     - fees + slippage (= the fixed engine, REALISTIC)
then the fixed engine on the out-of-sample window (after the strategies were
written/committed, 2025-11-05 onwards), and the combined book.

Optionally (--original PATH) also runs the untouched original classes from
Algorithmic-Trading-Repository/Portfolio for a like-for-like check.

Usage:  python scripts/run_baseline.py [--original ../Algorithmic-Trading-Repository/Portfolio]
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

from engine import LEGACY, REALISTIC, ExecConfig, PortfolioManager, Sleeve, backtest_strategy  # noqa: E402
from strategies import ACMomentum, CorrReversion, OBVMomentum  # noqa: E402

OOS_START = "2025-11-05"   # last commit to the original repo
BOOK_START = "2020-06-01"  # first date all three original strategies were live
STEPS = {
    "A Legacy": LEGACY,
    "B +Next-bar open": ExecConfig("next_open", intrabar_stops=False, costs="zero"),
    "C +Intrabar stops": ExecConfig("next_open", intrabar_stops=True, costs="zero"),
    "D +Costs (FIXED)": REALISTIC,
}
COLS = ["Total Return %", "CAGR %", "Sharpe", "Max DD %", "Calmar", "Trades", "Win Rate %",
        "Exposure %", "Costs Paid", "Benchmark Return %", "Benchmark Sharpe"]
OUT = ROOT / "reports"


def strategies():
    return [(ACMomentum, "2019-01-07"), (OBVMomentum, "2020-06-01"), (CorrReversion, "2016-01-01")]


def fmt(df: pd.DataFrame) -> str:
    def f(v):
        if isinstance(v, (float, np.floating)):
            if np.isnan(v):
                return "–"
            if np.isinf(v):
                return "∞"
            return f"{v:,.0f}" if abs(v) >= 1000 else f"{v:,.2f}"
        return str(v)
    return df.map(f).to_markdown()


def run_original(path: Path) -> dict[str, dict]:
    """Run the untouched original classes and report what they say."""
    sys.path.insert(0, str(path))
    from CorrArb_Class import MeanReversionCorrelationStrategy
    from CTSI_Class import MomentumCryptoACStrategy
    from momentum_obv_strategy import MomentumOBVStrategy
    from Portfolio_Manager import PortfolioManager as OldPM

    out = {}
    runs = [
        ("BTC AC Momentum", MomentumCryptoACStrategy("ac", "BTC-USD"), "2019-01-07", dict(fees=0, sl_stop=0.02)),
        ("BTC OBV Momentum", MomentumOBVStrategy("obv", "BTC-USD", mom_period=75), "2020-06-01", {}),
        ("Oil Corr Reversion", MeanReversionCorrelationStrategy("oil", ["CL=F", "BZ=F"], rolling_window=30,
                                                               entry_corr_low=0.6, exit_corr_high=0.9),
         "2016-01-01", {}),
    ]
    for name, s, start, kw in runs:
        s.load_data(start_date=start)
        pf = s.backtest(init_cash=100_000, **kw)
        st = pf.stats()  # what the notebook printed (averaged if multi-column)
        out[name] = {"Total Return %": st["Total Return [%]"], "Sharpe": st["Sharpe Ratio"],
                     "Max DD %": -st["Max Drawdown [%]"], "Win Rate %": st.get("Win Rate [%]"),
                     "Trades": st.get("Total Trades")}

    # The old combined book, exactly as Main.ipynb ran it
    params = [
        MeanReversionCorrelationStrategy("Oil", ["CL=F", "BZ=F"], rolling_window=30, entry_corr_low=0.6,
                                         exit_corr_high=0.9, start_date="2016-01-01"),
        MomentumCryptoACStrategy("AC", "BTC-USD", start_date="2019-01-07", sl_stop=0.02),
        MomentumOBVStrategy("OBV", "BTC-USD", mom_period=75, start_date="2020-06-01"),
    ]
    pm = OldPM(params)
    pm.run(init_cash_per_strategy=100_000)
    st = pm.get_stats()
    value = pm.combined_portfolio.value()
    out["OLD BOOK (as reported)"] = {"Total Return %": st["Total Return [%]"], "Sharpe": st["Sharpe Ratio"],
                                     "Max DD %": -st["Max Drawdown [%]"], "Win Rate %": st.get("Win Rate [%]"),
                                     "Trades": st.get("Total Trades")}
    out["OLD BOOK (plot start value)"] = {"Total Return %": 100 * (value.sum(axis=1).iloc[0] / pm.total_init_cash - 1)}
    real_cash = 300_000 * value.shape[1]  # each of the N columns actually got the full 300k
    v = value.sum(axis=1)
    out["OLD BOOK (true sum of columns)"] = {"Total Return %": 100 * (v.iloc[-1] / real_cash - 1),
                                             "Max DD %": 100 * (v / v.cummax() - 1).min()}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", type=Path, default=None)
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    lines = ["# Baseline re-run of the original strategies", "",
             f"Generated {pd.Timestamp.now():%Y-%m-%d %H:%M}. Capital $100k per sleeve. "
             f"Out-of-sample window starts {OOS_START}.", ""]

    curves = {}
    for cls, start in strategies():
        rows = {}
        for label, cfg in STEPS.items():
            r = backtest_strategy(cls(), 100_000, start, config=cfg)
            rows[label] = r.metrics
            if label.startswith("D"):
                curves[r.name] = r
        oos = backtest_strategy(cls(), 100_000, OOS_START, config=REALISTIC)
        rows[f"E Fixed, OOS since {OOS_START}"] = oos.metrics
        df = pd.DataFrame(rows).T.reindex(columns=COLS)
        name = cls().name
        lines += [f"## {name}  (from {start})", "", fmt(df), ""]
        df.to_csv(OUT / f"baseline_{name.replace(' ', '_').lower()}.csv")
        print(name); print(df[["Total Return %", "CAGR %", "Sharpe", "Max DD %", "Trades"]].round(2), "\n")

    # Combined book, equal weight, common start
    for label, start in [("full", BOOK_START), ("OOS", OOS_START)]:
        book = PortfolioManager([Sleeve(c()) for c, _ in strategies()], capital=300_000,
                                start=start, config=REALISTIC).run()
        t = book.metrics_table().T.reindex(columns=COLS)
        lines += [f"## Combined book ({label}, from {start}, equal weight, $300k)", "", fmt(t), "",
                  "Sleeve return correlation:", "", book.correlation().round(2).to_markdown(), "",
                  "P&L contribution (% of book):", "", book.contribution().round(2).to_frame("%").to_markdown(), ""]
        print(f"BOOK {label}"); print(t[["Total Return %", "CAGR %", "Sharpe", "Max DD %"]].round(2), "\n")
        if label == "full":
            full_book = book

    if args.original:
        orig = pd.DataFrame(run_original(args.original)).T
        lines += ["## Original code, run unchanged on today's data", "", fmt(orig), ""]
        print("ORIGINAL"); print(orig.round(2))

    (OUT / "baseline.md").write_text("\n".join(lines))
    _plot(full_book, OUT / "baseline_book.png")
    print(f"\nWrote {OUT/'baseline.md'}")


def _plot(book, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    se = book.sleeve_equity()
    for c in se:
        axes[0].plot(se.index, se[c] / se[c].iloc[0], label=c, lw=1)
    axes[0].plot(book.equity.index, book.equity / book.equity.iloc[0], label="BOOK", lw=2, color="black")
    axes[0].set_yscale("log"); axes[0].legend(); axes[0].set_title("Fixed engine: growth of $1 (log)")
    dd = book.equity / book.equity.cummax() - 1
    axes[1].fill_between(dd.index, dd * 100, 0, color="tab:red", alpha=0.4); axes[1].set_ylabel("Book DD %")
    fig.tight_layout(); fig.savefig(path, dpi=110)


if __name__ == "__main__":
    main()
