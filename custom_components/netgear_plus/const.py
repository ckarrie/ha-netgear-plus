"""HomeAssistant Config Flow."""

from datetime import timedelta

from homeassistant.const import Platform

from .netgear_plus import models

DOMAIN = "netgear_plus"

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.SWITCH, Platform.BUTTON]

DEFAULT_NAME = "Netgear Plus Switch"
SCAN_INTERVAL = 10
DEFAULT_CONF_TIMEOUT = timedelta(seconds=15)
DEFAULT_HOST = "192.168.178.5"
DEFAULT_USER = "admin"
DEFAULT_PASSWORD = "password"  # noqa: S105
KEY_COORDINATOR_SWITCH_INFOS = "coordinator_switch_infos"
KEY_SWITCH = "switch"
SUPPORTED_MODELS = models.MODELS
ON_VALUES = ["on", True]
OFF_VALUES = ["off", False]
