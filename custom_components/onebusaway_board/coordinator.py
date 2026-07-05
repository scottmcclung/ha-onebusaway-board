"""Data update coordinator for OneBusAway Board."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OneBusAwayClient, OneBusAwayError
from .board import build_departures, extract_alerts
from .const import LOGGER, MINUTES_AFTER, NAME


class OneBusAwayCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch and parse the board for a single stop."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: OneBusAwayClient,
        stop: str,
        scan_interval: timedelta,
    ) -> None:
        super().__init__(
            hass, LOGGER, name=NAME, update_interval=scan_interval
        )
        self._client = client
        self._stop = stop

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            board = await self._client.arrivals_and_departures(
                self._stop, MINUTES_AFTER
            )
        except OneBusAwayError as err:
            raise UpdateFailed(str(err)) from err

        return {
            "departures": build_departures(board),
            "alerts": extract_alerts(board),
        }
