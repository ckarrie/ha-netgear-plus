"""Entity defitions for Netgear Plus Switches."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.components.sensor import (
    RestoreSensor,
    SensorEntityDescription,
)
from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import const
from .netgear_switch import (
    HomeAssistantNetgearSwitch,
    NetgearAPICoordinatorEntity,
    NetgearCoordinatorEntity,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class NetgearSensorEntityDescription(SensorEntityDescription):
    """Describes Netgear sensor entities."""

    value: Callable = lambda data: data
    index: int = 0


@dataclass(frozen=True)
class NetgearBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Netgear binary sensor entities."""

    value: Callable = lambda data: data
    index: int = 0

    device_class: BinarySensorDeviceClass | str | None = None
    last_reset: datetime | None = None
    native_unit_of_measurement: str | None = None
    options: list[str] | None = None
    state_class: SensorStateClass | str | None = None
    suggested_display_precision: int | None = None
    suggested_unit_of_measurement: str | None = None
    unit_of_measurement: None = None  # Type override, use native_unit_of_measurement
    native_precision = None


@dataclass(frozen=True)
class NetgearButtonEntityDescription(ButtonEntityDescription):
    """Describes Netgear button entities."""

    cls: type | None = None
    device_class: ButtonDeviceClass | None = None
    index: int = 0


class NetgearRouterSensorEntity(NetgearAPICoordinatorEntity, RestoreSensor):
    """Representation of a device connected to a Netgear router."""

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

    def __repr__(self) -> str:
        """Return human readable object representation."""
        return f"<NetgearNetgearRouterSensorEntity unique_id={self._unique_id}>"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
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


class NetgearRouterBinarySensorEntity(NetgearAPICoordinatorEntity, BinarySensorEntity):
    """Representation of a device connected to a Netgear router."""

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

    def __repr__(self) -> str:
        """Return human readable object representation."""
        return f"<NetgearRouterBinarySensorEntity unique_id={self._unique_id}>"

    @property
    def native_value(self) -> StateType | bool:
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
        """Return entity availability."""
        return True

    @property
    def is_on(self) -> bool:
        """Return binary sensor state."""
        return self._value in const.ON_VALUES

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


class NetgearPOESwitchEntity(NetgearAPICoordinatorEntity, SwitchEntity):
    """Represents a POE On/Off Power Switch in HomeAssistant."""

    entity_description: NetgearBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        hub: HomeAssistantNetgearSwitch,
        entity_description: NetgearBinarySensorEntityDescription,
        port_nr: int | None = None,
    ) -> None:
        """Initialize a Netgear device."""
        super().__init__(coordinator, hub)
        self.entity_description = entity_description
        self._name = f"{hub.device_name} {entity_description.name}"
        self._unique_id = (
            f"{hub.unique_id}-{entity_description.key}-{entity_description.index}"
        )
        self.port_nr = port_nr
        self._value = None
        self.hub = hub

    def __repr__(self) -> str:
        """Return human readable object representation."""
        return f"<NetgearPOESwitchEntity \
unique_id={self._unique_id} port_nr={self.port_nr}>"

    @callback
    def async_update_device(self) -> None:
        """Update entities with data from switch."""
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

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._value in const.ON_VALUES

    async def async_turn_on(self, **kwargs: dict[str, Any]) -> None:  # noqa: ARG002
        """Enable power on PoE port."""
        if self.port_nr:
            successful = await self.hub.hass.async_add_executor_job(
                self.hub.api.turn_on_poe_port, self.port_nr
            )
            self._value = "on" if successful else "off"
            _LOGGER.info(
                "called turn_on_poe_port for uid=%s port=%s: successful=%s",
                self._unique_id,
                self.port_nr,
                successful,
            )

    async def async_turn_off(self, **kwargs: dict[str, Any]) -> None:  # noqa: ARG002
        """Disable power on PoE port."""
        if self.port_nr:
            successful = self.hub.hass.async_add_executor_job(
                self.hub.api.turn_off_poe_port, self.port_nr
            )
            self._value = "off" if successful else "on"
            _LOGGER.info(
                "called turn_off_poe_port for uid=%s port=%s: successful=%s",
                self._unique_id,
                self.port_nr,
                successful,
            )


class NetgearPoEPowerCycleButtonEntity(NetgearCoordinatorEntity, ButtonEntity):
    """Represents a PoE Power Cycle Button in HomeAssistant."""

    entity_description: NetgearButtonEntityDescription
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        hub: HomeAssistantNetgearSwitch,
        entity_description: NetgearButtonEntityDescription,
        port_nr: int | None = None,
    ) -> None:
        """Initialize a Netgear device."""
        super().__init__(coordinator, hub)
        self.entity_description = entity_description
        self._name = f"{hub.device_name} {entity_description.name}"
        self._unique_id = (
            f"{hub.unique_id}-{entity_description.key}-{entity_description.index}"
        )
        self.port_nr = port_nr
        self.hub = hub

    def __repr__(self) -> str:
        """Return human readable object representation."""
        return f"<NetgearPoEPowerCycleButtonEntity \
unique_id={self._unique_id} port_nr={self.port_nr}>"

    async def async_press(self) -> None:
        """Power Cycle Port."""
        if self.port_nr:
            successful = await self.hub.hass.async_add_executor_job(
                self.hub.api.power_cycle_poe_port, self.port_nr
            )
            _LOGGER.info(
                "called power_cycle_poe_port for uid=%s port=%s: successful=%s",
                self._unique_id,
                self.port_nr,
                successful,
            )
            if not successful:
                message = f"Running command 'power_cycle_poe_port' \
for port {self.port_nr} failed"
                raise HomeAssistantError(message)

            await self.coordinator.async_request_refresh()
