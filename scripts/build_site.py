"""Build the static "live paper trading" page into site/index.html.

Run after the daily paper tick (the GitHub Action does this). Netlify publishes the site/ folder.
Look and links are set in site_config.json (accent colour, font, link back to the personal website).

Usage: python scripts/build_site.py [--out site]
"""
from __future__ import annotations

import argparse
import html
import json
import logging
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402

from dashboard.core import expected_band, paper_book  # noqa: E402
from engine import PortfolioManager, Sleeve  # noqa: E402
from paper import ledger  # noqa: E402
from paper.config import CAPITAL, SLEEVES, sleeve_capital  # noqa: E402

PLOTLY_JS = "https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js"
NICE = {"BTC OBV Momentum": "Bitcoin OBV momentum", "BTC AC Momentum": "Bitcoin AC momentum",
        "Oil Trend/Carry BNO": "Oil trend + carry (BNO)", "BOOK": "Portfolio"}
T: dict = {}            # theme, from site_config.json (set in build)
COLOURS: dict = {}


def esc(x) -> str:
    return html.escape(str(x))


def fig_html(fig, div_id: str) -> str:
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family=T["mono"], size=12, color=T["text_secondary"]),
                      margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified",
                      hoverlabel=dict(bgcolor=T["card_hover"], bordercolor=T["border_strong"],
                                      font=dict(family=T["mono"], color=T["text"])),
                      legend=dict(orientation="h", y=-0.18, x=0, font=dict(family=T["sans"], size=13)))
    fig.update_xaxes(showgrid=False, linecolor=T["border_strong"])
    fig.update_yaxes(gridcolor=T["border"], zeroline=False)
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=div_id,
                       config={"displayModeBar": False, "responsive": True})


def backtest_book(start: str):
    caps = sleeve_capital()
    sleeves = [Sleeve(sl.make(), caps[sl.name] / CAPITAL, config=sl.config) for sl in SLEEVES]
    return PortfolioManager(sleeves, capital=CAPITAL, start=start).run()


def build(out: Path, cfg: dict) -> Path:
    meta = ledger.load_meta() or {}
    eq_rows = ledger.read_csv("equity")
    fills = ledger.read_csv("fills")
    caps = meta.get("capital") or sleeve_capital()
    pb = paper_book(eq_rows, caps)
    start = meta.get("start", "–")
    now = datetime.now(timezone.utc)
    T.clear(); T.update(cfg["theme"])
    COLOURS.clear(); COLOURS.update(T["series"])
    accent = T["accent"]

    # ---- paper numbers ----
    if not pb.empty:
        value = float(pb["BOOK"].iloc[-1])
        ret = 100 * (value / sum(caps.values()) - 1)
        days = (pb.index[-1] - pd.Timestamp(start)).days + 1
        as_of = pb.index[-1].date().isoformat()
    else:
        value, ret, days, as_of = sum(caps.values()), 0.0, 0, "–"

    # ---- backtest context ----
    bt = backtest_book(cfg["backtest_start"])
    hist = bt.equity.loc[: pd.Timestamp(start) - pd.Timedelta(days=1)] if start != "–" else bt.equity
    band = expected_band(hist, days) if days >= 5 else {}
    m = bt.metrics_table().T

    # ---- chart: paper return since start ----
    paper_chart = ""
    if not pb.empty:
        fig = go.Figure()
        for col in [c for c in pb.columns if c != "BOOK"]:
            r = 100 * (pb[col] / caps.get(col, pb[col].iloc[0]) - 1)
            fig.add_scatter(x=pb.index, y=r, name=NICE.get(col, col), mode="lines+markers" if len(pb) < 15 else "lines",
                            line=dict(width=1.6, color=COLOURS.get(col)), hovertemplate="%{y:+.2f}%")
        r = 100 * (pb["BOOK"] / sum(caps.values()) - 1)
        fig.add_scatter(x=pb.index, y=r, name="Portfolio", mode="lines+markers" if len(pb) < 15 else "lines",
                        line=dict(width=3.2, color=accent), hovertemplate="%{y:+.2f}%")
        fig.add_hline(y=0, line_color=T["border_strong"], line_width=1)
        fig.update_layout(height=340)
        fig.update_yaxes(ticksuffix="%")
        fig.update_xaxes(tickformat="%d %b", dtick=86_400_000 if len(pb) <= 21 else None)
        paper_chart = fig_html(fig, "paper-chart")

    # ---- chart: backtest history with paper start ----
    se = bt.sleeve_equity()
    fig = go.Figure()
    for c in se:
        s = se[c] / se[c].iloc[0]
        fig.add_scatter(x=s.index, y=s, name=NICE.get(c, c), mode="lines", line=dict(width=1.3, color=COLOURS.get(c)),
                        hovertemplate="%{y:.2f}×")
    b = bt.equity / bt.equity.iloc[0]
    fig.add_scatter(x=b.index, y=b, name="Portfolio", mode="lines", line=dict(width=2.8, color=accent),
                    hovertemplate="%{y:.2f}×")
    if start != "–":
        fig.add_vline(x=pd.Timestamp(start), line_dash="dot", line_color=T["text_muted"])
        fig.add_annotation(x=pd.Timestamp(start), y=1, yref="paper", text="paper trading starts", showarrow=False,
                           xanchor="right", font=dict(size=11, color=T["text_muted"]))
    ticks = [v for v in (0.5, 1, 2, 5, 10, 20, 50, 100) if v <= float(max(se.max().max() / se.iloc[0].min(), b.max())) * 1.5]
    fig.update_yaxes(type="log", tickvals=ticks, ticktext=[f"{v:g}×" for v in ticks])
    fig.update_layout(height=360)
    bt_chart = fig_html(fig, "backtest-chart")

    # ---- tables ----
    pos_rows = ""
    for name, info in (meta.get("latest") or {}).items():
        for sym, order in (info.get("next_open") or {}).items():
            eqv = info.get("equity")
            pos_rows += (f"<tr><td>{esc(NICE.get(name, name))}</td><td>{esc(sym)}</td>"
                         f"<td>{esc((info.get('position') or {}).get(sym, '–'))}</td><td>{esc(order)}</td>"
                         f"<td class='num'>{'$' + format(eqv, ',.0f') if eqv else '–'}</td></tr>")
    fill_rows = ""
    if not fills.empty:
        for _, f in fills.iloc[::-1].head(15).iterrows():
            fill_rows += (f"<tr><td>{esc(f['date'])}</td><td>{esc(NICE.get(f['sleeve'], f['sleeve']))}</td>"
                          f"<td>{esc(f['symbol'])}</td><td>{esc(f['action'])}</td>"
                          f"<td class='num'>{float(f['price']):,.2f}</td><td>{esc(f['reason'])}</td></tr>")
    met_rows = ""
    for name, r in m.iterrows():
        met_rows += (f"<tr><td>{esc(NICE.get(name, name))}</td><td class='num'>{r['Sharpe']:.2f}</td>"
                     f"<td class='num'>{r['CAGR %']:.0f}%</td><td class='num'>{r['Max DD %']:.0f}%</td></tr>")

    if band:
        inside = band["p5"] <= ret <= band["p95"]
        band_txt = (f"After <b>{days} days</b> the paper portfolio is <b>{ret:+.2f}%</b>. In the backtest, {days}-day "
                    f"returns ranged from <b>{band['p5']:+.1f}%</b> to <b>{band['p95']:+.1f}%</b> (5th–95th percentile; "
                    f"median {band['p50']:+.1f}%), so this is <b>{'within' if inside else 'outside'}</b> the usual range.")
    else:
        band_txt = ("It's too early to compare: the comparison with the backtest's normal range appears after "
                    "5 days of paper trading.")

    links = []
    brand = (f"<a class='brand' href='{esc(cfg['back_link_url'])}'>← {esc(cfg['back_link_label'])}</a>"
             if cfg.get("back_link_url") else "<span></span>")
    if cfg.get("writeup_url"):
        links.append(f"<a href='{esc(cfg['writeup_url'])}'>Project write-up</a>")
    links.append(f"<a href='{esc(cfg['github_url'])}'>Code on GitHub ↗</a>")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(cfg['title'])}</title>
<meta name="description" content="Daily-updated paper trading results of {esc(cfg['owner'])}'s Portfolio Engine: two Bitcoin momentum strategies and an oil trend strategy.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{T['fonts_css']}" rel="stylesheet">
<script src="{PLOTLY_JS}"></script>
<style>
  :root {{ --bg: {T['bg']}; --card: {T['card']}; --card-hover: {T['card_hover']}; --border: {T['border']};
          --border-strong: {T['border_strong']}; --text: {T['text']}; --text-2: {T['text_secondary']};
          --muted: {T['text_muted']}; --accent: {accent}; --accent-soft: {T['accent_soft']}; --good: {T['good']};
          --bad: {T['bad']}; --serif: {T['serif']}; --sans: {T['sans']}; --mono: {T['mono']}; }}
  * {{ box-sizing: border-box; }}
  html {{ background: var(--bg); }}
  body {{ margin: 0; background: var(--bg); color: var(--text); font-family: var(--sans); line-height: 1.6;
          -webkit-font-smoothing: antialiased; }}
  .wrap {{ max-width: 1040px; margin: 0 auto; padding: 28px 22px 72px; }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ color: {T.get('accent_strong', accent)}; text-decoration: underline; }}
  nav {{ display: flex; justify-content: space-between; align-items: center; gap: 18px; flex-wrap: wrap;
         font-family: var(--mono); font-size: 12px; letter-spacing: .04em; text-transform: uppercase;
         padding-bottom: 18px; border-bottom: 1px solid var(--border); margin-bottom: 40px; }}
  nav .links {{ display: flex; gap: 22px; flex-wrap: wrap; }}
  nav .brand {{ color: var(--text-2); }}
  .eyebrow {{ font-family: var(--mono); font-size: 12px; letter-spacing: .08em; text-transform: uppercase;
              color: var(--accent); display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }}
  .live {{ display: inline-flex; align-items: center; gap: 6px; color: var(--good); background: rgba(143,179,140,.14);
           border-radius: 999px; padding: 3px 10px; font-size: 11px; }}
  .live .dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--good); }}
  h1 {{ font-family: var(--serif); font-weight: 400; font-size: clamp(34px, 5vw, 54px); line-height: 1.08;
        margin: 0 0 16px; letter-spacing: -0.02em; }}
  h2 {{ font-family: var(--serif); font-weight: 400; font-size: 28px; margin: 56px 0 8px; letter-spacing: -0.01em; }}
  .lede {{ color: var(--text-2); font-size: 18px; max-width: 760px; margin: 0; }}
  .stamp {{ color: var(--muted); font-family: var(--mono); font-size: 12px; margin-top: 16px; }}
  .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 34px; }}
  .kpi {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 18px 20px; }}
  .kpi .label {{ font-family: var(--mono); font-size: 11px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }}
  .kpi .value {{ font-family: var(--serif); font-size: 32px; margin-top: 6px; letter-spacing: -0.01em; }}
  .pos {{ color: var(--good); }} .neg {{ color: var(--bad); }}
  .note {{ color: var(--text-2); font-size: 15.5px; max-width: 780px; margin: 0 0 16px; }}
  .note b {{ color: var(--text); font-weight: 600; }}
  .table-wrap {{ overflow-x: auto; border: 1px solid var(--border); border-radius: 14px; background: var(--card); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  th, td {{ text-align: left; padding: 12px 16px; border-bottom: 1px solid var(--border); white-space: nowrap; }}
  th {{ font-family: var(--mono); font-weight: 400; font-size: 11px; letter-spacing: .06em; text-transform: uppercase;
        color: var(--muted); }}
  tr:last-child td {{ border-bottom: 0; }}
  td.num, th.num {{ text-align: right; font-family: var(--mono); font-size: 13px; }}
  .chart {{ border: 1px solid var(--border); border-radius: 14px; padding: 14px 8px 6px; background: var(--card); }}
  .steps {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 16px; }}
  .step {{ border-top: 1px solid var(--accent); padding-top: 12px; font-size: 14.5px; color: var(--text-2); }}
  .step b {{ display: block; margin-bottom: 4px; font-family: var(--mono); font-weight: 400; font-size: 12px;
             letter-spacing: .06em; text-transform: uppercase; color: var(--accent); }}
  footer {{ margin-top: 64px; padding-top: 20px; border-top: 1px solid var(--border); color: var(--muted); font-size: 13px; }}
  @media (max-width: 760px) {{ .kpis, .steps {{ grid-template-columns: repeat(2, 1fr); }} .kpi .value {{ font-size: 26px; }} }}
</style>
</head>
<body>
<div class="wrap">
  <nav>{brand}<span class="links">{' '.join(links)}</span></nav>
  <div class="eyebrow">Portfolio Engine <span class="live"><span class="dot"></span>Live paper trading</span></div>
  <h1>How my strategies are doing, updated daily</h1>
  <p class="lede">Three trading strategies (two on Bitcoin, one on Brent crude oil) running on simulated money since
  {esc(start)}. They were selected by testing eight ideas against rules fixed in advance; this page shows how they do
  on data that didn't exist when they were built.</p>
  <div class="stamp">Updated automatically every day · latest completed market day {esc(as_of)} · page built
  {now:%d %b %Y, %H:%M} UTC</div>

  <div class="kpis">
    <div class="kpi"><div class="label">Paper portfolio value</div><div class="value">${value:,.0f}</div></div>
    <div class="kpi"><div class="label">Return since start</div>
      <div class="value {'pos' if ret > 0 else 'neg' if ret < 0 else ''}">{ret:+.2f}%</div></div>
    <div class="kpi"><div class="label">Days live</div><div class="value">{days}</div></div>
    <div class="kpi"><div class="label">Simulated capital</div><div class="value">${sum(caps.values()):,.0f}</div></div>
  </div>

  <h2>Paper performance</h2>
  <p class="note">{band_txt}</p>
  {'<div class="chart">' + paper_chart + '</div>' if paper_chart else '<p class="note">The first results appear after the first completed trading day.</p>'}

  <h2>Positions and next orders</h2>
  <p class="note">Each strategy decides at the daily close and trades at the next day's open.</p>
  <div class="table-wrap"><table>
    <tr><th>Strategy</th><th>Market</th><th>Position now</th><th>Next open</th><th class="num">Equity</th></tr>
    {pos_rows or '<tr><td colspan=5>No positions yet.</td></tr>'}
  </table></div>

  <h2>Recent trades</h2>
  <div class="table-wrap"><table>
    <tr><th>Date</th><th>Strategy</th><th>Market</th><th>Action</th><th class="num">Price</th><th>Why</th></tr>
    {fill_rows or '<tr><td colspan=6>No trades yet.</td></tr>'}
  </table></div>

  <h2>Backtest context</h2>
  <p class="note">The same strategies over history ({esc(cfg['backtest_start'][:4])} → today), after trading costs, trading
  at the next day's open. Backtests flatter; the paper results above are the real test.</p>
  <div class="chart">{bt_chart}</div>
  <div class="table-wrap" style="margin-top:14px"><table>
    <tr><th>Strategy</th><th class="num">Sharpe</th><th class="num">Annual return</th><th class="num">Worst drawdown</th></tr>
    {met_rows}
  </table></div>

  <h2>How it works</h2>
  <div class="steps">
    <div class="step"><b>1 · Signals</b>Each day, after the close, every strategy reads the latest prices and decides its position.</div>
    <div class="step"><b>2 · Simulated fills</b>Orders fill at the next open with fees and slippage; 2% stop-losses are checked intraday.</div>
    <div class="step"><b>3 · Permanent record</b>Results are appended to a ledger that is never rewritten, so nothing can be tidied up later.</div>
    <div class="step"><b>4 · Automated</b>A scheduled GitHub Actions job runs the update and rebuilds this page daily.</div>
  </div>

  <footer>Educational project. Backtested and simulated (paper) results only: no real money is traded, past
  performance does not predict future results, and nothing here is investment advice. Data: Yahoo Finance daily bars.
  · <a href="{esc(cfg['github_url'])}">Source code</a></footer>
</div>
</body>
</html>"""
    out.mkdir(parents=True, exist_ok=True)
    path = out / "index.html"
    path.write_text(page, encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "site"))
    a = ap.parse_args()
    cfg = json.loads((ROOT / "site_config.json").read_text())
    p = build(Path(a.out), cfg)
    print(f"wrote {p}")


if __name__ == "__main__":
    main()
