from __future__ import annotations

from abc import abstractmethod
import asyncio
import requests
from lxml import html
from typing import Any
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo, Entity

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
)



from .errors import CannotLoginException
from .const import DOMAIN

LOGIN_URL_TMPL = 'http://{ip}/login.cgi'
PORT_STATISTICS_URL_TMPL = 'http://{ip}/portStatistics.cgi'
ALLOWED_COOKIE_TYPES = ['GS108SID', 'SID']


class GS108Switch(object):
    def __init__(self, host, password):
        self.host = host
        self.password = password
        self.cookie_name = None
        self.cookie_content = None
        self.sleep_time = 0.25
        self.timeout = 15.000

    def get_unique_id(self):
        return 'gs108_' + self.host.replace('.', '_')

    def get_login_cookie(self):
        response = requests.post(
            LOGIN_URL_TMPL.format(ip=self.host),
            data=dict(password=self.password),
            allow_redirects=True
        )
        for ct in ALLOWED_COOKIE_TYPES:
            cookie = response.cookies.get(ct, None)
            if cookie:
                self.cookie_name = ct
                self.cookie_content = cookie
                return True
        return False

    def fetch_port_statistics(self):
        # Set up our cookie jar
        jar = requests.cookies.RequestsCookieJar()
        jar.set(self.cookie_name, self.cookie_content, domain=self.host, path='/')
        try:
            page = requests.get(
                PORT_STATISTICS_URL_TMPL.format(ip=self.host),
                cookies=jar,
                timeout=self.timeout
            )
            return page
        except requests.exceptions.Timeout:
            return None

    def get_switch_infos(self):
        page = self.fetch_port_statistics()
        if not page:
            return None

        _start_time = time.perf_counter()

        # Parse content
        tree = html.fromstring(page.content)
        rx1 = tree.xpath('//tr[@class="portID"]/td[2]')
        tx1 = tree.xpath('//tr[@class="portID"]/td[3]')
        crc1 = tree.xpath('//tr[@class="portID"]/td[4]')

        # Hold fire
        time.sleep(self.sleep_time)

        # Get the port stats page again! We need to compare two points in time
        page = self.fetch_port_statistics()
        if not page:
            return None

        _end_time = time.perf_counter()
        tree = html.fromstring(page.content)

        rx2 = tree.xpath('//tr[@class="portID"]/td[2]')
        tx2 = tree.xpath('//tr[@class="portID"]/td[3]')
        crc2 = tree.xpath('//tr[@class="portID"]/td[4]')

        sample_time = _end_time - _start_time
        sample_factor = 1 / sample_time

        # Port data
        ports = min([len(tx1), len(tx2)])

        sum_port_traffic_rx = 0
        sum_port_traffic_tx = 0
        sum_port_traffic_crc_err = 0
        sum_port_speed_bps_rx = 0
        sum_port_speed_bps_tx = 0

        switch_data = {
            'switch_ip': self.host,
            'response_time_s': sample_time,
        }

        for port_number0 in range(ports):
            try:
                port_number = port_number0 + 1
                port_traffic_rx = int(rx2[port_number0].text, 10) - int(rx1[port_number0].text, 10)
                port_traffic_tx = int(tx2[port_number0].text, 10) - int(tx1[port_number0].text, 10)
                port_traffic_crc_err = int(crc2[port_number0].text, 10) - int(crc1[port_number0].text, 10)
                port_speed_bps_rx = int(port_traffic_rx * sample_factor)
                port_speed_bps_tx = int(port_traffic_tx * sample_factor)
            except IndexError:
                print("IndexError at port_number0", port_number0)
                continue

            # Lowpass-Filter
            if port_traffic_rx < 0:
                port_traffic_rx = 0
            if port_traffic_tx < 0:
                port_traffic_tx = 0
            if port_traffic_crc_err < 0:
                port_traffic_crc_err = 0
            if port_speed_bps_rx < 0:
                port_speed_bps_rx = 0
            if port_speed_bps_tx < 0:
                port_speed_bps_tx = 0

            sum_port_traffic_rx += port_traffic_rx
            sum_port_traffic_tx += port_traffic_tx
            sum_port_traffic_crc_err += port_traffic_crc_err
            sum_port_speed_bps_rx += port_speed_bps_rx
            sum_port_speed_bps_tx += port_speed_bps_tx

            switch_data[f'port_{port_number}_traffic_rx_bytes'] = port_traffic_rx
            switch_data[f'port_{port_number}_traffic_tx_bytes'] = port_traffic_tx
            switch_data[f'port_{port_number}_speed_rx_bytes'] = port_speed_bps_rx
            switch_data[f'port_{port_number}_speed_tx_bytes'] = port_speed_bps_tx
            switch_data[f'port_{port_number}_speed_io_bytes'] = port_speed_bps_rx + port_speed_bps_tx
            switch_data[f'port_{port_number}_crc_errors'] = port_traffic_crc_err

        switch_data['sum_port_traffic_rx'] = sum_port_traffic_rx
        switch_data['sum_port_traffic_tx'] = sum_port_traffic_tx
        switch_data['sum_port_traffic_crc_err'] = sum_port_traffic_crc_err
        switch_data['sum_port_speed_bps_rx'] = sum_port_speed_bps_rx
        switch_data['sum_port_speed_bps_tx'] = sum_port_speed_bps_tx
        switch_data['sum_port_speed_bps_io'] = sum_port_speed_bps_rx + sum_port_speed_bps_tx
        return switch_data


def get_api(host: str, password: str) -> GS108Switch:
    """Get the Netgear API and login to it."""
    api: GS108Switch = GS108Switch(host, password)

    if not api.get_login_cookie():
        raise CannotLoginException

    return api


class HAGS108Switch:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        assert entry.unique_id
        self.hass = hass
        self.entry = entry
        self.entry_id = entry.entry_id
        self.unique_id = entry.unique_id
        self.device_name = entry.title
        self.model = "GS108E"
        self._host: str = entry.data[CONF_HOST]
        self._password = entry.data[CONF_PASSWORD]

        self.api: GS108Switch = None
        self.api_lock = asyncio.Lock()

    def _setup(self) -> bool:
        self.api = get_api(
            host=self._host,
            password=self._password
        )
        return True

    async def async_setup(self) -> bool:
        async with self.api_lock:
            if not await self.hass.async_add_executor_job(self._setup):
                return False
        return True

    async def async_get_switch_infos(self) -> dict[str, Any] | None:
        async with self.api_lock:
            return await self.hass.async_add_executor_job(self.api.get_switch_infos)


class HAGS108SwitchCoordinatorEntity(CoordinatorEntity):
    """Base class for a Netgear router entity."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, switch: HAGS108Switch
    ) -> None:
        """Initialize a Netgear device."""
        super().__init__(coordinator)
        self._switch = switch
        self._name = switch.device_name
        self._unique_id = switch.unique_id

    @abstractmethod
    @callback
    def async_update_device(self) -> None:
        """Update the Netgear device."""

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_update_device()
        super()._handle_coordinator_update()

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name."""
        return self._name

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._switch.unique_id)},
        )


class HAGS108SwitchEntity(Entity):
    """Base class for a Netgear router entity without coordinator."""

    def __init__(self, switch: HAGS108Switch) -> None:
        """Initialize a Netgear device."""
        self._switch = switch
        self._name = switch.device_name
        self._unique_id = switch.unique_id

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name."""
        return self._name

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._switch.unique_id)},
        )

