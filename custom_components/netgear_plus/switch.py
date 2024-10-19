"""Module to set up the Netgear PoE switch entities for Home Assistant."""

import logging

from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import const
from .netgear_entities import (
    HomeAssistantNetgearSwitch,
    NetgearBinarySensorEntityDescription,
    NetgearPOESwitchEntity,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fritzbox smarthome switch from config_entry."""
    entities = []
    gs_switch: HomeAssistantNetgearSwitch = hass.data[const.DOMAIN][
        config_entry.entry_id
    ][const.KEY_SWITCH]
    coordinator_switch_infos = hass.data[const.DOMAIN][config_entry.entry_id][
        const.KEY_COORDINATOR_SWITCH_INFOS
    ]

    if gs_switch.api and gs_switch.api.poe_ports and len(gs_switch.api.poe_ports) > 0:
        _LOGGER.info(
            "[switch.async_setup_entry] setting up Platform.SWITCH for %s Switch Ports",
            gs_switch.api.poe_ports,
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

    async_add_entities(entities)
