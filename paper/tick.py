"""Daily paper-trading update.

    python -m paper.tick            # normal daily run (no-op if there are no new completed bars)
    python -m paper.tick --force    # re-run even if up to date
    python -m paper.tick --reset    # archive the current book and start a fresh one tomorrow

Scheduled by .github/workflows/paper_tick.yml (cron, 00:30 UTC daily), or a local crontab (see paper/README.md).
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING)

from paper.config import SLEEVES, sleeve_capital  # noqa: E402
from paper.ledger import STATE, tick  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--reset", action="store_true")
    a = ap.parse_args()
    if a.reset and STATE.exists() and any(STATE.iterdir()):
        dest = STATE.parent / f"archive_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}"
        shutil.move(str(STATE), dest)
        print(f"archived old book to {dest}")
    out = tick(SLEEVES, sleeve_capital(), force=a.force)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
