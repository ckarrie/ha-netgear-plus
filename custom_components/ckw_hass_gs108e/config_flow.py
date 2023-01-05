"""Config flow to configure the Netgear integration."""
from __future__ import annotations

import logging
from typing import cast
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_TIMEOUT,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.util.network import is_ipv4_address

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    DEFAULT_HOST,
    DEFAULT_CONF_TIMEOUT,
)
from .errors import CannotLoginException
from .netgear_switch import get_api

_LOGGER = logging.getLogger(__name__)


def _user_schema_with_defaults(user_input):
    user_schema = {vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "")): str}
    user_schema.update(_ordered_shared_schema(user_input))

    return vol.Schema(user_schema)


def _ordered_shared_schema(schema_input):
    return {
        vol.Required(CONF_PASSWORD, default=schema_input.get(CONF_PASSWORD, "")): str,
    }


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Init object."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        settings_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TIMEOUT,
                    default=self.config_entry.options.get(CONF_TIMEOUT, DEFAULT_CONF_TIMEOUT.total_seconds()),  # CONF_TIMEOUT = 'timeout'
                ): int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=settings_schema)


class NetgearFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self):
        """Initialize the netgear config flow."""
        self.placeholders = {
            CONF_HOST: DEFAULT_HOST,
        }
        self.discovered = False

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)

    async def _show_setup_form(self, user_input=None, errors=None):
        """Show the setup form to the user."""
        if not user_input:
            user_input = {}

        data_schema = _user_schema_with_defaults(user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors or {},
            description_placeholders=self.placeholders,
        )

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is None:
            return await self._show_setup_form()

        host = user_input.get(CONF_HOST, self.placeholders[CONF_HOST])
        password = user_input[CONF_PASSWORD]

        # Open connection and check authentication
        try:
            api = await self.hass.async_add_executor_job(
                get_api, host, password
            )
        except CannotLoginException:
            errors["base"] = "config"

        if errors:
            return await self._show_setup_form(user_input, errors)

        config_data = {
            CONF_PASSWORD: password,
            CONF_HOST: host,
        }

        # Check if already configured
        unique_id = await self.hass.async_add_executor_job(api.get_unique_id)
        await self.async_set_unique_id(unique_id, raise_on_progress=False)
        self._abort_if_unique_id_configured(updates=config_data)

        name = f'GS108E {host}'

        return self.async_create_entry(
            title=name,
            data=config_data,
        )
