#!/usr/bin/env python3
"""Exercise the pure board logic against the live OneBusAway API.

No Home Assistant required — this fetches real boards with urllib and runs the
same build_departures()/extract_alerts() the integration uses, so we can prove
the join end-to-end before touching HACS.

Usage:
    OBA_KEY=<your-onebusaway-api-key> python scripts/validate_live.py

OBA_KEY is required. Optional env: OBA_URL, OBA_ORIGIN,
OBA_TARGETS ("Label=stop,Label=stop").
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
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
ORIGIN = os.environ.get("OBA_ORIGIN", "40_N15-T2")  # Shoreline South, southbound
TARGETS_RAW = os.environ.get(
    "OBA_TARGETS", "Westlake=40_1108,Bellevue Downtown=40_E15-T2"
)


def fetch(stop: str, minutes_after: int) -> dict:
    url = (
        f"{URL}/where/arrivals-and-departures-for-stop/{stop}.json"
        f"?key={KEY}&minutesAfter={minutes_after}"
    )
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.load(resp)


def hhmm(iso: str | None) -> str:
    if not iso:
        return "--"
    return time.strftime("%-I:%M", time.localtime(_iso_to_epoch(iso)))


def _iso_to_epoch(iso: str) -> float:
    from datetime import datetime

    return datetime.fromisoformat(iso).timestamp()


def main() -> int:
    if not KEY:
        print(
            "OBA_KEY is required. Set it to your OneBusAway API key, e.g.\n"
            "  OBA_KEY=<key> python scripts/validate_live.py",
            file=sys.stderr,
        )
        return 2

    targets = {}
    for pair in TARGETS_RAW.split(","):
        label, _, stop = pair.partition("=")
        targets[label.strip()] = stop.strip()

    origin = fetch(ORIGIN, 75)
    target_json = {label: fetch(stop, 150) for label, stop in targets.items()}

    departures = build_departures(origin, target_json)
    alerts = extract_alerts(origin, *target_json.values())

    from datetime import datetime, timezone

    def iso(ms):
        return (
            datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat() if ms else None
        )

    labels = list(targets.keys())
    header = f"{'route':7} {'depart':8} " + " ".join(f"->{l:12}" for l in labels)
    print(header)
    print("-" * len(header))
    for d in departures[:8]:
        row = f"{(d['route'] or ''):7} {hhmm(iso(d['depart_time'])):8} "
        row += " ".join(
            f"  {hhmm(iso(d['arrivals'].get(l))):12}" for l in labels
        )
        print(row)

    print(f"\nalerts: {len(alerts)}")
    for a in alerts:
        print(f"  - [{a.get('severity')}] {a.get('summary')}")

    assert departures, "no departures parsed"
    assert all(d["depart_time"] for d in departures), "departure with no time"
    print("\nOK: board built, join produced per-target arrivals.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
