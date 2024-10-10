"""HomeAssistant integration for Netgear Switches - Binary Switches definitions."""

from __future__ import annotations

import logging
from collections import OrderedDict
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from .const import DOMAIN, KEY_COORDINATOR_SWITCH_INFOS, KEY_SWITCH
from .netgear_entities import (
    NetgearBinarySensorEntityDescription,
    NetgearRouterBinarySensorEntity,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .netgear_switch import HomeAssistantNetgearSwitch

_LOGGER = logging.getLogger(__name__)

PORT_TEMPLATE = OrderedDict(
    {
        "port_{port}_status": {
            "name": "Port {port} Status",
            "device_class": BinarySensorDeviceClass.CONNECTIVITY,
            #'icon': "mdi:upload"
        },
    }
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up device tracker for Netgear component."""
    gs_switch: HomeAssistantNetgearSwitch = hass.data[DOMAIN][entry.entry_id][
        KEY_SWITCH
    ]
    coordinator_switch_infos = hass.data[DOMAIN][entry.entry_id][
        KEY_COORDINATOR_SWITCH_INFOS
    ]

    # Router entities
    switch_entities = []

    ports_cnt = gs_switch.api.ports or 0
    _LOGGER.info(
        "[binary_sensor.async_setup_entry] \
setting up Platform.BINARY_SENSOR for %d Switch Ports",
        ports_cnt,
    )
    for i in range(ports_cnt):
        port_nr = i + 1
        for port_sensor_key, port_sensor_data in PORT_TEMPLATE.items():
            value = "off"
            description = NetgearBinarySensorEntityDescription(
                key=port_sensor_key.format(port=port_nr),
                name=port_sensor_data["name"].format(port=port_nr),
                device_class=port_sensor_data["device_class"],
                icon=port_sensor_data.get("icon"),
                value=value,  # type: ignore[valid-type]
            )
            port_status_binarysensor_entity = NetgearRouterBinarySensorEntity(
                coordinator=coordinator_switch_infos,
                switch=gs_switch,
                entity_description=description,
            )
            switch_entities.append(port_status_binarysensor_entity)

    async_add_entities(switch_entities)
