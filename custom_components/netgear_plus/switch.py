"""Module to set up the Netgear PoE switch entities for Home Assistant."""

import logging

from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import NetgearSwitchConfigEntry
from .netgear_entities import (
    NetgearBinarySensorEntityDescription,
    NetgearLedSwitchEntity,
    NetgearPOESwitchEntity,
    NetgearPortSwitchEntity,
)
from .netgear_switch import HomeAssistantNetgearSwitch, NetgearAPICoordinatorEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: NetgearSwitchConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fritzbox smarthome switch from config_entry."""
    del hass
    entities = []
    gs_switch = config_entry.runtime_data.gs_switch
    coordinator_switch_infos = config_entry.runtime_data.coordinator_switch_infos

    if gs_switch.api and gs_switch.api.poe_ports and len(gs_switch.api.poe_ports) > 0:
        _LOGGER.info(
            "[switch.async_setup_entry] setting up Platform.SWITCH for %s Switch Ports",
            len(gs_switch.api.poe_ports),
        )

        for poe_port in gs_switch.api.poe_ports:
            switch_entity = NetgearPOESwitchEntity(
                coordinator=coordinator_switch_infos,
                hub=gs_switch,
                entity_description=NetgearBinarySensorEntityDescription(
                    key=f"port_{poe_port}_poe_power_active",
                    name=f"Port {poe_port} PoE Power",
                    device_class=SwitchDeviceClass.OUTLET,
                ),
                port_nr=poe_port,
            )

            entities.append(switch_entity)

    if (
        gs_switch.api
        and gs_switch.api.ports
        and gs_switch.api.switch_model.MODEL_NAME == "GS308EP"
    ):
        _LOGGER.info(
            "[switch.async_setup_entry] setting up Flow Control switches for %s ports",
            gs_switch.api.ports,
        )
        for port_nr in range(1, gs_switch.api.ports + 1):
            entities.append(
                NetgearPortFlowControlSwitchEntity(
                    coordinator=coordinator_switch_infos,
                    hub=gs_switch,
                    port_nr=port_nr,
                )
            )

    if (
        gs_switch.api
        and gs_switch.api.ports
        and gs_switch.api.switch_model.MODEL_NAME != "GS308EP"
    ):
        _LOGGER.info(
            "[switch.async_setup_entry] setting up legacy Port switches for %s ports",
            gs_switch.api.ports,
        )
        for port_nr in range(1, gs_switch.api.ports + 1):
            port_switch = NetgearPortSwitchEntity(
                coordinator=coordinator_switch_infos,
                hub=gs_switch,
                entity_description=NetgearBinarySensorEntityDescription(
                    key=f"port_{port_nr}_modus_speed",
                    name=f"Port {port_nr}",
                    device_class=SwitchDeviceClass.SWITCH,
                ),
                port_nr=port_nr,
            )
            entities.append(port_switch)

    if gs_switch.api and gs_switch.api.switch_model.has_led_switch():  # type: ignore call-issue
        _LOGGER.info(
            "[switch.async_setup_entry] setting up Platform.SWITCH for Front Panel LEDs"
        )

        switch_entity = NetgearLedSwitchEntity(
            coordinator=coordinator_switch_infos,
            hub=gs_switch,
            entity_description=NetgearBinarySensorEntityDescription(
                key="led_status",
                name="Front Panel LEDs",
                device_class=SwitchDeviceClass.SWITCH,
            ),
        )

        entities.append(switch_entity)

    async_add_entities(entities)


class NetgearPortFlowControlSwitchEntity(NetgearAPICoordinatorEntity, SwitchEntity):
    """Switch entity for a GS308EP port's flow-control setting."""

    _attr_icon = "mdi:swap-horizontal"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        hub: HomeAssistantNetgearSwitch,
        port_nr: int,
    ) -> None:
        """Initialize the port flow-control switch."""
        super().__init__(coordinator, hub)
        self.hub = hub
        self.port_nr = port_nr
        self._unique_id = f"{hub.unique_id}-port_{port_nr}_flow_control"
        self._name = f"Port {port_nr} Flow Control"
        self._attr_is_on = False
        self.async_update_device()

    @callback
    def async_update_device(self) -> None:
        """Update flow-control state from coordinator data."""
        data = self.coordinator.data or {}
        value = data.get(f"port_{self.port_nr}_setting_flow_control")

        if isinstance(value, bool):
            self._attr_is_on = value
            return

        try:
            self._attr_is_on = int(value) == 1
        except (TypeError, ValueError):
            self._attr_is_on = False

    async def async_turn_on(self, **kwargs) -> None:
        """Enable flow control for this port."""
        del kwargs
        await self._async_set_flow_control(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable flow control for this port."""
        del kwargs
        await self._async_set_flow_control(False)

    async def _async_set_flow_control(self, enabled: bool) -> None:
        """Write the flow-control setting to the switch."""
        successful = await self.hub.async_call_api(
            self.hub.api.set_port_settings,
            self.port_nr,
            flow_control=enabled,
        )
        if not successful:
            state = "enabling" if enabled else "disabling"
            raise HomeAssistantError(
                f"{state.capitalize()} flow control for port {self.port_nr} failed"
            )

        self._attr_is_on = enabled
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
