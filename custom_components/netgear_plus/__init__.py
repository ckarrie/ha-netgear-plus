"""HomeAssistant integration for Netgear Switches."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
from attr import dataclass
from homeassistant.const import CONF_HOST

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    PLATFORMS,
    SCAN_INTERVAL,
)
from .errors import CannotLoginError
from .netgear_switch import HomeAssistantNetgearSwitch

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_TIMEDELTA = timedelta(seconds=SCAN_INTERVAL)

type NetgearSwitchConfigEntry = ConfigEntry[NetgearSwitchData]


@dataclass
class NetgearSwitchData:
    """Runtime Data for ConfigEntry."""

    gs_switch: HomeAssistantNetgearSwitch
    coordinator_switch_infos: DataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: NetgearSwitchConfigEntry
) -> bool:
    """Set up Netgear component."""
    gs_switch = HomeAssistantNetgearSwitch(hass, entry)
    try:
        if not await gs_switch.async_setup():
            raise ConfigEntryNotReady
    except CannotLoginError as ex:
        raise ConfigEntryNotReady from ex

    entry.async_on_unload(entry.add_update_listener(update_listener))

    if not entry.unique_id:
        message = "entry.unique_id not defined."
        raise NameError(message)
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.unique_id)},
        manufacturer="Netgear",
        name=gs_switch.device_name,
        model=gs_switch.model,
        configuration_url=f"http://{entry.data[CONF_HOST]}/",
    )

    async def async_update_switch_infos() -> dict[str, Any] | None:
        """Fetch data from the router."""
        return await gs_switch.async_get_switch_infos()

    # Create update coordinators
    coordinator_switch_infos = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{gs_switch.device_name} Switch infos",
        update_method=async_update_switch_infos,
        update_interval=SCAN_INTERVAL_TIMEDELTA,
    )

    await coordinator_switch_infos.async_config_entry_first_refresh()

    entry.runtime_data = NetgearSwitchData(gs_switch, coordinator_switch_infos)  # type: ignore argument-type

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
