"""Editable Netgear Plus port settings select entities."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from py_netgear_plus import (
    PORT_SPEED_100_FULL,
    PORT_SPEED_100_HALF,
    PORT_SPEED_10_FULL,
    PORT_SPEED_10_HALF,
    PORT_SPEED_AUTO,
    PORT_SPEED_DISABLED,
)

from . import NetgearSwitchConfigEntry
from .netgear_switch import HomeAssistantNetgearSwitch, NetgearAPICoordinatorEntity

_LOGGER = logging.getLogger(__name__)

SPEED_TO_OPTION = {
    PORT_SPEED_AUTO: "Auto",
    PORT_SPEED_DISABLED: "Disabled",
    PORT_SPEED_10_HALF: "10 Mbps half duplex",
    PORT_SPEED_10_FULL: "10 Mbps full duplex",
    PORT_SPEED_100_HALF: "100 Mbps half duplex",
    PORT_SPEED_100_FULL: "100 Mbps full duplex",
}
OPTION_TO_SPEED = {option: speed for speed, option in SPEED_TO_OPTION.items()}


# GS308EP rate-limit values are dropdown option codes used by the switch.
RATE_TO_OPTION = {
    1: "No Limit",
    2: "512 Kbit/s",
    3: "1 Mbit/s",
    4: "2 Mbit/s",
    5: "4 Mbit/s",
    6: "8 Mbit/s",
    7: "16 Mbit/s",
    8: "32 Mbit/s",
    9: "64 Mbit/s",
    10: "128 Mbit/s",
    11: "256 Mbit/s",
    12: "512 Mbit/s",
}
OPTION_TO_RATE = {option: rate for rate, option in RATE_TO_OPTION.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: NetgearSwitchConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up editable port speed selects."""
    del hass
    gs_switch = config_entry.runtime_data.gs_switch
    coordinator = config_entry.runtime_data.coordinator_switch_infos

    if (
        not gs_switch.api
        or not gs_switch.api.ports
        or gs_switch.api.switch_model.MODEL_NAME != "GS308EP"
    ):
        return

    entities: list[SelectEntity] = []
    for port in range(1, gs_switch.api.ports + 1):
        entities.extend(
            (
                NetgearPortSpeedSelectEntity(coordinator, gs_switch, port),
                NetgearPortRateLimitSelectEntity(
                    coordinator,
                    gs_switch,
                    port,
                    direction="ingress",
                ),
                NetgearPortRateLimitSelectEntity(
                    coordinator,
                    gs_switch,
                    port,
                    direction="egress",
                ),
            )
        )

    async_add_entities(entities)


class NetgearPortSpeedSelectEntity(NetgearAPICoordinatorEntity, SelectEntity):
    """Select entity for a port's configured speed and enabled state."""

    _attr_options = list(OPTION_TO_SPEED)
    _attr_icon = "mdi:ethernet"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        hub: HomeAssistantNetgearSwitch,
        port_nr: int,
    ) -> None:
        """Initialize the port speed select."""
        super().__init__(coordinator, hub)
        self.hub = hub
        self.port_nr = port_nr
        self._unique_id = f"{hub.unique_id}-port_{port_nr}_speed"
        self._attr_current_option = None
        self.async_update_device()

    @property
    def name(self) -> str:
        """Return the entity name, including the configured port description."""
        data = self.coordinator.data or {}
        description = str(
            data.get(f"port_{self.port_nr}_setting_name")
            or data.get(f"port_{self.port_nr}_description")
            or ""
        ).strip()
        base = f"Port {self.port_nr} Speed"
        return f"{base} ({description})" if description else base

    @callback
    def async_update_device(self) -> None:
        """Update the selected option from coordinator data."""
        data = self.coordinator.data or {}
        speed = data.get(f"port_{self.port_nr}_setting_speed")
        try:
            speed = int(speed)
        except (TypeError, ValueError):
            self._attr_current_option = None
            return
        self._attr_current_option = SPEED_TO_OPTION.get(speed)

    async def async_select_option(self, option: str) -> None:
        """Set the configured port speed."""
        speed = OPTION_TO_SPEED.get(option)
        if speed is None:
            raise HomeAssistantError(f"Unsupported port speed option: {option}")

        successful = await self.hub.async_call_api(
            self.hub.api.set_port_settings,
            self.port_nr,
            speed=speed,
        )
        if not successful:
            raise HomeAssistantError(
                f"Changing speed for port {self.port_nr} to {option} failed"
            )

        self._attr_current_option = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class NetgearPortRateLimitSelectEntity(NetgearAPICoordinatorEntity, SelectEntity):
    """Select entity for a GS308EP port ingress or egress rate limit."""

    _attr_options = list(OPTION_TO_RATE)
    _attr_icon = "mdi:speedometer"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        hub: HomeAssistantNetgearSwitch,
        port_nr: int,
        *,
        direction: str,
    ) -> None:
        """Initialize a port rate-limit select."""
        if direction not in {"ingress", "egress"}:
            raise ValueError(f"Unsupported rate-limit direction: {direction}")

        super().__init__(coordinator, hub)
        self.hub = hub
        self.port_nr = port_nr
        self.direction = direction
        self._unique_id = (
            f"{hub.unique_id}-port_{port_nr}_{direction}_rate_limit"
        )
        label = "In Rate Limit" if direction == "ingress" else "Out Rate Limit"
        self._name = f"Port {port_nr} {label}"
        self._attr_current_option = None
        self.async_update_device()

    @callback
    def async_update_device(self) -> None:
        """Update the selected rate limit from coordinator data."""
        data = self.coordinator.data or {}
        key = f"port_{self.port_nr}_setting_{self.direction}_rate"
        rate = data.get(key)

        try:
            rate = int(rate)
        except (TypeError, ValueError):
            self._attr_current_option = None
            return

        self._attr_current_option = RATE_TO_OPTION.get(rate)

    async def async_select_option(self, option: str) -> None:
        """Set the configured port rate limit."""
        rate = OPTION_TO_RATE.get(option)
        if rate is None:
            raise HomeAssistantError(f"Unsupported rate-limit option: {option}")

        kwargs = {f"{self.direction}_rate": rate}
        successful = await self.hub.async_call_api(
            self.hub.api.set_port_settings,
            self.port_nr,
            **kwargs,
        )
        if not successful:
            label = "in" if self.direction == "ingress" else "out"
            raise HomeAssistantError(
                f"Changing {label} rate limit for port {self.port_nr} "
                f"to {option} failed"
            )

        self._attr_current_option = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
