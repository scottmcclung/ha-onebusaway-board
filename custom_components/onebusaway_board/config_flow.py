"""Config and options flow for OneBusAway Board."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    OneBusAwayAuthError,
    OneBusAwayClient,
    OneBusAwayConnectionError,
    OneBusAwayError,
)
from .const import (
    CONF_KEY,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_STOP,
    CONF_URL,
    DEFAULT_SCAN_INTERVAL_MIN,
    DEFAULT_URL,
    DOMAIN,
    MINUTES_AFTER,
    NAME,
)


def _interval_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            max=60,
            unit_of_measurement="min",
            mode=selector.NumberSelectorMode.BOX,
        )
    )


class OneBusAwayBoardFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial config flow. One entry per stop."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_STOP])
            self._abort_if_unique_id_configured()
            client = OneBusAwayClient(
                user_input[CONF_URL],
                user_input[CONF_KEY],
                async_get_clientsession(self.hass),
            )
            try:
                await client.arrivals_and_departures(
                    user_input[CONF_STOP], MINUTES_AFTER
                )
            except OneBusAwayAuthError:
                errors["base"] = "auth"
            except OneBusAwayConnectionError:
                errors["base"] = "cannot_connect"
            except OneBusAwayError:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=NAME): selector.TextSelector(),
                vol.Required(CONF_URL, default=DEFAULT_URL): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
                ),
                vol.Required(CONF_KEY): selector.TextSelector(),
                vol.Required(CONF_STOP): selector.TextSelector(),
                vol.Required(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL_MIN
                ): _interval_selector(),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return OneBusAwayOptionsFlow(entry)


class OneBusAwayOptionsFlow(OptionsFlow):
    """Edit the poll interval after setup."""

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self._entry.data, **self._entry.options}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=current.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MIN
                    ),
                ): _interval_selector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
