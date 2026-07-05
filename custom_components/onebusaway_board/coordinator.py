"""Data update coordinator for OneBusAway Board."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OneBusAwayClient, OneBusAwayError
from .board import build_departures, extract_alerts
from .const import LOGGER, NAME, ORIGIN_MINUTES_AFTER, TARGET_MINUTES_AFTER


class OneBusAwayCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch the origin board plus each target board and join them by tripId."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: OneBusAwayClient,
        stop: str,
        targets: dict[str, str],
        scan_interval: timedelta,
    ) -> None:
        super().__init__(
            hass, LOGGER, name=NAME, update_interval=scan_interval
        )
        self._client = client
        self._stop = stop
        self._targets = targets

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            origin = await self._client.arrivals_and_departures(
                self._stop, ORIGIN_MINUTES_AFTER
            )
            target_json: dict[str, Any] = {}
            for label, stop_id in self._targets.items():
                target_json[label] = await self._client.arrivals_and_departures(
                    stop_id, TARGET_MINUTES_AFTER
                )
        except OneBusAwayError as err:
            raise UpdateFailed(str(err)) from err

        return {
            "departures": build_departures(origin, target_json),
            "alerts": extract_alerts(origin, *target_json.values()),
        }
