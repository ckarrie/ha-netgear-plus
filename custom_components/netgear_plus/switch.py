import logging

from homeassistant.components.switch import SwitchDeviceClass

from . import const
from .netgear_plus.models import GS3xxSeries
from .netgear_entities import (
    HomeAssistantNetgearSwitch,
    NetgearBinarySensorEntityDescription,
    NetgearPOESwitchEntity,
    NetgearSensorEntityDescription,
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

    if (
        isinstance(gs_switch.api.switch_model, GS3xxSeries)
        and gs_switch.api.poe_ports is not None
    ):
        for poe_port in gs_switch.api.poe_ports:
            # poe_port_power_status = port_{poe_port_nr}_poe_power
            switch_entity = NetgearPOESwitchEntity(
                coordinator=coordinator_switch_infos,
                hub=gs_switch,
                entity_description=NetgearBinarySensorEntityDescription(
                    key=f"port_{poe_port}_poe_power_active",
                    name=f"Port {poe_port} POE Power",
                    device_class=SwitchDeviceClass.OUTLET,
                    # value=gs_switch.api._loaded_switch_infos,
                    # value="off",
                ),
                port_nr=poe_port,
            )

            entities.append(switch_entity)

    async_add_entities(entities)
