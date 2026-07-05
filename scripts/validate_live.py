#!/usr/bin/env python3
"""Exercise the pure board logic against the live OneBusAway API.

No Home Assistant required — this fetches a real stop board with urllib and runs
the same build_departures()/extract_alerts() the integration uses, so we can
verify parsing end-to-end before touching HACS.

Usage:
    OBA_KEY=<your-onebusaway-api-key> python scripts/validate_live.py

OBA_KEY is required. Optional env: OBA_URL, OBA_STOP.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Import board.py directly (it is pure, no relative imports) so we don't trigger
# the package __init__, which imports Home Assistant.
sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        / "custom_components"
        / "onebusaway_board"
    ),
)

from board import build_departures, extract_alerts  # noqa: E402

URL = os.environ.get("OBA_URL", "https://api.pugetsound.onebusaway.org/api")
KEY = os.environ.get("OBA_KEY")  # required — supply your own OneBusAway API key
STOP = os.environ.get("OBA_STOP", "40_N15-T2")  # Shoreline South, southbound


def fetch(stop: str, minutes_after: int) -> dict:
    url = (
        f"{URL}/where/arrivals-and-departures-for-stop/{stop}.json"
        f"?key={KEY}&minutesAfter={minutes_after}"
    )
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.load(resp)


def hhmm(ms: int | None) -> str:
    if not ms:
        return "--"
    return datetime.fromtimestamp(ms / 1000, timezone.utc).astimezone().strftime(
        "%-I:%M"
    )


def main() -> int:
    if not KEY:
        print(
            "OBA_KEY is required. Set it to your OneBusAway API key, e.g.\n"
            "  OBA_KEY=<key> python scripts/validate_live.py",
            file=sys.stderr,
        )
        return 2

    board = fetch(STOP, 120)
    departures = build_departures(board)
    alerts = extract_alerts(board)

    print(f"stop {STOP} — {len(departures)} departures")
    print(f"{'route':8} {'headsign':26} {'depart':8} {'arrive':8} {'dev(s)':>7}")
    print("-" * 62)
    for d in departures[:12]:
        print(
            f"{(d['route'] or ''):8} {(d['headsign'] or '')[:26]:26} "
            f"{hhmm(d['depart_time']):8} {hhmm(d['arrival_time']):8} "
            f"{str(d['schedule_deviation'] if d['schedule_deviation'] is not None else ''):>7}"
        )

    print(f"\nalerts: {len(alerts)}")
    for a in alerts:
        print(f"  - [{a.get('severity')}] {a.get('summary')}")

    assert departures, "no departures parsed"
    assert all(d["trip_id"] for d in departures), "departure missing trip_id"
    print("\nOK: single-stop board built (trip_id present for cross-stop joins).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
