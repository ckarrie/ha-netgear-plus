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
    """Set up the Fritzbox smarthome switch from config_entry."""
    entities = []
    gs_switch: HomeAssistantNetgearSwitch = hass.data[const.DOMAIN][
        config_entry.entry_id
    ][const.KEY_SWITCH]
    coordinator_switch_infos = hass.data[const.DOMAIN][config_entry.entry_id][
        const.KEY_COORDINATOR_SWITCH_INFOS
    ]

    if gs_switch.api.poe_ports and len(gs_switch.api.poe_ports) > 0:
        for poe_port in gs_switch.api.poe_ports:
            # poe_port_power_status = port_{poe_port_nr}_poe_power
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
