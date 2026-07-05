"""Constants for the OneBusAway Board integration."""
from __future__ import annotations

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN: str = "onebusaway_board"
NAME: str = "OneBusAway Board"
ATTRIBUTION: str = "Data provided by OneBusAway"

DEFAULT_URL: str = "https://api.pugetsound.onebusaway.org/api"
DEFAULT_SCAN_INTERVAL_MIN: int = 5

# How far ahead to look. The target window is wider than the origin window so a
# train that has already left the origin is still present on its target board.
ORIGIN_MINUTES_AFTER: int = 75
TARGET_MINUTES_AFTER: int = 150

CONF_NAME: str = "name"
CONF_URL: str = "url"
CONF_KEY: str = "key"
CONF_STOP: str = "stop"
CONF_TARGETS: str = "targets"
CONF_SCAN_INTERVAL: str = "scan_interval"
