"""Constants for the OneBusAway Board integration."""
from __future__ import annotations

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN: str = "onebusaway_board"
NAME: str = "OneBusAway Board"
ATTRIBUTION: str = "Data provided by OneBusAway"

DEFAULT_URL: str = "https://api.pugetsound.onebusaway.org/api"
DEFAULT_SCAN_INTERVAL_MIN: int = 5

# How far ahead to fetch a stop's board. Kept generous so consumers that join
# boards across stops by tripId (e.g. "when does this train reach my
# destination") still find a departing train on a downstream stop's board.
MINUTES_AFTER: int = 120
# Cap the board length exposed in attributes.
MAX_DEPARTURES: int = 12

CONF_NAME: str = "name"
CONF_URL: str = "url"
CONF_KEY: str = "key"
CONF_STOP: str = "stop"
CONF_SCAN_INTERVAL: str = "scan_interval"
