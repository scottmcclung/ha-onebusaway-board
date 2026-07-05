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
    CONF_TARGETS,
    CONF_URL,
    DEFAULT_SCAN_INTERVAL_MIN,
    DEFAULT_URL,
    DOMAIN,
    NAME,
    ORIGIN_MINUTES_AFTER,
)


def parse_targets(raw: str) -> dict[str, str]:
    """Parse a multiline 'Label = stop_id' string into {label: stop_id}."""
    targets: dict[str, str] = {}
    for line in (raw or "").splitlines():
        stripped = line.strip()
        if not stripped or "=" not in stripped:
            continue
        label, _, stop = stripped.partition("=")
        label, stop = label.strip(), stop.strip()
        if label and stop:
            targets[label] = stop
    return targets


def _interval_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1, max=60, unit_of_measurement="min", mode=selector.NumberSelectorMode.BOX
        )
    )


def _targets_selector() -> selector.TextSelector:
    return selector.TextSelector(selector.TextSelectorConfig(multiline=True))


class OneBusAwayBoardFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            client = OneBusAwayClient(
                user_input[CONF_URL],
                user_input[CONF_KEY],
                async_get_clientsession(self.hass),
            )
            try:
                await client.arrivals_and_departures(
                    user_input[CONF_STOP], ORIGIN_MINUTES_AFTER
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
                vol.Optional(CONF_TARGETS, default=""): _targets_selector(),
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
    """Edit targets and poll interval after setup."""

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
                vol.Optional(
                    CONF_TARGETS, default=current.get(CONF_TARGETS, "")
                ): _targets_selector(),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=current.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MIN
                    ),
                ): _interval_selector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
