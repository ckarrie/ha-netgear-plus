import logging

from homeassistant.components.button import ButtonDeviceClass

from . import const
from .netgear_entities import (
    HomeAssistantNetgearSwitch,
    NetgearButtonEntityDescription,
    NetgearPoEPowerCycleButtonEntity,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the switch from config_entry."""
    entities = []
    gs_switch: HomeAssistantNetgearSwitch = hass.data[const.DOMAIN][
        config_entry.entry_id
    ][const.KEY_SWITCH]
    coordinator_switch_infos = hass.data[const.DOMAIN][config_entry.entry_id][
        const.KEY_COORDINATOR_SWITCH_INFOS
    ]

    _LOGGER.debug(
        f"called async_setup_entry for ButtonDeviceClass"
    )

    if gs_switch.api.poe_ports and len(gs_switch.api.poe_ports) > 0:
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

            _LOGGER.debug(
                f"Added NetgearPoEPowerCycleButtonEntity for port {poe_port}."
            )

    async_add_entities(entities)
