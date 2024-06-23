from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .netgear_switch import HAGS108SwitchCoordinatorEntity, HomeAssistantNetgearSwitch

_LOGGER = logging.getLogger(__name__)


@dataclass
class NetgearSensorEntityDescription(SensorEntityDescription):
    """Class describing Netgear sensor entities."""

    value: Callable = lambda data: data
    index: int = 0


@dataclass
class NetgearBinarySensorEntityDescription(BinarySensorEntityDescription):
    value: Callable = lambda data: data
    index: int = 0

    device_class: SensorDeviceClass | None = None
    last_reset: datetime | None = None
    native_unit_of_measurement: str | None = None
    options: list[str] | None = None
    state_class: SensorStateClass | str | None = None
    suggested_display_precision: int | None = None
    suggested_unit_of_measurement: str | None = None
    unit_of_measurement: None = None  # Type override, use native_unit_of_measurement
    native_precision = None


class NetgearRouterSensorEntity(HAGS108SwitchCoordinatorEntity, RestoreSensor):
    """Representation of a device connected to a Netgear router."""

    # _attr_entity_registry_enabled_default = False
    entity_description: NetgearSensorEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        switch: HomeAssistantNetgearSwitch,
        entity_description: NetgearSensorEntityDescription,
    ) -> None:
        """Initialize a Netgear device."""
        super().__init__(coordinator, switch)
        self.entity_description = entity_description
        self._name = f"{switch.device_name} {entity_description.name}"
        self._unique_id = (
            f"{switch.unique_id}-{entity_description.key}-{entity_description.index}"
        )
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


class NetgearRouterBinarySensorEntity(
    HAGS108SwitchCoordinatorEntity, BinarySensorEntity
):
    """Representation of a device connected to a Netgear router."""

    # _attr_entity_registry_enabled_default = False
    entity_description: NetgearBinarySensorEntityDescription
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        switch: HomeAssistantNetgearSwitch,
        entity_description: NetgearBinarySensorEntityDescription,
    ) -> None:
        """Initialize a Netgear device."""
        super().__init__(coordinator, switch)
        self.entity_description = entity_description
        self._name = f"{switch.device_name} {entity_description.name}"
        self._unique_id = (
            f"{switch.unique_id}-{entity_description.key}-{entity_description.index}"
        )
        self._value: StateType | bool | str = None
        self._attr_is_on = False
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

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        """Return binary sensor state."""
        return self._value == "on"

    @callback
    def async_update_device(self) -> None:
        """Update the Netgear device."""
        if self.coordinator.data is None:
            return

        _value = self.coordinator.data.get(self.entity_description.key)

        if _value is None:
            self._value = None
            _LOGGER.debug(
                "key '%s' not in Netgear router response '%s'",
                self.entity_description.key,
                _value,
            )
            return

        self._value = _value
