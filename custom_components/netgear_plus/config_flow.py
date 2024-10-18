"""Config flow to configure the Netgear integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlparse

import requests
import voluptuous as vol
from homeassistant import config_entries

if TYPE_CHECKING:
    from homeassistant.components import ssdp
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_TIMEOUT
from homeassistant.core import callback
from homeassistant.util.network import is_ipv4_address

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigFlowResult

from .const import DEFAULT_CONF_TIMEOUT, DEFAULT_HOST, DOMAIN
from .errors import CannotLoginError
from .netgear_switch import get_api

_LOGGER = logging.getLogger(__name__)


def _discovery_schema_with_defaults(discovery_info: dict[str, Any]) -> vol.Schema:
    return vol.Schema(_ordered_shared_schema(discovery_info))


def _user_schema_with_defaults(user_input: dict[str, Any]) -> vol.Schema:
    user_schema = {vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "")): str}
    user_schema.update(_ordered_shared_schema(user_input))

    return vol.Schema(user_schema)


def _ordered_shared_schema(schema_input: dict[str, Any]) -> dict[vol.Required, type]:
    return {
        vol.Required(CONF_PASSWORD, default=schema_input.get(CONF_PASSWORD, "")): str,
    }


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Init object."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        settings_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TIMEOUT,
                    default=self.config_entry.options.get(
                        CONF_TIMEOUT, DEFAULT_CONF_TIMEOUT.total_seconds()
                    ),  # CONF_TIMEOUT = 'timeout'
                ): int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=settings_schema)


class NetgearFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
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

    async def _show_setup_form(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, str] | None = None,
    ) -> ConfigFlowResult:
        """Show the setup form to the user."""
        if not user_input:
            user_input = {}

        if self.discovered:
            data_schema = _discovery_schema_with_defaults(user_input)
        else:
            data_schema = _user_schema_with_defaults(user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors or {},
            description_placeholders=self.placeholders,
        )

    async def async_step_ssdp(
        self, discovery_info: ssdp.SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Initialize flow from ssdp."""
        updated_data: dict[str, str | int | bool] = {}
        errors: dict[str, str] = {}

        device_url = urlparse(discovery_info.ssdp_location)
        if hostname := device_url.hostname:
            hostname = cast(str, hostname)
            updated_data[CONF_HOST] = hostname

        if not is_ipv4_address(str(hostname)):
            return self.async_abort(reason="not_ipv4_address")

        _LOGGER.debug("Netgear ssdp discovery info: %s", discovery_info)

        # Open connection to get unique id
        try:
            api = await self.hass.async_add_executor_job(
                get_api,
                updated_data[CONF_HOST],  # type: ignore[arg-type]
            )
        except requests.exceptions.ConnectTimeout:
            errors["base"] = "timeout"
        except NotImplementedError:
            errors["base"] = "not_implemented_error"

        unique_id = await self.hass.async_add_executor_job(api.get_unique_id)
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(updates=updated_data)

        self.placeholders.update(updated_data)  # type: ignore[arg-type]
        self.discovered = True

        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is None:
            return await self._show_setup_form()

        host = user_input.get(CONF_HOST, self.placeholders[CONF_HOST])
        password = user_input[CONF_PASSWORD]

        # Open connection and check authentication
        try:
            api = await self.hass.async_add_executor_job(get_api, host, password)
        except CannotLoginError:
            errors["base"] = "config"
        except requests.exceptions.ConnectTimeout:
            errors["base"] = "timeout"
        except NotImplementedError:
            errors["base"] = "not_implemented_error"

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

        # set autodetected switch model name
        model_name = api.switch_model.MODEL_NAME
        name = f"{model_name} {host}"

        return self.async_create_entry(
            title=name,
            data=config_data,
        )
