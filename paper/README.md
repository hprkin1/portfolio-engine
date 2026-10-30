# Paper trading

Forward paper trading of the live candidates in `paper/config.py` (BTC OBV momentum, BTC AC momentum,
oil trend/carry on BNO), $30k split equally. Started 2026-10-31.

**How it works.** Each daily tick replays every strategy through the same engine used for backtests
(signals at the close, fills at the next open, intraday stops, fees + slippage) from the start date to the
latest *completed* daily bar, then **appends** only the new days to the ledger in `paper/state/`:

| File | Contents |
|---|---|
| `meta.json` | start date, capital, last bar per strategy, latest positions and next-open orders, drift |
| `equity.csv` | daily equity per strategy (append-only) |
| `fills.csv` | every fill: date, strategy, symbol, action, price, reason (signal / stop) |
| `orders.csv` | every decision taken at a close, to be executed at the next open |

Rows already written are never changed. If a replay disagrees with the record (Yahoo revised a price, or the
config was edited), the difference is reported as **drift** on the dashboard and the record stays as it was.

## Scheduling (cron)

**GitHub Actions (default):** `.github/workflows/paper_tick.yml` runs `python -m paper.tick` at 00:30 UTC every
day and commits `paper/state/`. `git pull` to see the latest ledger locally. You can also trigger it from the
Actions tab, or from cron-job.org via `repository_dispatch` with event type `paper_tick`.

**Local crontab (alternative; don't run both, or the two ledgers diverge):**

```cron
CRON_TZ=UTC
30 0 * * * cd /path/to/portfolio-engine && /usr/bin/env python3 -m paper.tick >> paper/tick.log 2>&1
```

## Commands

```bash
python -m paper.tick            # daily update (no-op if no new completed bars)
python -m paper.tick --force    # re-run anyway
python -m paper.tick --reset    # archive this book and start a fresh one tomorrow
```
