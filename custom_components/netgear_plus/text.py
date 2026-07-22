"""Editable Netgear Plus port name text entities."""

from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import NetgearSwitchConfigEntry
from .netgear_switch import HomeAssistantNetgearSwitch, NetgearAPICoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: NetgearSwitchConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up editable port name text entities."""
    del hass
    gs_switch = config_entry.runtime_data.gs_switch
    coordinator = config_entry.runtime_data.coordinator_switch_infos

    if (
        not gs_switch.api
        or not gs_switch.api.ports
        or gs_switch.api.switch_model.MODEL_NAME != "GS308EP"
    ):
        return

    async_add_entities(
        NetgearPortNameTextEntity(coordinator, gs_switch, port)
        for port in range(1, gs_switch.api.ports + 1)
    )


class NetgearPortNameTextEntity(NetgearAPICoordinatorEntity, TextEntity):
    """Text entity for a port's configured name."""

    _attr_icon = "mdi:rename"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        hub: HomeAssistantNetgearSwitch,
        port_nr: int,
    ) -> None:
        """Initialize the port name text entity."""
        super().__init__(coordinator, hub)
        self.hub = hub
        self.port_nr = port_nr
        self._unique_id = f"{hub.unique_id}-port_{port_nr}_name"
        self._name = f"Port {port_nr} Port Name"
        self._attr_native_value = ""
        self.async_update_device()

    @callback
    def async_update_device(self) -> None:
        """Update the configured port name from coordinator data."""
        data = self.coordinator.data or {}
        value = data.get(f"port_{self.port_nr}_setting_name")
        self._attr_native_value = "" if value is None else str(value)

    async def async_set_value(self, value: str) -> None:
        """Set the configured port name."""
        successful = await self.hub.async_call_api(
            self.hub.api.set_port_name,
            self.port_nr,
            value,
        )
        if not successful:
            raise HomeAssistantError(f"Renaming port {self.port_nr} failed")

        self._attr_native_value = value
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
