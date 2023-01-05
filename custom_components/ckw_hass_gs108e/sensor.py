"""Support for monitoring a Netgear Switch."""
from datetime import timedelta
import logging

from .netgear_switch import HAGS108SwitchEntity, HAGS108Switch, HAGS108SwitchCoordinatorEntity
from requests.exceptions import RequestException
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_NAME, STATE_UNAVAILABLE, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

CONF_DEFAULT_NAME = "ckw_hass_gs108e"
CONF_DEFAULT_IP = "169.254.1.1"
CONF_DEFAULT_PASSWORD = "password"

ATTR_BYTES_RECEIVED = "bytes_received"
ATTR_BYTES_SENT = "bytes_sent"
ATTR_TRANSMISSION_RATE_UP = "transmission_rate_up"
ATTR_TRANSMISSION_RATE_DOWN = "transmission_rate_down"
ATTR_TRANSMISSION_RATE_IO = "transmission_rate_io"
ATTR_INTERNAL_IP = "internal_ip"
ATTR_PORTS = "ports"

ATTR_PORT_NR = "port_nr"
ATTR_PORT_BYTES_RECEIVED = "traffic_rx_bytes"
ATTR_PORT_BYTES_SENT = "traffic_tx_bytes"
ATTR_PORT_SPEED_TX = "speed_rx_bytes"
ATTR_PORT_SPEED_RX = "speed_tx_bytes"

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

STATE_ONLINE = "online"
STATE_OFFLINE = "offline"

ICON = "mdi:switch"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=CONF_DEFAULT_NAME): cv.string,
        vol.Optional(CONF_HOST, default=CONF_DEFAULT_IP): cv.string,
        vol.Optional(CONF_PASSWORD, default=CONF_DEFAULT_PASSWORD): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the FRITZ!Box monitor sensors."""
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    password = config.get(CONF_PASSWORD)

    try:
        switch_infos = get_switch_infos(switch_ip=host, switch_password=password)
    except (ValueError, TypeError):
        switch_infos = None

    if switch_infos is None:
        _LOGGER.error("Failed to establish connection to Netgear Switch: %s", host)
        return 1
    _LOGGER.info("Successfully connected to Netgear")

    add_entities([NetgearMonitorSensor(name, host, password)], True)


class NetgearMonitorSensor(Entity):
    """Implementation of a fritzbox monitor sensor."""

    def __init__(self, name, host, password):
        """Initialize the sensor."""
        self._name = name
        self._host = host
        self._password = password
        self._switch_infos = {}
        self._state = STATE_UNAVAILABLE
        self._internal_ip = None
        self._bytes_sent = self._bytes_received = None
        self._transmission_rate_up = None
        self._transmission_rate_down = None
        self._transmission_rate_io = None
        self._ports = []
        self._crc_errors = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name.rstrip()

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return ICON

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def state_attributes(self):
        """Return the device state attributes."""
        # Don't return attributes if FritzBox is unreachable
        if self._state == STATE_UNAVAILABLE:
            return {}
        attributes = {
            ATTR_INTERNAL_IP: self._host,
            ATTR_BYTES_SENT: self._bytes_sent,
            ATTR_BYTES_RECEIVED: self._bytes_received,
            ATTR_TRANSMISSION_RATE_UP: self._transmission_rate_up,
            ATTR_TRANSMISSION_RATE_DOWN: self._transmission_rate_down,
            ATTR_TRANSMISSION_RATE_IO: self._transmission_rate_io,
            ATTR_PORTS: len(self._ports),
        }

        for port in self._ports[:]:
            port_nr = port.pop('port_nr', None)
            if port_nr is not None:
                for k, v in port.items():
                    attr_keyname = '{}_{}_{}'.format(ATTR_PORTS, port_nr, k)
                    attributes[attr_keyname] = v

        return attributes

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Retrieve information from the FritzBox."""
        try:
            self._switch_infos = get_switch_infos(switch_ip=self._host, switch_password=self._password)
            if self._switch_infos:
                self._internal_ip = self._host
                self._bytes_sent = self._switch_infos.get('sum_port_traffic_tx')
                self._bytes_received = self._switch_infos.get('sum_port_traffic_rx')
                self._transmission_rate_up = self._switch_infos.get('sum_port_speed_bps_tx')
                self._transmission_rate_down = self._switch_infos.get('sum_port_speed_bps_rx')
                self._transmission_rate_io = self._switch_infos.get('sum_port_speed_bps_io')
                self._ports = self._switch_infos.get('ports', [])
                self._state = STATE_ONLINE
            else:
                self._bytes_sent = 0
                self._bytes_received = 0
                self._transmission_rate_up = 0
                self._transmission_rate_down = 0
                self._transmission_rate_io = 0
                self._ports = []
                self._state = STATE_UNAVAILABLE

        except RequestException as err:
            self._state = STATE_UNAVAILABLE
            _LOGGER.warning("Could not reach Netgear: %s", err)

        except (ValueError, TypeError):
            self._state = STATE_UNAVAILABLE

