from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    KEY_COORDINATOR_SWITCH_INFOS,
    KEY_SWITCH,
    PLATFORMS,
    SCAN_INTERVAL
)
from .errors import CannotLoginException
from .netgear_switch import HAGS108Switch

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=SCAN_INTERVAL)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Netgear component."""
    gs_switch = HAGS108Switch(hass, entry)
    try:
        if not await gs_switch.async_setup():
            raise ConfigEntryNotReady
    except CannotLoginException as ex:
        raise ConfigEntryNotReady from ex

    hass.data.setdefault(DOMAIN, {})

    entry.async_on_unload(entry.add_update_listener(update_listener))

    assert entry.unique_id
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
        update_interval=SCAN_INTERVAL,
    )

    await coordinator_switch_infos.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        KEY_SWITCH: gs_switch,
        KEY_COORDINATOR_SWITCH_INFOS: coordinator_switch_infos,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    gs_switch = hass.data[DOMAIN][entry.entry_id][KEY_SWITCH]

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
