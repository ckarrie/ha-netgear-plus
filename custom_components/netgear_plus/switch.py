"""Module to set up the Netgear PoE switch entities for Home Assistant."""

import logging

from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NetgearSwitchConfigEntry
from .netgear_entities import (
    NetgearBinarySensorEntityDescription,
    NetgearLedSwitchEntity,
    NetgearPOESwitchEntity,
)

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
