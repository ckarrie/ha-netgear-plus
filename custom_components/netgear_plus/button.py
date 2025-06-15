"""Module that sets up the button entities for the Netgear Plus integration."""

import logging

from homeassistant.components.button import ButtonDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NetgearSwitchConfigEntry
from .netgear_entities import (
    NetgearButtonEntityDescription,
    NetgearPoEPowerCycleButtonEntity,
    NetgearRebootButtonEntity,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: NetgearSwitchConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button from config_entry."""
    del hass
    entities = []
    gs_switch = config_entry.runtime_data.gs_switch
    coordinator_switch_infos = config_entry.runtime_data.coordinator_switch_infos

    if gs_switch.api:
        if gs_switch.api.switch_model.has_reboot_button():
            _LOGGER.info(
                "[button.async_setup_entry] setting up Platform.BUTTON for Switch Reboot"
            )
            entities.append(
                NetgearRebootButtonEntity(
                    coordinator=coordinator_switch_infos,
                    hub=gs_switch,
                    entity_description=NetgearButtonEntityDescription(
                        key="reboot",
                        name="Reboot Switch",
                        device_class=ButtonDeviceClass.RESTART,
                    ),
                )
            )

        n_poe_ports = 0
        if gs_switch.api.poe_ports:
            n_poe_ports = len(gs_switch.api.poe_ports)

        _LOGGER.info(
            "[button.async_setup_entry] setting up Platform.BUTTON for %s Switch Ports",
            n_poe_ports,
        )

        if n_poe_ports > 0:
            for poe_port in gs_switch.api.poe_ports:
                switch_entity = NetgearPoEPowerCycleButtonEntity(
                    coordinator=coordinator_switch_infos,
                    hub=gs_switch,
                    entity_description=NetgearButtonEntityDescription(
                        key=f"port_{poe_port}_poe_power_cycle",
                        name=f"Port {poe_port} PoE Power Cycle",
                        device_class=ButtonDeviceClass.RESTART,
                    ),
                    port_nr=poe_port,
                )

                entities.append(switch_entity)

    async_add_entities(entities)
