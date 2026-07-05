"""Pure parsing/join logic for OneBusAway Board.

No Home Assistant imports on purpose: this module is fed raw decoded API JSON so
it can be exercised against the live API (or fixtures) without standing up Home
Assistant. The coordinator handles all I/O and hands the JSON here.
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


def _target_arrivals(target_json: dict[str, Any]) -> dict[str, int | None]:
    """Map tripId -> arrival time (epoch ms) for a single target stop's board."""
    out: dict[str, int | None] = {}
    for ad in _arrivals_and_departures(target_json):
        trip = ad.get("tripId")
        if trip:
            out[trip] = _arrival_time(ad)
    return out


def build_departures(
    origin_json: dict[str, Any],
    targets: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build the origin departure board, joining each trip to its target arrivals.

    ``targets`` maps a display label (e.g. "Westlake") to that stop's decoded
    board JSON. A trip that does not serve a target (a 1 Line train has no entry
    on a Bellevue board) simply gets ``None`` for that label — no special-casing.
    """
    target_maps = {label: _target_arrivals(j) for label, j in targets.items()}

    departures: list[dict[str, Any]] = []
    for ad in _arrivals_and_departures(origin_json):
        depart = _departure_time(ad)
        if depart is None:
            continue
        trip = ad.get("tripId")
        departures.append(
            {
                "trip_id": trip,
                "route": ad.get("routeShortName") or ad.get("routeLongName"),
                "headsign": ad.get("tripHeadsign"),
                "depart_time": depart,
                "predicted": bool(ad.get("predicted")),
                "status": ad.get("status"),
                "schedule_deviation": (ad.get("tripStatus") or {}).get(
                    "scheduleDeviation"
                ),
                "arrivals": {
                    label: tmap.get(trip) for label, tmap in target_maps.items()
                },
            }
        )

    departures.sort(key=lambda d: d["depart_time"])
    return departures


def extract_alerts(*boards: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect de-duplicated service alerts (situations) across boards."""
    seen: set[str] = set()
    alerts: list[dict[str, Any]] = []
    for board in boards:
        situations = board.get("data", {}).get("references", {}).get("situations", [])
        for sit in situations:
            sid = sit.get("id")
            if not sid or sid in seen:
                continue
            seen.add(sid)
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
