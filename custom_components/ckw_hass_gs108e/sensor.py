"""Support for Netgear routers."""
from __future__ import annotations

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

SENSOR_TYPES = {
    "link_rate": SensorEntityDescription(
        key="link_rate",
        name="link rate",
        native_unit_of_measurement="Mbps",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:speedometer",
    ),
}


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
    
    #NetgearSensorEntityDescription(
    #    key="NewOOKLADownlinkBandwidth",
    #    name="Downlink Bandwidth",
    #    entity_category=EntityCategory.DIAGNOSTIC,
    #    native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
    #    device_class=SensorDeviceClass.DATA_RATE,
    #    icon="mdi:download",
    #),
]

PORT_SENSORS = [
    NetgearSensorEntityDescription(
        key="port_1_traffic_rx_bytes",
        name="Port 1 Traffic Received",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_1_traffic_tx_bytes",
        name="Port 1 Traffic Transferred",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_1_speed_rx_bytes",
        name="Port 1 Receiving",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_1_speed_tx_bytes",
        name="Port 1 Transferring",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_1_speed_io_bytes",
        name="Port 1 IO",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:swap-vertical",
    ),
    NetgearSensorEntityDescription(
        key="port_2_traffic_rx_bytes",
        name="Port 2 Traffic Received",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_2_traffic_tx_bytes",
        name="Port 2 Traffic Transferred",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_2_speed_rx_bytes",
        name="Port 2 Receiving",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_2_speed_tx_bytes",
        name="Port 2 Transferring",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_2_speed_io_bytes",
        name="Port 2 IO",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:swap-vertical",
    ),
    NetgearSensorEntityDescription(
        key="port_3_traffic_rx_bytes",
        name="Port 3 Traffic Received",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_3_traffic_tx_bytes",
        name="Port 3 Traffic Transferred",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_3_speed_rx_bytes",
        name="Port 3 Receiving",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_3_speed_tx_bytes",
        name="Port 3 Transferring",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_3_speed_io_bytes",
        name="Port 3 IO",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:swap-vertical",
    ),
    NetgearSensorEntityDescription(
        key="port_4_traffic_rx_bytes",
        name="Port 4 Traffic Received",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_4_traffic_tx_bytes",
        name="Port 4 Traffic Transferred",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_4_speed_rx_bytes",
        name="Port 4 Receiving",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_4_speed_tx_bytes",
        name="Port 4 Transferring",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_4_speed_io_bytes",
        name="Port 4 IO",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:swap-vertical",
    ),
    NetgearSensorEntityDescription(
        key="port_5_traffic_rx_bytes",
        name="Port 5 Traffic Received",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_5_traffic_tx_bytes",
        name="Port 5 Traffic Transferred",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_5_speed_rx_bytes",
        name="Port 5 Receiving",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_5_speed_tx_bytes",
        name="Port 5 Transferring",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_5_speed_io_bytes",
        name="Port 5 IO",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:swap-vertical",
    ),
    NetgearSensorEntityDescription(
        key="port_6_traffic_rx_bytes",
        name="Port 6 Traffic Received",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_6_traffic_tx_bytes",
        name="Port 6 Traffic Transferred",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_6_speed_rx_bytes",
        name="Port 6 Receiving",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_6_speed_tx_bytes",
        name="Port 6 Transferring",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_6_speed_io_bytes",
        name="Port 6 IO",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:swap-vertical",
    ),
    NetgearSensorEntityDescription(
        key="port_7_traffic_rx_bytes",
        name="Port 7 Traffic Received",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_7_traffic_tx_bytes",
        name="Port 7 Traffic Transferred",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_7_speed_rx_bytes",
        name="Port 7 Receiving",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_7_speed_tx_bytes",
        name="Port 7 Transferring",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_7_speed_io_bytes",
        name="Port 7 IO",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:swap-vertical",
    ),
    NetgearSensorEntityDescription(
        key="port_8_traffic_rx_bytes",
        name="Port 8 Traffic Received",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_8_traffic_tx_bytes",
        name="Port 8 Traffic Transferred",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_8_speed_rx_bytes",
        name="Port 8 Receiving",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:download",
    ),
    NetgearSensorEntityDescription(
        key="port_8_speed_tx_bytes",
        name="Port 8 Transferring",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:upload",
    ),
    NetgearSensorEntityDescription(
        key="port_8_speed_io_bytes",
        name="Port 8 IO",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:swap-vertical",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up device tracker for Netgear component."""
    gs_switch = hass.data[DOMAIN][entry.entry_id][KEY_SWITCH]
    coordinator_switch_infos = hass.data[DOMAIN][entry.entry_id][KEY_COORDINATOR_SWITCH_INFOS]

    # Router entities
    switch_entities = []

    for description in DEVICE_SENSOR_TYPES:
        switch_entities.append(
            NetgearRouterSensorEntity(coordinator_switch_infos, gs_switch, description)
        )

    for description in PORT_SENSORS:
        switch_entities.append(
            NetgearRouterSensorEntity(coordinator_switch_infos, gs_switch, description)
        )

    async_add_entities(switch_entities)

    # Entities per network device
    tracked = set()
    sensors = ["link_rate"]

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
