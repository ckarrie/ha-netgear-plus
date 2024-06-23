"""HomeAssistant Config Flow."""

from datetime import timedelta

from homeassistant.const import Platform

from .gs108e import models

DOMAIN = "ckw_hass_gs108e"

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]

DEFAULT_NAME = "Netgear GS108E Switch"
SCAN_INTERVAL = 30
DEFAULT_CONF_TIMEOUT = timedelta(seconds=15)
DEFAULT_HOST = "192.168.178.5"
DEFAULT_USER = "admin"
DEFAULT_PASSWORD = "password"
KEY_COORDINATOR_SWITCH_INFOS = "coordinator_switch_infos"
KEY_SWITCH = "switch"
SUPPORTED_MODELS = [
    # models.GS105E,
    # models.GS105Ev2,
    models.GS108E,
    models.GS108Ev3,
]
