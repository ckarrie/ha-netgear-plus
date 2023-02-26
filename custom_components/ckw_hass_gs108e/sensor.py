"""Support for Netgear routers."""
from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
import logging

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

from .const import (
    DOMAIN,
    KEY_COORDINATOR_SWITCH_INFOS,
    KEY_SWITCH,
)
from .netgear_switch import HAGS108Switch, HAGS108SwitchCoordinatorEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class NetgearSensorEntityDescription(SensorEntityDescription):
    """Class describing Netgear sensor entities."""

    value: Callable = lambda data: data
    index: int = 0


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

PORT_TEMPLATE = OrderedDict({
    'port_{port}_traffic_rx_mbytes': {
        'name': 'Port {port} Traffic Received',
        'native_unit_of_measurement': UnitOfInformation.MEGABYTES,
        # 'unit_of_measurement': UnitOfInformation.GIGABYTES,
        'device_class': SensorDeviceClass.DATA_SIZE,
        'icon': "mdi:download"
    },
    'port_{port}_traffic_tx_mbytes': {
        'name': 'Port {port} Traffic Transferred',
        'native_unit_of_measurement': UnitOfInformation.MEGABYTES,
        # 'unit_of_measurement': UnitOfInformation.GIGABYTES,
        'device_class': SensorDeviceClass.DATA_SIZE,
        'icon': "mdi:upload"
    },
    'port_{port}_speed_rx_mbytes': {
        'name': 'Port {port} Receiving',
        'native_unit_of_measurement': UnitOfDataRate.MEGABYTES_PER_SECOND,
        # 'unit_of_measurement': UnitOfInformation.GIGABYTES,
        'device_class': SensorDeviceClass.DATA_RATE,
        'icon': "mdi:download"
    },
    'port_{port}_speed_tx_mbytes': {
        'name': 'Port {port} Transferring',
        'native_unit_of_measurement': UnitOfDataRate.MEGABYTES_PER_SECOND,
        # 'unit_of_measurement': UnitOfInformation.GIGABYTES,
        'device_class': SensorDeviceClass.DATA_RATE,
        'icon': "mdi:upload"
    },
    'port_{port}_speed_io_mbytes': {
        'name': 'Port {port} Receiving',
        'native_unit_of_measurement': UnitOfDataRate.MEGABYTES_PER_SECOND,
        # 'unit_of_measurement': UnitOfInformation.GIGABYTES,
        'device_class': SensorDeviceClass.DATA_RATE,
        'icon': "mdi:swap-vertical"
    },
    'port_{port}_sum_rx_mbytes': {
        'name': 'Port {port} Total Received',
        'native_unit_of_measurement': UnitOfInformation.MEGABYTES,
        'unit_of_measurement': UnitOfInformation.GIGABYTES,
        'device_class': SensorDeviceClass.DATA_SIZE,
        'icon': "mdi:download"
    },
    'port_{port}_sum_tx_mbytes': {
        'name': 'Port {port} Total Transferred',
        'native_unit_of_measurement': UnitOfInformation.MEGABYTES,
        'unit_of_measurement': UnitOfInformation.GIGABYTES,
        'device_class': SensorDeviceClass.DATA_SIZE,
        'icon': "mdi:upload"
    },
})


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up device tracker for Netgear component."""
    gs_switch = hass.data[DOMAIN][entry.entry_id][KEY_SWITCH]
    coordinator_switch_infos = hass.data[DOMAIN][entry.entry_id][KEY_COORDINATOR_SWITCH_INFOS]

    # Router entities
    switch_entities = []

    for description in DEVICE_SENSOR_TYPES:
        descr_entity = NetgearRouterSensorEntity(
            coordinator=coordinator_switch_infos,
            switch=gs_switch,
            entity_description=description
        )
        switch_entities.append(descr_entity)

    ports_cnt = gs_switch.SWITCH_PORTS
    for i in range(ports_cnt):
        port_nr = i + 1
        for port_sensor_key, port_sensor_data in PORT_TEMPLATE.items():
            description = NetgearSensorEntityDescription(
                key=port_sensor_key.format(port=port_nr),
                name=port_sensor_data['name'].format(port=port_nr),
                native_unit_of_measurement=port_sensor_data['native_unit_of_measurement'],
                unit_of_measurement=port_sensor_data.get('unit_of_measurement', None),
                device_class=port_sensor_data['device_class'],
                icon=port_sensor_data['icon']
            )
            port_sensor_entity = NetgearRouterSensorEntity(
                coordinator=coordinator_switch_infos,
                switch=gs_switch,
                entity_description=description
            )
            switch_entities.append(port_sensor_entity)

    async_add_entities(switch_entities)
    coordinator_switch_infos.data = True


class NetgearRouterSensorEntity(HAGS108SwitchCoordinatorEntity, RestoreSensor):
    """Representation of a device connected to a Netgear router."""

    #_attr_entity_registry_enabled_default = False
    entity_description: NetgearSensorEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        switch: HAGS108Switch,
        entity_description: NetgearSensorEntityDescription,
    ) -> None:
        """Initialize a Netgear device."""
        super().__init__(coordinator, switch)
        self.entity_description = entity_description
        self._name = f"{switch.device_name} {entity_description.name}"
        self._unique_id = f"{switch.unique_id}-{entity_description.key}-{entity_description.index}"
        self._value: StateType | date | datetime | Decimal = None
        self.async_update_device()

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._value

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        if self.coordinator.data is None:
            sensor_data = await self.async_get_last_sensor_data()
            if sensor_data is not None:
                self._value = sensor_data.native_value

    @callback
    def async_update_device(self) -> None:
        """Update the Netgear device."""
        if self.coordinator.data is None:
            return

        data = self.coordinator.data.get(self.entity_description.key)
        if data is None:
            self._value = None
            _LOGGER.debug(
                "key '%s' not in Netgear router response '%s'",
                self.entity_description.key,
                data,
            )
            return

        self._value = self.entity_description.value(data)
