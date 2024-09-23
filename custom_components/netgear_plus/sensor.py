"""Number Sensors for Netgear routers."""

from __future__ import annotations

from collections import OrderedDict
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
from .netgear_entities import NetgearRouterSensorEntity, NetgearSensorEntityDescription
from .netgear_switch import HomeAssistantNetgearSwitch

_LOGGER = logging.getLogger(__name__)


DEVICE_SENSOR_TYPES = [
    NetgearSensorEntityDescription(
        key="switch_ip",
        name="IP Address",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        device_class=None,
        icon="mdi:switch",
    ),
    NetgearSensorEntityDescription(
        key="switch_name",
        name="Switch Name",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        device_class=None,
        icon="mdi:text",
    ),
    NetgearSensorEntityDescription(
        key="switch_bootloader",
        name="Switch Bootlader",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        device_class=None,
        icon="mdi:text",
    ),
    NetgearSensorEntityDescription(
        key="switch_firmware",
        name="Switch Firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        device_class=None,
        icon="mdi:text",
    ),
    NetgearSensorEntityDescription(
        key="switch_serial_number",
        name="Switch Serial Number",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=None,
        device_class=None,
        icon="mdi:text",
    ),
    NetgearSensorEntityDescription(
        key="response_time_s",
        name="Response Time (seconds)",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        icon="mdi:clock",
    ),
]

PORT_TEMPLATE = OrderedDict(
    {
        "port_{port}_traffic_rx_mbytes": {
            "name": "Port {port} Traffic Received",
            "native_unit_of_measurement": UnitOfInformation.MEGABYTES,
            # 'unit_of_measurement': UnitOfInformation.GIGABYTES,
            "device_class": SensorDeviceClass.DATA_SIZE,
            "icon": "mdi:download",
        },
        "port_{port}_traffic_tx_mbytes": {
            "name": "Port {port} Traffic Transferred",
            "native_unit_of_measurement": UnitOfInformation.MEGABYTES,
            # 'unit_of_measurement': UnitOfInformation.GIGABYTES,
            "device_class": SensorDeviceClass.DATA_SIZE,
            "icon": "mdi:upload",
        },
        "port_{port}_speed_rx_mbytes": {
            "name": "Port {port} Receiving",
            "native_unit_of_measurement": UnitOfDataRate.MEGABYTES_PER_SECOND,
            # 'unit_of_measurement': UnitOfInformation.GIGABYTES,
            "device_class": SensorDeviceClass.DATA_RATE,
            "icon": "mdi:download",
        },
        "port_{port}_speed_tx_mbytes": {
            "name": "Port {port} Transferring",
            "native_unit_of_measurement": UnitOfDataRate.MEGABYTES_PER_SECOND,
            # 'unit_of_measurement': UnitOfInformation.GIGABYTES,
            "device_class": SensorDeviceClass.DATA_RATE,
            "icon": "mdi:upload",
        },
        "port_{port}_speed_io_mbytes": {
            "name": "Port {port} IO",
            "native_unit_of_measurement": UnitOfDataRate.MEGABYTES_PER_SECOND,
            # 'unit_of_measurement': UnitOfInformation.GIGABYTES,
            "device_class": SensorDeviceClass.DATA_RATE,
            "icon": "mdi:swap-vertical",
        },
        "port_{port}_sum_rx_mbytes": {
            "name": "Port {port} Total Received",
            "native_unit_of_measurement": UnitOfInformation.MEGABYTES,
            "unit_of_measurement": UnitOfInformation.GIGABYTES,
            "device_class": SensorDeviceClass.DATA_SIZE,
            "icon": "mdi:download",
        },
        "port_{port}_sum_tx_mbytes": {
            "name": "Port {port} Total Transferred",
            "native_unit_of_measurement": UnitOfInformation.MEGABYTES,
            "unit_of_measurement": UnitOfInformation.GIGABYTES,
            "device_class": SensorDeviceClass.DATA_SIZE,
            "icon": "mdi:upload",
        },
        # "port_{port}_status": {
        #    "name": "Port {port} Status",
        #    # "native_unit_of_measurement": BinarySensorDeviceClass.CONNECTIVITY,
        #    "device_class": BinarySensorDeviceClass.CONNECTIVITY,
        #    #'icon': "mdi:upload"
        # },
        "port_{port}_connection_speed": {
            "name": "Port {port} Connection Speed",
            "native_unit_of_measurement": UnitOfDataRate.MEGABYTES_PER_SECOND,
            "device_class": SensorDeviceClass.DATA_RATE,
            #'icon': "mdi:upload"
        },
    }
)

AGGREGATED_SENSORS = OrderedDict(
    {
        "sum_port_speed_bps_io": {
            "name": "Switch IO",
            "native_unit_of_measurement": UnitOfDataRate.MEGABYTES_PER_SECOND,
            "device_class": SensorDeviceClass.DATA_RATE,
            #'icon': "mdi:upload"
        },
        "sum_port_traffic_rx": {
            "name": "Switch Traffic Received",
            "native_unit_of_measurement": UnitOfInformation.MEGABYTES,
            "device_class": SensorDeviceClass.DATA_SIZE,
            "icon": "mdi:download",
        },
        "sum_port_traffic_tx": {
            "name": "Switch Traffic Transferred",
            "native_unit_of_measurement": UnitOfInformation.MEGABYTES,
            "device_class": SensorDeviceClass.DATA_SIZE,
            "icon": "mdi:upload",
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

    for description in DEVICE_SENSOR_TYPES:
        descr_entity = NetgearRouterSensorEntity(
            coordinator=coordinator_switch_infos,
            switch=gs_switch,
            entity_description=description,
        )
        switch_entities.append(descr_entity)

    ports_cnt = gs_switch.api.ports
    _LOGGER.info(
        "[sensor.async_setup_entry] setting up Platform.SENSOR for %d Switch Ports",
        ports_cnt,
    )

    entity_descriptions_kwargs = []

    # Adding port sensors
    for i in range(ports_cnt):
        port_nr = i + 1
        for port_sensor_key, port_sensor_data in PORT_TEMPLATE.items():
            entity_descriptions_kwargs.append(
                {
                    "key": port_sensor_key.format(port=port_nr),
                    "name": port_sensor_data["name"].format(port=port_nr),
                    "native_unit_of_measurement": port_sensor_data.get(
                        "native_unit_of_measurement", None
                    ),
                    "unit_of_measurement": port_sensor_data.get(
                        "unit_of_measurement", None
                    ),
                    "device_class": port_sensor_data["device_class"],
                    "icon": port_sensor_data.get("icon"),
                }
            )

    # Adding aggregated sensors
    for sensor_key, sensor_data in AGGREGATED_SENSORS.items():
        entity_descriptions_kwargs.append(
            {
                "key": sensor_key,
                "name": sensor_data["name"],
                "native_unit_of_measurement": sensor_data["native_unit_of_measurement"],
                "unit_of_measurement": sensor_data.get("unit_of_measurement", None),
                "device_class": sensor_data["device_class"],
                "icon": sensor_data.get("icon"),
            }
        )

    for description_kwargs in entity_descriptions_kwargs:
        description = NetgearSensorEntityDescription(**description_kwargs)
        port_sensor_entity = NetgearRouterSensorEntity(
            coordinator=coordinator_switch_infos,
            switch=gs_switch,
            entity_description=description,
        )
        switch_entities.append(port_sensor_entity)

    async_add_entities(switch_entities)
    # commented next line, why was it there???
    # coordinator_switch_infos.data = True
