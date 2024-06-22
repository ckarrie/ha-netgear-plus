from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
import logging

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfDataRate,
    UnitOfInformation,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, KEY_COORDINATOR_SWITCH_INFOS, KEY_SWITCH
from .netgear_entities import (
    NetgearBinarySensorEntityDescription,
    NetgearRouterBinarySensorEntity,
)
from .netgear_switch import HAGS108Switch, HAGS108SwitchCoordinatorEntity

device_class_connection = BinarySensorDeviceClass.CONNECTIVITY

# Todo add connectivity sensors as binary

PORT_TEMPLATE = OrderedDict(
    {
        "port_{port}_status": {
            "name": "Port {port} Status",
            # "native_unit_of_measurement": BinarySensorDeviceClass.CONNECTIVITY,
            "device_class": BinarySensorDeviceClass.CONNECTIVITY,
            #'icon': "mdi:upload"
        },
    }
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up device tracker for Netgear component."""
    gs_switch = hass.data[DOMAIN][entry.entry_id][KEY_SWITCH]
    coordinator_switch_infos = hass.data[DOMAIN][entry.entry_id][
        KEY_COORDINATOR_SWITCH_INFOS
    ]

    # print("coordinator_switch_infos.data=", coordinator_switch_infos.data)

    # Router entities
    switch_entities = []

    ports_cnt = gs_switch.SWITCH_PORTS
    for i in range(ports_cnt):
        port_nr = i + 1
        for port_sensor_key, port_sensor_data in PORT_TEMPLATE.items():
            value = "off"
            description = NetgearBinarySensorEntityDescription(
                key=port_sensor_key.format(port=port_nr),
                name=port_sensor_data["name"].format(port=port_nr),
                device_class=port_sensor_data["device_class"],
                icon=port_sensor_data.get("icon"),
                value=value,
            )
            port_status_binarysensor_entity = NetgearRouterBinarySensorEntity(
                coordinator=coordinator_switch_infos,
                switch=gs_switch,
                entity_description=description,
            )
            switch_entities.append(port_status_binarysensor_entity)

    async_add_entities(switch_entities)
