"""Pure parsing logic for a single OneBusAway stop board.

No Home Assistant imports on purpose: this module is fed raw decoded API JSON so
it can be exercised against the live API (or fixtures) without standing up Home
Assistant. The coordinator handles all I/O and hands the JSON here.

Each stop is its own board. Cross-stop composition (e.g. "when does this train
reach my destination") is a consumer concern: every departure carries its
``trip_id``, so a consumer joins boards across stops on that key.
"""
from __future__ import annotations

from typing import Any


def _best_time(ad: dict[str, Any], predicted_key: str, scheduled_key: str) -> int | None:
    """Prefer the real-time prediction, fall back to schedule.

    OBA reports a predicted time of 0 when it has no real-time data for a trip,
    so 0 must be treated as "unknown" rather than the epoch.
    """
    predicted = ad.get(predicted_key) or 0
    if predicted > 0:
        return int(predicted)
    scheduled = ad.get(scheduled_key) or 0
    return int(scheduled) if scheduled > 0 else None


def _departure_time(ad: dict[str, Any]) -> int | None:
    return _best_time(ad, "predictedDepartureTime", "scheduledDepartureTime")


def _arrival_time(ad: dict[str, Any]) -> int | None:
    return _best_time(ad, "predictedArrivalTime", "scheduledArrivalTime")


def _arrivals_and_departures(board: dict[str, Any]) -> list[dict[str, Any]]:
    return board.get("data", {}).get("entry", {}).get("arrivalsAndDepartures", [])


def build_departures(board_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Build the board for a single stop, sorted by time.

    Each entry carries both the arrival and departure time at this stop: a
    consumer treating the stop as an origin uses ``depart_time``; one treating
    it as a destination (matched by ``trip_id``) uses ``arrival_time``.
    """
    departures: list[dict[str, Any]] = []
    for ad in _arrivals_and_departures(board_json):
        depart = _departure_time(ad)
        arrive = _arrival_time(ad)
        when = depart or arrive
        if when is None:
            continue
        departures.append(
            {
                "trip_id": ad.get("tripId"),
                "route": ad.get("routeShortName") or ad.get("routeLongName"),
                "headsign": ad.get("tripHeadsign"),
                "arrival_time": arrive,
                "depart_time": depart,
                "predicted": bool(ad.get("predicted")),
                "status": ad.get("status"),
                "schedule_deviation": (ad.get("tripStatus") or {}).get(
                    "scheduleDeviation"
                ),
            }
        )

    departures.sort(key=lambda d: d["depart_time"] or d["arrival_time"])
    return departures


def extract_alerts(board_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect service alerts (situations) for a stop's board."""
    situations = (
        board_json.get("data", {}).get("references", {}).get("situations", [])
    )
    alerts: list[dict[str, Any]] = []
    for sit in situations:
        sid = sit.get("id")
        if not sid:
            continue
        alerts.append(
            {
                "id": sid,
                "summary": (sit.get("summary") or {}).get("value"),
                "description": (sit.get("description") or {}).get("value"),
                "severity": sit.get("severity"),
                "url": (sit.get("url") or {}).get("value"),
            }
        )
    return alerts
