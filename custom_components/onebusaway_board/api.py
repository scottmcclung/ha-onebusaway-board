"""Async client for the OneBusAway 'where' REST API."""
from __future__ import annotations

import asyncio
import socket
from typing import Any

import aiohttp
import async_timeout


class OneBusAwayError(Exception):
    """General OneBusAway API error."""


class OneBusAwayAuthError(OneBusAwayError):
    """Invalid API key."""


class OneBusAwayConnectionError(OneBusAwayError):
    """Communication error."""


class OneBusAwayClient:
    """Minimal client covering the endpoints this integration needs."""

    def __init__(
        self, base_url: str, key: str, session: aiohttp.ClientSession
    ) -> None:
        self._base = base_url.rstrip("/")
        self._key = key
        self._session = session

    async def arrivals_and_departures(
        self, stop: str, minutes_after: int
    ) -> dict[str, Any]:
        """Fetch the arrivals-and-departures board for a stop."""
        url = (
            f"{self._base}/where/arrivals-and-departures-for-stop/{stop}.json"
            f"?key={self._key}&minutesAfter={minutes_after}"
        )
        return await self._get(url)

    async def _get(self, url: str) -> dict[str, Any]:
        try:
            async with async_timeout.timeout(15):
                response = await self._session.get(url)
                if response.status in (401, 403):
                    raise OneBusAwayAuthError("Invalid API key")
                response.raise_for_status()
                return await response.json()
        except OneBusAwayAuthError:
            raise
        except asyncio.TimeoutError as err:
            raise OneBusAwayConnectionError("Timeout fetching OneBusAway data") from err
        except (aiohttp.ClientError, socket.gaierror) as err:
            raise OneBusAwayConnectionError("Error fetching OneBusAway data") from err
