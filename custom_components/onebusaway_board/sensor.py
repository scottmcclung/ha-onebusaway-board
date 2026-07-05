"""Sensor platform for OneBusAway Board."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, MAX_DEPARTURES, NAME
from .coordinator import OneBusAwayCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the board sensor for this stop's config entry."""
    coordinator: OneBusAwayCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OneBusAwayBoardSensor(coordinator, entry)])


def _iso(ms: int | None) -> str | None:
    if not ms:
        return None
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat()


class OneBusAwayBoardSensor(CoordinatorEntity[OneBusAwayCoordinator], SensorEntity):
    """Departure board for one stop: state is the next departure, board in attrs."""

    _attr_has_entity_name = True
    _attr_name = "Next departure"
    _attr_icon = "mdi:train"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_attribution = ATTRIBUTION

    def __init__(
        self, coordinator: OneBusAwayCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_board"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title or NAME,
            manufacturer=NAME,
        )

    @property
    def _departures(self) -> list[dict[str, Any]]:
        return (self.coordinator.data or {}).get("departures", [])

    @property
    def native_value(self) -> datetime | None:
        for dep in self._departures:
            ms = dep.get("depart_time") or dep.get("arrival_time")
            if ms:
                return datetime.fromtimestamp(ms / 1000, timezone.utc)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        departures = [
            {
                "route": dep.get("route"),
                "headsign": dep.get("headsign"),
                "trip_id": dep.get("trip_id"),
                "depart": _iso(dep.get("depart_time")),
                "arrive": _iso(dep.get("arrival_time")),
                "predicted": dep.get("predicted"),
                "status": dep.get("status"),
                "schedule_deviation": dep.get("schedule_deviation"),
            }
            for dep in self._departures[:MAX_DEPARTURES]
        ]
        return {"departures": departures, "alerts": data.get("alerts", [])}
