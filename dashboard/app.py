"""Portfolio Engine dashboard.   Run:  streamlit run dashboard/app.py"""
from __future__ import annotations

import json
import logging
import sys
import warnings
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard.core import (SPECS, book_drawdown, cost_stress, defaults, expected_band, metrics_frame,  # noqa: E402
                            monthly_returns, paper_book, run_book, sweep, yearly_sharpe)
from engine import PortfolioManager, Sleeve  # noqa: E402
from paper import ledger  # noqa: E402
from paper.config import CAPITAL as PAPER_CAPITAL, SLEEVES as PAPER_SLEEVES, sleeve_capital  # noqa: E402

st.set_page_config(page_title="Portfolio Engine", layout="wide")
ACCENT, GREY = "#2E6FD8", "#9AA0A6"
FMT = {"Total Return %": "{:,.1f}", "CAGR %": "{:,.1f}", "Ann. Vol %": "{:,.1f}", "Sharpe": "{:.2f}",
       "Sortino": "{:.2f}", "Max DD %": "{:,.1f}", "Max DD Days": "{:,.0f}", "Calmar": "{:.2f}", "Trades": "{:,.0f}",
       "Trades/Yr": "{:,.1f}", "Win Rate %": "{:,.1f}", "Exposure %": "{:,.0f}", "Costs Paid": "${:,.0f}"}


# ---------------- cached runs ----------------
@st.cache_resource(ttl=3600, show_spinner="Running backtest…")
def cached_book(selection_json: str, start: str, end: str | None, capital: float, weighting: str,
                weights_json: str, cost_mult: float, max_weight: float | None):
    return run_book(json.loads(selection_json), start, end, capital, weighting, json.loads(weights_json),
                    cost_mult, max_weight)


@st.cache_resource(ttl=3600, show_spinner="Running the paper-traded book over history…")
def cached_paper_config_book(start: str):
    caps = sleeve_capital()
    sleeves = [Sleeve(sl.make(), caps[sl.name] / PAPER_CAPITAL, config=sl.config) for sl in PAPER_SLEEVES]
    return PortfolioManager(sleeves, capital=PAPER_CAPITAL, start=start).run()


@st.cache_data(ttl=3600, show_spinner="Sweeping settings…")
def cached_sweep(key, params_json, p1, v1, start, end, cost_mult, p2, v2):
    return sweep(key, json.loads(params_json), p1, list(v1), start, end, cost_mult, p2, list(v2) if v2 else None)


@st.cache_data(ttl=3600, show_spinner="Stress-testing costs…")
def cached_costs(key, params_json, start, end):
    return cost_stress(key, json.loads(params_json), start, end)


@st.cache_resource(ttl=3600, show_spinner=False)
def cached_single(key, params_json, start, end):
    from dashboard.core import run_sleeve
    return run_sleeve(key, json.loads(params_json), start, end)


# ---------------- chart helpers ----------------
def growth_chart(book, log=True, marker: str | None = None, title="Growth of $1"):
    fig = go.Figure()
    se = book.sleeve_equity()
    for c in se:
        s = se[c] / se[c].iloc[0]
        fig.add_scatter(x=s.index, y=s, name=c, mode="lines", line=dict(width=1.2))
    b = book.equity / book.equity.iloc[0]
    fig.add_scatter(x=b.index, y=b, name="BOOK", mode="lines", line=dict(width=2.6, color=ACCENT))
    if marker:
        fig.add_vline(x=pd.Timestamp(marker), line_dash="dot", line_color=GREY)
        fig.add_annotation(x=pd.Timestamp(marker), y=1, yref="paper", text="paper start", showarrow=False,
                           xanchor="left", font=dict(color=GREY))
    fig.update_layout(title=title, height=420, margin=dict(l=10, r=10, t=50, b=10), hovermode="x unified",
                      legend=dict(orientation="h", y=-0.15))
    if log:
        hi = float(max(se.max().max() / se.iloc[0].min(), b.max()))
        ticks = [v for v in (0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000) if v <= hi * 1.5]
        fig.update_yaxes(type="log", tickvals=ticks, ticktext=[f"{v:g}×" for v in ticks], title="× starting value")
    else:
        fig.update_yaxes(title="× starting value")
    return fig


def dd_chart(equity, title="Book drawdown"):
    d = book_drawdown(equity)
    fig = go.Figure(go.Scatter(x=d.index, y=d, fill="tozeroy", mode="lines", line=dict(color="#C0504D", width=1),
                               name="Drawdown"))
    fig.update_layout(title=title, height=230, margin=dict(l=10, r=10, t=50, b=10), yaxis_title="%")
    return fig


def heatmap(df, title, fmt=".1f", zmid=0, colorscale="RdYlGn"):
    fig = go.Figure(go.Heatmap(z=df.values, x=[str(c) for c in df.columns], y=[str(i) for i in df.index],
                               colorscale=colorscale, zmid=zmid, texttemplate="%{z:" + fmt + "}", hoverongaps=False))
    fig.update_layout(title=title, height=max(260, 34 * len(df) + 90), margin=dict(l=10, r=10, t=50, b=10))
    fig.update_yaxes(autorange="reversed")
    return fig


def style_metrics(df):
    """Format to strings ourselves (Streamlit ignores Styler na_rep and shows 'None')."""
    out = df.copy().astype(object)
    for c in df.columns:
        f = FMT.get(c, "{:,.2f}")
        out[c] = [("–" if v is None or (isinstance(v, float) and np.isnan(v)) else f.format(v)) for v in df[c]]
    return out


def param_inputs(key: str, prefix: str, values: dict | None = None) -> dict:
    out = {}
    for p in SPECS[key].params:
        v = (values or {}).get(p.name, p.default)
        k = f"{prefix}-{key}-{p.name}"
        if p.kind == "int":
            out[p.name] = st.number_input(p.label, int(p.lo), int(p.hi), int(v), int(p.step), key=k)
        elif p.kind == "float":
            out[p.name] = st.number_input(p.label, float(p.lo), float(p.hi), float(v), float(p.step), key=k, format="%.3f")
        elif p.kind == "bool":
            out[p.name] = st.checkbox(p.label, bool(v), key=k)
        else:
            out[p.name] = st.selectbox(p.label, p.choices, p.choices.index(v), key=k)
    return out


# ---------------- header ----------------
meta = ledger.load_meta()
st.title("Portfolio Engine")
st.caption("Backtests use the same engine as paper trading: signals at the close, fills at the next open, "
           "intraday stops, fees + slippage. Data: Yahoo Finance daily bars.")
tab_over, tab_bt, tab_rob, tab_paper = st.tabs(["Overview", "Backtest", "Robustness", "Paper trading"])

# ================= OVERVIEW =================
with tab_over:
    eq_rows = ledger.read_csv("equity")
    pb = paper_book(eq_rows, (meta or {}).get("capital"))
    c1, c2, c3, c4 = st.columns(4)
    if meta:
        start = meta["start"]
        if not pb.empty:
            val = pb["BOOK"].iloc[-1]
            c1.metric("Paper book value", f"${val:,.0f}", f"{100 * (val / PAPER_CAPITAL - 1):+.2f}% since {start}")
        else:
            c1.metric("Paper book value", f"${PAPER_CAPITAL:,.0f}")
            c1.caption(f"Paper trading starts {start}")
        c2.metric("Days paper trading", f"{max(0, (pd.Timestamp.utcnow().tz_localize(None) - pd.Timestamp(start)).days)}")
        c3.metric("Last update (UTC)", meta.get("last_tick_utc", "–")[:16].replace("T", " "))
    else:
        c1.metric("Paper book", "not started")
        st.info("Paper trading hasn't started. Run `python -m paper.tick` once (or wait for the daily cron job).")
    ov_start = c4.date_input("Backtest from", date(2020, 6, 1), key="ov-start")
    book = cached_paper_config_book(str(ov_start))
    m = book.metrics

    st.subheader("Today's orders (executed at the next open)")
    if meta and meta.get("latest"):
        rows = []
        for sl, info in meta["latest"].items():
            for sym, order in (info.get("next_open") or {}).items():
                rows.append({"Strategy": sl, "Symbol": sym, "Position now": (info.get("position") or {}).get(sym, "–"),
                             "Next open": order, "Decided at close of": info.get("last_bar")})
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    else:
        st.write("No orders yet.")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Backtest Sharpe", f"{m['Sharpe']:.2f}")
    k2.metric("Backtest CAGR", f"{m['CAGR %']:.1f}%")
    k3.metric("Max drawdown", f"{m['Max DD %']:.1f}%")
    k4.metric("Ann. volatility", f"{m['Ann. Vol %']:.1f}%")
    st.plotly_chart(growth_chart(book, marker=meta["start"] if meta else None,
                                 title=f"Paper-traded book, backtest from {ov_start}"), use_container_width=True)
    a, b = st.columns([2, 1])
    a.plotly_chart(dd_chart(book.equity), use_container_width=True)
    corr = book.correlation().round(2)
    b.plotly_chart(heatmap(corr, "Strategy correlation (daily returns)", ".2f", 0, "RdBu_r"), use_container_width=True)
    st.dataframe(style_metrics(metrics_frame(book)), use_container_width=True)

# ================= BACKTEST =================
with tab_bt:
    st.subheader("Build a book and backtest it")
    with st.form("bt-form"):
        cols = st.columns(len(SPECS))
        selection, weights = {}, {}
        for col, (key, spec) in zip(cols, SPECS.items()):
            with col:
                on = st.checkbox(spec.title, True, key=f"bt-on-{key}")
                st.caption(spec.blurb)
                w = st.number_input("Weight", 0.0, 10.0, 1.0, 0.5, key=f"bt-w-{key}")
                with st.expander("Settings"):
                    params = param_inputs(key, "bt")
                if on:
                    selection[key], weights[key] = params, w
        r1, r2, r3, r4, r5 = st.columns(5)
        bt_start = r1.date_input("Start", date(2020, 6, 1), key="bt-start")
        bt_end = r2.date_input("End", date.today(), key="bt-end")
        capital = r3.number_input("Capital ($)", 1_000.0, 10_000_000.0, 100_000.0, 1_000.0, key="bt-cap")
        weighting = r4.selectbox("Weighting", ["capital", "inverse_vol"],
                                 format_func=lambda x: {"capital": "Fixed capital split",
                                                        "inverse_vol": "Equal risk (inverse vol, monthly)"}[x])
        cost_mult = r5.number_input("Cost multiplier", 0.0, 5.0, 1.0, 0.5, key="bt-cost",
                                    help="1 = 5 bp fee + 5 bp slippage per side (crypto/equity presets)")
        max_w = st.slider("Max weight per strategy (equal-risk only)", 0.2, 1.0, 0.5, 0.05)
        go_bt = st.form_submit_button("Run backtest", type="primary")
    if not selection:
        st.warning("Pick at least one strategy.")
    elif go_bt or "bt-done" in st.session_state:
        st.session_state["bt-done"] = True
        res = cached_book(json.dumps(selection, sort_keys=True), str(bt_start), str(bt_end), float(capital), weighting,
                          json.dumps(weights, sort_keys=True), float(cost_mult),
                          float(max_w) if weighting == "inverse_vol" else None)
        mt = metrics_frame(res)
        b = mt.loc["BOOK"]
        k = st.columns(5)
        k[0].metric("Book CAGR", f"{b['CAGR %']:.1f}%")
        k[1].metric("Sharpe", f"{b['Sharpe']:.2f}")
        k[2].metric("Max drawdown", f"{b['Max DD %']:.1f}%")
        k[3].metric("End value", f"${res.equity.iloc[-1]:,.0f}")
        k[4].metric("Costs paid", f"${b.get('Costs Paid', 0):,.0f}")
        log = st.toggle("Log scale", True, key="bt-log")
        st.plotly_chart(growth_chart(res, log=log, title="Growth of $1"), use_container_width=True)
        st.plotly_chart(dd_chart(res.equity), use_container_width=True)
        st.dataframe(style_metrics(mt), use_container_width=True)
        mr = monthly_returns(res.equity)
        st.plotly_chart(heatmap(mr, "Book monthly returns (%)"), use_container_width=True)
        a, bcol = st.columns(2)
        a.plotly_chart(heatmap(res.correlation().round(2), "Strategy correlation", ".2f", 0, "RdBu_r"),
                       use_container_width=True)
        contrib = res.contribution().round(1)
        fig = go.Figure(go.Bar(x=contrib.values, y=contrib.index, orientation="h", marker_color=ACCENT,
                               text=[f"{v:+.1f}%" for v in contrib.values], textposition="auto"))
        fig.update_layout(title="P&L contribution (% of starting book)", height=300, margin=dict(l=10, r=10, t=50, b=10))
        bcol.plotly_chart(fig, use_container_width=True)
        if res.weight_history is not None:
            wh = res.weight_history
            fig = go.Figure([go.Scatter(x=wh.index, y=wh[c], stackgroup="w", name=c) for c in wh])
            fig.update_layout(title="Capital weights (equal-risk)", height=280, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("**Trades**")
        pick = st.selectbox("Strategy", list(res.sleeves), key="bt-trades")
        pos = res.sleeves[pick].positions
        show = [c for c in ["Column", "Direction", "Entry Timestamp", "Avg Entry Price", "Exit Timestamp",
                            "Avg Exit Price", "Return", "PnL", "Exit Reason", "Status"] if c in pos.columns]
        tv = pos[show].sort_values("Entry Timestamp", ascending=False).copy()
        if "Return" in tv:
            tv["Return"] = (100 * tv["Return"]).round(2)
            tv = tv.rename(columns={"Return": "Return %"})
        st.dataframe(tv, hide_index=True, use_container_width=True)
        st.download_button("Download equity (CSV)", res.sleeve_equity().assign(BOOK=res.equity).to_csv().encode(),
                           "book_equity.csv", "text/csv")

# ================= ROBUSTNESS =================
with tab_rob:
    st.subheader("Does it hold up?")
    st.caption("Use this to check that results sit on a plateau, not a lucky spike. Picking the best cell here and "
               "trading it is overfitting: the same data chose and tested it.")
    key = st.selectbox("Strategy", list(SPECS), format_func=lambda k: SPECS[k].title, key="rob-key")
    spec = SPECS[key]
    with st.expander("Base settings", expanded=False):
        base = param_inputs(key, "rob")
    c = st.columns(4)
    r_start = c[0].date_input("Start", pd.Timestamp(spec.default_start).date(), key="rob-start")
    r_end = c[1].date_input("End", date.today(), key="rob-end")
    p1 = c[2].selectbox("Sweep setting", spec.sweepable, key="rob-p1",
                        format_func=lambda n: next(p.label for p in spec.params if p.name == n))
    p2 = c[3].selectbox("Second setting (optional)", ["—"] + [x for x in spec.sweepable if x != p1], key="rob-p2",
                        format_func=lambda n: n if n == "—" else next(p.label for p in spec.params if p.name == n))

    def value_range(name, tag):
        p = next(x for x in spec.params if x.name == name)
        cast = int if p.kind == "int" else float
        dlo = max(p.lo, p.default * 0.5) if p.default else p.lo
        dhi = min(p.hi, p.default * 1.6) if p.default else p.hi
        lo, hi = st.slider(f"{p.label} range", cast(p.lo), cast(p.hi), (cast(dlo), cast(dhi)), cast(p.step),
                           key=f"rob-rng-{tag}")
        n = st.number_input(f"Points ({p.label})", 3, 12, 7, key=f"rob-n-{tag}")
        vals = list(np.linspace(lo, hi, int(n))) + [base[name]]          # always include the current setting
        return sorted({int(round(v)) for v in vals}) if p.kind == "int" else sorted({round(float(v), 4) for v in vals})

    rc = st.columns(2)
    with rc[0]:
        v1 = value_range(p1, "1")
    v2 = None
    if p2 != "—":
        with rc[1]:
            v2 = value_range(p2, "2")
    if st.button("Run robustness check", type="primary", key="rob-go") or "rob-done" in st.session_state:
        st.session_state["rob-done"] = True
        bj = json.dumps(base, sort_keys=True)
        grid = cached_sweep(key, bj, p1, tuple(v1), str(r_start), str(r_end), 1.0,
                            None if p2 == "—" else p2, tuple(v2) if v2 else None)
        if p2 == "—":
            fig = go.Figure(go.Scatter(x=grid.index, y=grid["Sharpe"], mode="lines+markers", line=dict(color=ACCENT)))
            fig.add_vline(x=base[p1], line_dash="dot", line_color=GREY)
            lab1 = next(p.label for p in spec.params if p.name == p1)
            fig.update_layout(title=f"Sharpe vs {lab1} (dotted = current setting)", height=360,
                              margin=dict(l=10, r=10, t=50, b=10), xaxis_title=lab1, yaxis_title="Sharpe")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.plotly_chart(heatmap(grid.round(2), f"Sharpe: rows = {p1}, columns = {p2}", ".2f", 0),
                            use_container_width=True)
        share = float((grid.values > 0).mean())
        st.write(f"Share of settings with positive Sharpe: **{share:.0%}** · median Sharpe "
                 f"**{np.nanmedian(grid.values):.2f}**")
        cs = cached_costs(key, bj, str(r_start), str(r_end))
        a, b = st.columns(2)
        fig = go.Figure(go.Scatter(x=cs.index, y=cs["Sharpe"], mode="lines+markers", line=dict(color=ACCENT)))
        fig.update_layout(title="Sharpe vs cost multiplier (1 = base costs)", height=320,
                          margin=dict(l=10, r=10, t=50, b=10), xaxis_title="× costs")
        a.plotly_chart(fig, use_container_width=True)
        single = cached_single(key, bj, str(r_start), str(r_end))
        ys = yearly_sharpe(single.equity)
        fig = go.Figure(go.Bar(x=ys.index.astype(str), y=ys.values,
                               marker_color=[ACCENT if v >= 0 else "#C0504D" for v in ys.values]))
        fig.update_layout(title="Sharpe by calendar year (current settings)", height=320,
                          margin=dict(l=10, r=10, t=50, b=10))
        b.plotly_chart(fig, use_container_width=True)

# ================= PAPER =================
with tab_paper:
    st.subheader("Paper trading")
    if not meta:
        st.info("No paper book yet. Run `python -m paper.tick` (or wait for the daily cron job).")
    else:
        caps = meta.get("capital", {})
        c = st.columns(4)
        c[0].metric("Started", meta["start"])
        c[1].metric("Starting capital", f"${sum(caps.values()):,.0f}")
        c[2].metric("Updates run", meta.get("ticks", 0))
        c[3].metric("Last update (UTC)", meta.get("last_tick_utc", "–")[:16].replace("T", " "))
        drift = {k: v for k, v in (meta.get("drift_pct") or {}).items() if abs(v) > 0.01}
        if drift:
            st.warning("Replaying history no longer matches the recorded ledger (price revisions or a config change): "
                       + ", ".join(f"{k} {v:+.2f}%" for k, v in drift.items()) + ". The recorded ledger is kept as-is.")
        if pb.empty:
            st.info(f"No completed trading days since {meta['start']} yet. The first fills happen at the open on or "
                    f"after {meta['start']}.")
        else:
            caps_all = {**caps, "BOOK": sum(caps.values())}
            fig = go.Figure()
            for col in pb.columns:
                r = 100 * (pb[col] / caps_all.get(col, pb[col].iloc[0]) - 1)
                fig.add_scatter(x=pb.index, y=r, name=col, mode="lines",
                                line=dict(width=2.6 if col == "BOOK" else 1.2, color=ACCENT if col == "BOOK" else None),
                                customdata=pb[col], hovertemplate="%{y:+.2f}% ($%{customdata:,.0f})")
            fig.add_hline(y=0, line_color=GREY, line_width=1)
            fig.update_layout(title="Paper return since start (%)", height=380, margin=dict(l=10, r=10, t=50, b=10),
                              hovermode="x unified", yaxis_ticksuffix="%")
            st.plotly_chart(fig, use_container_width=True)
            days = (pb.index[-1] - pd.Timestamp(meta["start"])).days + 1
            ret = 100 * (pb["BOOK"].iloc[-1] / sum(caps.values()) - 1)
            hist = cached_paper_config_book("2020-06-01")
            band = expected_band(hist.equity.loc[: pd.Timestamp(meta["start"]) - pd.Timedelta(days=1)], days)
            if band:
                st.write(f"After **{days} days** the paper book is **{ret:+.2f}%**. In the backtest (Jun 2020 → paper "
                         f"start), {days}-day returns ranged **{band['p5']:+.1f}%** to **{band['p95']:+.1f}%** "
                         f"(5th–95th percentile), median {band['p50']:+.1f}%.")
        st.markdown("**Positions and next-open orders**")
        rows = []
        for sl, info in (meta.get("latest") or {}).items():
            for sym, order in (info.get("next_open") or {}).items():
                rows.append({"Strategy": sl, "Symbol": sym, "Capital": f"${caps.get(sl, 0):,.0f}",
                             "Equity": f"${info['equity']:,.0f}" if info.get("equity") else "–",
                             "Position now": (info.get("position") or {}).get(sym, "–"), "Next open": order,
                             "Last bar": info.get("last_bar")})
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        f = ledger.read_csv("fills")
        st.markdown("**Fills**")
        if not f.empty:
            f = f.iloc[::-1].copy()
            f["size"] = f["size"].map(lambda v: "" if pd.isna(v) else f"{v:,.4f}")
            f["price"] = f["price"].map(lambda v: f"{v:,.2f}")
        st.dataframe(f if not f.empty else pd.DataFrame({"": ["No fills yet"]}), hide_index=True,
                     use_container_width=True)
        o = ledger.read_csv("orders")
        with st.expander("Decision log (every order decided at a close)"):
            st.dataframe(o.iloc[::-1] if not o.empty else o, hide_index=True, use_container_width=True)
    st.divider()
    st.caption("The daily update runs by cron (GitHub Actions, 00:30 UTC). If it runs on GitHub, `git pull` to see "
               "the latest ledger here. Running it locally too will make the two copies diverge.")
    if st.button("Run update now (locally)", key="paper-tick"):
        with st.spinner("Updating paper book…"):
            out = ledger.tick(PAPER_SLEEVES, sleeve_capital())
        st.cache_resource.clear()
        st.success("Updated: " + ", ".join(f"{k}: {v['status']}" for k, v in out["sleeves"].items()))
        st.rerun()
