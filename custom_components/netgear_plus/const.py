"""HomeAssistant Config Flow."""

from datetime import timedelta

from homeassistant.const import Platform

from .gs108e import models

DOMAIN = "netgear_plus"

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.SWITCH]

DEFAULT_NAME = "Netgear GS108E Switch"
SCAN_INTERVAL = 10
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
ON_VALUES = ["on", True]
OFF_VALUES = ["off", False]
