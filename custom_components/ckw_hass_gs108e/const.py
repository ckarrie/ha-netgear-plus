from homeassistant.const import Platform
DOMAIN = 'ckw_hass_gs108e'

PLATFORMS = [
    Platform.SENSOR,
]

DEFAULT_NAME = "Netgear GS108E Switch"
SCAN_INTERVAL = 10
TIMEOUT = 2
DEFAULT_HOST = "192.168.178.5"
DEFAULT_USER = "admin"
DEFAULT_PASSWORD = 'password'
KEY_COORDINATOR_SWITCH_INFOS = 'coordinator_switch_infos'
KEY_SWITCH = "switch"