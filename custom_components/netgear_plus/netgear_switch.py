"""HomeAssistant Setup for Netgear API."""

from __future__ import annotations

import asyncio
import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .errors import CannotLoginError
from .netgear_plus import NetgearSwitchConnector

_LOGGER = logging.getLogger(__name__)


def get_api(host: str, password: str = "") -> NetgearSwitchConnector:
    """Get the Netgear API and login to it."""
    api: NetgearSwitchConnector = NetgearSwitchConnector(host, password)
    api.autodetect_model()
    # Only login if password is not empty.
    # This allows to call get_unique_id before the user has provided a password
    if password and not api.get_login_cookie():
        raise CannotLoginError
    return api


class HomeAssistantNetgearSwitch:
    """Class to manage the Netgear switch integration with Home Assistant."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the HomeAssistantNetgearSwitch class."""
        if not entry.unique_id:
            error_message = "ConfigEntry must have a unique_id"
            raise ValueError(error_message)
        self.hass = hass
        self.entry = entry
        self.entry_id = entry.entry_id
        self.unique_id = entry.unique_id
        self.device_name = entry.title
        self._host: str = entry.data[CONF_HOST]
        self._password = entry.data[CONF_PASSWORD]

        # set on setup
        self.api: NetgearSwitchConnector | None = None
        self.model = None

        # async lock
        self.api_lock = asyncio.Lock()

    def _setup(self) -> bool:
        self.api = get_api(host=self._host, password=self._password)
        if not self.api.switch_model:
            _LOGGER.info(
                "[HomeAssistantNetgearSwitch._setup] "
                "No NetgearSwitchConnector switch_model set, "
                "autodetecting model via NetgearSwitchConnector.autodetect_model()"
            )
            self.api.autodetect_model()
            _LOGGER.info(
                "[HomeAssistantNetgearSwitch._setup] Autodetected model: %s",
                str(self.api.switch_model),
            )
        self.model = self.api.switch_model.MODEL_NAME
        return True

    async def async_setup(self) -> bool:
        """Set up the Netgear switch asynchronously."""
        async with self.api_lock:
            if not await self.hass.async_add_executor_job(self._setup):
                return False
        return True

    async def async_get_switch_infos(self) -> dict[str, Any] | None:
        """Get switch information asynchronously."""
        async with self.api_lock:
            return await self.hass.async_add_executor_job(self.api.get_switch_infos)  # type: ignore[attr-defined]


class NetgearCoordinatorEntity(CoordinatorEntity):
    """Base class for a Netgear router entity."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, switch: HomeAssistantNetgearSwitch
    ) -> None:
        """Initialize a Netgear device."""
        super().__init__(coordinator)
        self._switch = switch
        self._name = switch.device_name
        self._unique_id = switch.unique_id

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name."""
        return self._name

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._switch.unique_id)},
        )


class NetgearAPICoordinatorEntity(NetgearCoordinatorEntity):
    """Base class for a Netgear router entity."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, switch: HomeAssistantNetgearSwitch
    ) -> None:
        """Initialize a Netgear device."""
        super().__init__(coordinator, switch)

    @abstractmethod
    @callback
    def async_update_device(self) -> None:
        """Update the Netgear device."""

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_update_device()
        super()._handle_coordinator_update()
