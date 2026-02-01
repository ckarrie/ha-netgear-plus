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
from .errors import CannotLoginError, MaxSessionsError
from .netgear_switch import HomeAssistantNetgearSwitch

_LOGGER = logging.getLogger(__name__)

# Retry delay when max sessions error occurs (in seconds)
MAX_SESSIONS_RETRY_DELAY = 120  # 2 minutes

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
    except MaxSessionsError as ex:
        _LOGGER.warning(
            "Maximum sessions reached on switch %s. "
            "Will retry in %d seconds. "
            "Consider restarting the switch to clear stale sessions.",
            entry.data[CONF_HOST],
            MAX_SESSIONS_RETRY_DELAY,
        )
        raise ConfigEntryNotReady(
            f"Max sessions reached, retry in {MAX_SESSIONS_RETRY_DELAY}s"
        ) from ex
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


async def async_unload_entry(
    hass: HomeAssistant, entry: NetgearSwitchConfigEntry
) -> bool:
    """Unload a config entry."""
    # Logout from the switch to free up the session
    if hasattr(entry, "runtime_data") and entry.runtime_data:
        gs_switch = entry.runtime_data.gs_switch
        try:
            await gs_switch.async_logout()
            _LOGGER.debug("Successfully logged out from switch %s", gs_switch.device_name)
        except Exception:  # noqa: BLE001
            _LOGGER.debug(
                "Failed to logout from switch %s (may already be disconnected)",
                gs_switch.device_name,
            )
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
