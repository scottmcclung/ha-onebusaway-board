"""The OneBusAway Board integration."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OneBusAwayClient
from .config_flow import parse_targets
from .const import (
    CONF_KEY,
    CONF_SCAN_INTERVAL,
    CONF_STOP,
    CONF_TARGETS,
    CONF_URL,
    DEFAULT_SCAN_INTERVAL_MIN,
    DOMAIN,
)
from .coordinator import OneBusAwayCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


def _merged(entry: ConfigEntry) -> dict:
    """Entry data with options layered on top."""
    return {**entry.data, **entry.options}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    conf = _merged(entry)
    client = OneBusAwayClient(
        conf[CONF_URL], conf[CONF_KEY], async_get_clientsession(hass)
    )
    minutes = float(conf.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MIN))
    coordinator = OneBusAwayCoordinator(
        hass,
        client,
        conf[CONF_STOP],
        parse_targets(conf.get(CONF_TARGETS, "")),
        timedelta(minutes=minutes),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload_entry))
    return True


async def _reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
