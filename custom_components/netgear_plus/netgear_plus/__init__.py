"""Netgear API."""

import contextlib
import logging
import time
from typing import Any

import requests
import requests.cookies
from lxml import html

from . import models, netgear_crypt

SWITCH_STATES = ["on", "off"]

API_V2_CHECKS = {
    "bootloader": ["V1.00.03", "V2.06.01", "V2.06.02", "V2.06.03"],
    "firmware": ["V2.06.24GR", "V2.06.24EN"],
}


def _reduce_digits(v: float) -> float:
    bytes_to_mbytes = 1e-6
    return float(f"{round(v * bytes_to_mbytes, 2):.2f}")


PORT_STATUS_CONNECTED = ["Aktiv", "Up", "UP"]
PORT_MODUS_SPEED = ["Auto"]


_LOGGER = logging.getLogger(__name__)


class LoginFailedError(Exception):
    """Invalid credentials."""


class MultipleModelsDetectedError(Exception):
    """Detection of switch model was not unique."""


class SwitchModelNotDetectedError(Exception):
    """None of the models passed the tests."""


class NetgearSwitchConnector:
    """Representation of a Netgear Switch."""

    LOGIN_URL_REQUEST_TIMEOUT = 15

    def __init__(self, host: str, password: str) -> None:
        """Initialize Connector Object."""
        self.host = host

        # initial values
        self.switch_model = models.AutodetectedSwitchModel()
        self.ports = 0
        self.poe_ports = []
        self.port_status = {}
        self._switch_bootloader = "unknown"

        # sleep time between requests
        self.sleep_time = 0.25

        # plain login password
        self._password = password
        # response of login page request
        self._login_page_response = requests.Response()
        # cryped password if md5
        self._login_page_form_password = ""
        # cookie/hash data
        self.cookie_name = None
        self.cookie_content = None
        self._client_hash = ""

        # previous data calculation
        self._previous_timestamp = time.perf_counter()
        self._previous_data = {}

        # current data
        self._loaded_switch_infos = {}

    def autodetect_model(self) -> models.AutodetectedSwitchModel:
        """Detect switch model from login page contents."""
        _LOGGER.debug(
            "[NetgearSwitchConnector.autodetect_model] called for IP=%s", self.host
        )
        for template in models.AutodetectedSwitchModel.AUTODETECT_TEMPLATES:
            url = template["url"].format(ip=self.host)
            method = template["method"]

            response = requests.request(
                method,
                url,
                allow_redirects=False,
                timeout=self.LOGIN_URL_REQUEST_TIMEOUT,
            )

            if response and response.status_code == requests.codes.ok:
                self._login_page_response = response
            else:
                continue

            passed_checks_by_model = {}
            matched_models = []
            for mdl_cls in models.MODELS:
                mdl = mdl_cls()
                mdl_name = mdl.MODEL_NAME
                passed_checks_by_model[mdl_name] = {}
                autodetect_funcs = mdl.get_autodetect_funcs()
                for func_name, expected_results in autodetect_funcs:
                    func_result = getattr(self, func_name)()
                    check_successful = func_result in expected_results
                    passed_checks_by_model[mdl_name][func_name] = check_successful

                    # check_login_switchinfo_tag beats them all
                    if func_name == "check_login_switchinfo_tag" and check_successful:
                        matched_models.append(mdl)

                values_for_current_mdl = passed_checks_by_model[mdl_name].values()
                if all(values_for_current_mdl) and mdl not in matched_models:
                    matched_models.append(mdl)

            _LOGGER.debug(
                "[NetgearSwitchConnector.autodetect_model] \
passed_checks_by_model=%s matched_models=%s",
                passed_checks_by_model,
                matched_models,
            )

            if len(matched_models) == 1:
                # set local settings
                self._set_instance_attributes_by_model(matched_models[0])
                _LOGGER.info(
                    "[NetgearSwitchConnector.autodetect_model] found %s instance.",
                    matched_models[0],
                )
                if self.switch_model:
                    return self.switch_model
            if len(matched_models) > 1:
                raise MultipleModelsDetectedError(str(matched_models))
        raise SwitchModelNotDetectedError

    def _set_instance_attributes_by_model(
        self, switch_model: models.AutodetectedSwitchModel
    ) -> None:
        self.switch_model = switch_model
        self.ports = switch_model.PORTS
        self.poe_ports = switch_model.POE_PORTS
        self._previous_data = {
            "tx": [0] * self.ports,
            "rx": [0] * self.ports,
            "crc": [0] * self.ports,
            "io": [0] * self.ports,
        }

    def check_login_url(self) -> bool:
        """Request login page and saves response, checks for HTTP Status 200."""
        url = self.switch_model.LOGIN_TEMPLATE["url"].format(ip=self.host)
        _LOGGER.debug(
            "[NetgearSwitchConnector.check_login_url] calling request for url=%s", url
        )
        resp = requests.get(
            url, allow_redirects=False, timeout=self.LOGIN_URL_REQUEST_TIMEOUT
        )
        self._login_page_response = resp
        return resp.status_code == requests.codes.ok

    def check_login_form_rand(self) -> bool:
        """Check if login form contain hidden *rand* input."""
        tree = html.fromstring(self._login_page_response.content)
        input_rand_elems = tree.xpath('//input[@id="rand"]')
        user_password = self._password
        if input_rand_elems:
            input_rand = input_rand_elems[0].value
            merged = netgear_crypt.merge(user_password, input_rand)
            md5_str = netgear_crypt.make_md5(merged)
            self._login_page_form_password = md5_str
            return True
        self._login_page_form_password = user_password
        return False

    def check_login_title_tag(self) -> str:
        """For new firmwares V2.06.10, V2.06.17, V2.06.24."""
        tree = html.fromstring(self._login_page_response.content)
        title_elems = tree.xpath("//title")
        if title_elems:
            return title_elems[0].text.replace("NETGEAR", "").strip()
        return ""

    def check_login_switchinfo_tag(self) -> str:
        """Return info tag or empty when not present."""
        """For old firmware V2.00.05, return """ ""
        """or something like: "GS108Ev3 - 8-Port Gigabit ProSAFE Plus Switch"."""
        """Newer firmwares contains that too."""
        tree = html.fromstring(self._login_page_response.content)
        switchinfo_elems = tree.xpath('//div[@class="switchInfo"]')
        if switchinfo_elems:
            return switchinfo_elems[0].text
        return ""

    def get_unique_id(self) -> str:
        """Return unique identifier from switch model and ip address."""
        if self.switch_model.MODEL_NAME == "":
            _LOGGER.debug(
                "[NetgearSwitchConnector.get_unique_id] switch_model is None, \
try NetgearSwitchConnector.autodetect_model"
            )
            self.autodetect_model()
            _LOGGER.debug(
                "[NetgearSwitchConnector.get_unique_id] now switch_model is %s",
                str(self.switch_model),
            )
        model_lower = self.switch_model.MODEL_NAME.lower()
        return model_lower + "_" + self.host.replace(".", "_")

    def get_login_password(self) -> str:
        """Return the password in plain text or hashed depending on the model."""
        if self._login_page_form_password == "":
            if self._login_page_response is None:
                self.check_login_url()
            self.check_login_form_rand()
        return self._login_page_form_password

    def get_login_cookie(self) -> bool:
        """Login and save returned cookie."""
        if not self.switch_model:
            self.autodetect_model()
        response = None
        login_password = self.get_login_password()
        template = self.switch_model.LOGIN_TEMPLATE
        url = template["url"].format(ip=self.host)
        method = template["method"]
        key = template["key"]
        _LOGGER.debug(
            "[NetgearSwitchConnector.get_login_cookie] calling requests.%s for url=%s",
            method,
            url,
        )
        response = requests.request(
            method,
            url,
            data={key: login_password},
            allow_redirects=True,
            timeout=self.LOGIN_URL_REQUEST_TIMEOUT,
        )
        if not response or response.status_code != requests.codes.ok:
            raise LoginFailedError

        for ct in self.switch_model.ALLOWED_COOKIE_TYPES:
            cookie = response.cookies.get(ct, None)
            if cookie:
                self.cookie_name = ct
                self.cookie_content = cookie
                return True
        tree = html.fromstring(response.content)

        # Handling Error Messages
        error_msg = None
        if isinstance(self.switch_model, (models.GS3xxSeries)):
            error_msg = tree.xpath('//div[@class="pwdErrStyle"]')
            if error_msg:
                error_msg = error_msg[0].text
        else:
            error_msg = tree.xpath('//input[@id="err_msg"]')
            if error_msg:
                error_msg = error_msg[0].value
        if error_msg is not None:
            _LOGGER.warning(
                '[ckw_hass_gs108e.get_login_cookie] [IP: %s] \
Response from switch: "%s"',
                self.host,
                error_msg,
            )
        return False

    def _is_authenticated(self, response: requests.Response) -> bool:
        """Check for redirect to login when not authenticated (anymore)."""
        if "content" in dir(response):
            title = html.fromstring(response.content).xpath("//title")
            if len(title) == 0 or title[0].text.lower() != "redirect to login":
                return True
        return False

    def delete_login_cookie(self) -> bool:
        """Logout and delete cookie."""
        """Only used while testing. Prevents "Maximum number of sessions" error."""
        try:
            self.fetch_page(self.switch_model.LOGOUT_TEMPLATES)
        except requests.exceptions.ConnectionError:
            self.cookie_name = None
            self.cookie_content = None
            return True
        return False

    def _request(
        self,
        method: str,
        url: str,
        data: Any = None,
        *,
        timeout: int = 0,
        allow_redirects: bool = False,
    ) -> requests.Response:
        if (
            not self.cookie_name or not self.cookie_content
        ) and not self.get_login_cookie():
            return requests.Response()
        if timeout == 0:
            timeout = self.LOGIN_URL_REQUEST_TIMEOUT
        jar = requests.cookies.RequestsCookieJar()
        if self.cookie_name and self.cookie_content:
            jar.set(self.cookie_name, self.cookie_content, domain=self.host, path="/")
        request_func = requests.post if method == "post" else requests.get
        _LOGGER.debug(
            "[NetgearSwitchConnector._request] calling requests.%s for url=%s",
            method,
            url,
        )
        response = requests.Response()
        try:
            response = request_func(
                url,
                data=data,
                cookies=jar,
                timeout=timeout,
                allow_redirects=allow_redirects,
            )
        except requests.exceptions.Timeout:
            return response
        # Session expired: refresh login cookie and try again
        if not self._is_authenticated(response):
            if not self.get_login_cookie():
                return response
            with contextlib.suppress(requests.exceptions.Timeout):
                response = request_func(
                    url,
                    data=data,
                    cookies=jar,
                    timeout=timeout,
                    allow_redirects=allow_redirects,
                )
        return response

    def fetch_page(self, templates: list, client_hash: str = "") -> requests.Response:
        """Return response for 1st successful request from templates."""
        data = {}
        response = requests.Response()
        for template in templates:
            url = template["url"].format(ip=self.host)
            method = template["method"]
            if method == "post" and client_hash != "":
                data = {"hash": client_hash}
            response = self._request(method, url, data)
            if response.status_code == requests.codes.ok:
                break
        return response

    def _parse_port_statistics(self, tree) -> tuple:  # noqa: ANN001
        # convert to int
        def convert_to_int(
            lst: list,
            output_elems,  # noqa: ANN001
            base: int = 10,
            attr_name: str = "text",
        ) -> list:
            new_lst = []
            for obj in lst:
                try:
                    value = int(getattr(obj, attr_name), base)
                except (TypeError, ValueError):
                    value = 0
                new_lst.append(value)

            if len(new_lst) < output_elems:
                diff = output_elems - len(new_lst)
                new_lst.extend([0] * diff)
            return new_lst

        def convert_gs3xx_to_int(input_1: str, input_2: str, base: int = 10) -> int:
            int32 = 4294967296
            return int(input_1, base) * int32 + int(input_2, base)

        if isinstance(self.switch_model, models.GS3xxSeries):
            rx = []
            tx = []
            crc = []
            port_i = 0

            for _port in range(self.ports):
                page_inputs = tree.xpath(
                    '//*[@id="settingsStatusContainer"]/div/ul/input'
                )
                input_1_text: str = page_inputs[port_i].value
                input_2_text: str = page_inputs[port_i + 1].value
                rx_value = convert_gs3xx_to_int(input_1_text, input_2_text)
                rx.append(rx_value)

                input_3_text: str = page_inputs[port_i + 2].value
                input_4_text: str = page_inputs[port_i + 3].value
                tx_value = convert_gs3xx_to_int(input_3_text, input_4_text)
                tx.append(tx_value)

                crc.append(0)

                port_i += 6

        else:
            match_bootloader = self._switch_bootloader in API_V2_CHECKS["bootloader"]
            match_firmware = (
                self._loaded_switch_infos.get("switch_firmware", "")
                in API_V2_CHECKS["firmware"]
            )

            if match_bootloader or match_firmware:
                rx_elems = tree.xpath('//input[@name="rxPkt"]')
                tx_elems = tree.xpath('//input[@name="txpkt"]')
                crc_elems = tree.xpath('//input[@name="crcPkt"]')

                # convert to int (base 16)
                rx = convert_to_int(
                    rx_elems, output_elems=self.ports, base=16, attr_name="value"
                )
                tx = convert_to_int(
                    tx_elems, output_elems=self.ports, base=16, attr_name="value"
                )
                crc = convert_to_int(
                    crc_elems, output_elems=self.ports, base=16, attr_name="value"
                )

            else:
                rx_elems = tree.xpath('//tr[@class="portID"]/td[2]')
                tx_elems = tree.xpath('//tr[@class="portID"]/td[3]')
                crc_elems = tree.xpath('//tr[@class="portID"]/td[4]')

                # convert to int (base 10)
                rx = convert_to_int(
                    rx_elems, output_elems=self.ports, base=10, attr_name="text"
                )
                tx = convert_to_int(
                    tx_elems, output_elems=self.ports, base=10, attr_name="text"
                )
                crc = convert_to_int(
                    crc_elems, output_elems=self.ports, base=10, attr_name="text"
                )
        return rx, tx, crc

    def _parse_port_status(self, tree) -> dict:  # noqa: ANN001
        status_by_port = {}

        if isinstance(self.switch_model, (models.GS3xxSeries)):
            for port0 in range(self.ports):
                port_nr = port0 + 1
                xtree_port = tree.xpath(f'//div[@name="isShowPot{port_nr}"]')[0]
                port_state_text = xtree_port[1][0].text

                modus_speed_text = tree.xpath('//input[@class="Speed"]')[port0].value
                if modus_speed_text == "1":
                    modus_speed_text = "Auto"
                connection_speed_text = tree.xpath('//input[@class="LinkedSpeed"]')[
                    port0
                ].value
                connection_speed_text = (
                    connection_speed_text.replace("full", "")
                    .replace("half", "")
                    .strip()
                )

                status_by_port[port_nr] = {
                    "status": port_state_text,
                    "modus_speed": modus_speed_text,
                    "connection_speed": connection_speed_text,
                }

        else:
            match_bootloader = self._switch_bootloader in API_V2_CHECKS["bootloader"]
            match_firmware = (
                self._loaded_switch_infos.get("switch_firmware", "")
                in API_V2_CHECKS["firmware"]
            )

            if match_bootloader or match_firmware:
                _port_elems = tree.xpath('//tr[@class="portID"]/td[2]')
                portstatus_elems = tree.xpath('//tr[@class="portID"]/td[3]')
                portspeed_elems = tree.xpath('//tr[@class="portID"]/td[4]')
                portconnectionspeed_elems = tree.xpath('//tr[@class="portID"]/td[5]')

                for port_nr in range(self.ports):
                    try:
                        status_text = portstatus_elems[port_nr].text.replace("\n", "")
                        modus_speed_text = portspeed_elems[port_nr].text.replace(
                            "\n", ""
                        )
                        connection_speed_text = portconnectionspeed_elems[
                            port_nr
                        ].text.replace("\n", "")
                    except (IndexError, AttributeError):
                        status_text = self.port_status.get(port_nr + 1, {}).get(
                            "status", None
                        )
                        modus_speed_text = self.port_status.get(port_nr + 1, {}).get(
                            "modus_speed", None
                        )
                        connection_speed_text = self.port_status.get(
                            port_nr + 1, {}
                        ).get("connection_speed", None)
                    status_by_port[port_nr + 1] = {
                        "status": status_text,
                        "modus_speed": modus_speed_text,
                        "connection_speed": connection_speed_text,
                    }

        self.port_status = status_by_port
        _LOGGER.debug("Port Status is %s", self.port_status)
        return status_by_port

    def _parse_poe_port_config(self, tree) -> dict:  # noqa: ANN001
        config_by_port = {}
        poe_port_power_x = tree.xpath('//input[@id="hidPortPwr"]')
        for i, x in enumerate(poe_port_power_x):
            config_by_port[i + 1] = "on" if x.value == "1" else "off"
        return config_by_port

    def _parse_poe_port_status(self, tree) -> dict:  # noqa: ANN001
        poe_output_power = {}
        # Port name:
        #   //li[contains(@class,"poe_port_list_item")]
        #       //span[contains(@class,"poe_index_li_title")]
        # Power mode:
        #   //li[contains(@class,"poe_port_list_item")]
        #       //span[contains(@class,"poe-power-mode")]
        # Port status:
        #   //li[contains(@class,"poe_port_list_item")]
        #       //div[contains(@class,"poe_port_status")]
        poe_output_power_x = tree.xpath(
            '//li[contains(@class,"poe_port_list_item")]//div[contains(@class,"poe_port_status")]'
        )
        for i, x in enumerate(poe_output_power_x):
            try:
                poe_output_power[i + 1] = float(x.xpath(".//span")[5].text)
            except ValueError:
                poe_output_power[i + 1] = 0.0
        return poe_output_power

    def _get_gs3xx_switch_info(self, tree, text: str) -> str:  # noqa: ANN001
        span_node = tree.xpath(f'//span[text()="{text}"]')
        if span_node:
            for child_span in (
                span_node[0].getparent().getnext().iterchildren(tag="span")
            ):
                return child_span.text
        return ""

    def get_switch_infos(self) -> dict:
        """Return dict with all available statistics."""
        switch_data = {}

        if not self._loaded_switch_infos:
            if not self.switch_model:
                self.autodetect_model()
            page = self.fetch_page(self.switch_model.SWITCH_INFO_TEMPLATES)
            if not page:
                return switch_data
            tree = html.fromstring(page.content)

            if isinstance(self.switch_model, (models.GS3xxSeries)):
                switch_serial_number = self._get_gs3xx_switch_info(
                    tree=tree, text="ml198"
                )
                switch_name = tree.xpath('//div[@id="switch_name"]')[0].text
                switch_firmware = self._get_gs3xx_switch_info(tree=tree, text="ml089")

            else:
                # switch_info.htm:
                switch_serial_number = "unknown"

                switch_name = tree.xpath('//input[@id="switch_name"]')[0].value

                # Detect Firmware
                switch_firmware = tree.xpath('//table[@id="tbl1"]/tr[6]/td[2]')[0].text
                if switch_firmware is None:
                    # Fallback older versions
                    switch_firmware = tree.xpath('//table[@id="tbl1"]/tr[4]/td[2]')[
                        0
                    ].text

                switch_bootloader_x = tree.xpath('//td[@id="loader"]')
                switch_serial_number_x = tree.xpath('//table[@id="tbl1"]/tr[3]/td[2]')
                client_hash_x = tree.xpath('//input[@id="hash"]')

                if switch_bootloader_x:
                    self._switch_bootloader = switch_bootloader_x[0].text
                if switch_serial_number_x:
                    switch_serial_number = switch_serial_number_x[0].text

            client_hash_x = tree.xpath('//input[@id="hash"]')
            if client_hash_x:
                self._client_hash = client_hash_x[0].value

            # Avoid a second call on next get_switch_infos() call
            self._loaded_switch_infos = {
                "switch_ip": self.host,
                "switch_name": switch_name,
                "switch_bootloader": self._switch_bootloader,
                "switch_firmware": switch_firmware,
                "switch_serial_number": switch_serial_number,
            }

        switch_data.update(**self._loaded_switch_infos)

        # Hold fire
        time.sleep(self.sleep_time)

        response_portstatistics = self.fetch_page(
            self.switch_model.PORT_STATISTICS_TEMPLATES, client_hash=self._client_hash
        )
        if not response_portstatistics:
            return switch_data

        # init values
        sum_port_traffic_rx = 0
        sum_port_traffic_tx = 0
        sum_port_traffic_crc_err = 0
        sum_port_speed_bps_rx = 0
        sum_port_speed_bps_tx = 0

        _start_time = time.perf_counter()

        # Parse content
        tree_portstatistics = html.fromstring(response_portstatistics.content)
        rx1, tx1, crc1 = self._parse_port_statistics(tree=tree_portstatistics)
        io_zeros = [0] * self.ports
        current_data = {"rx": rx1, "tx": tx1, "crc": crc1, "io": io_zeros}

        # Fetch Port Status
        time.sleep(self.sleep_time)
        if isinstance(self.switch_model, (models.GS3xxSeries)):
            response_dashboard = self.fetch_page(
                self.switch_model.SWITCH_INFO_TEMPLATES
            )
            tree_response_dashboard = html.fromstring(response_dashboard.content)
            port_status = self._parse_port_status(tree=tree_response_dashboard)
        else:
            response_portstatus = self.fetch_page(
                self.switch_model.PORT_STATUS_TEMPLATES, client_hash=self._client_hash
            )
            tree_portstatus = html.fromstring(response_portstatus.content)
            port_status = self._parse_port_status(tree=tree_portstatus)

        # Fetch POE Port Status
        if isinstance(self.switch_model, (models.GS3xxSeries)):
            time.sleep(self.sleep_time)
            response_poeportconfig = self.fetch_page(
                self.switch_model.POE_PORT_CONFIG_TEMPLATES
            )
            tree_poeportconfig = html.fromstring(response_poeportconfig.content)
            poe_port_config = self._parse_poe_port_config(tree=tree_poeportconfig)

            for poe_port_nr, poe_power_config in poe_port_config.items():
                switch_data[f"port_{poe_port_nr}_poe_power_active"] = poe_power_config
            time.sleep(self.sleep_time)
            response_poeportstatus = self.fetch_page(
                self.switch_model.POE_PORT_STATUS_TEMPLATES
            )
            tree_poeportstatus = html.fromstring(response_poeportstatus.content)
            poe_port_status = self._parse_poe_port_status(tree=tree_poeportstatus)

            for poe_port_nr, poe_power_status in poe_port_status.items():
                switch_data[f"port_{poe_port_nr}_poe_output_power"] = poe_power_status

        sample_time = _start_time - self._previous_timestamp
        sample_factor = 1 / sample_time
        switch_data["response_time_s"] = round(sample_time, 1)

        for port_number0 in range(self.ports):
            try:
                port_number = port_number0 + 1
                port_traffic_rx = (
                    current_data["rx"][port_number0]
                    - self._previous_data["rx"][port_number0]
                )
                port_traffic_tx = (
                    current_data["tx"][port_number0]
                    - self._previous_data["tx"][port_number0]
                )
                port_traffic_crc_err = (
                    current_data["crc"][port_number0]
                    - self._previous_data["crc"][port_number0]
                )
                port_speed_bps_rx = int(port_traffic_rx * sample_factor)
                port_speed_bps_tx = int(port_traffic_tx * sample_factor)
                port_speed_bps_io = port_speed_bps_rx + port_speed_bps_tx
                port_sum_rx = current_data["rx"][port_number0]
                port_sum_tx = current_data["tx"][port_number0]
            except IndexError:
                _LOGGER.debug("IndexError at port_number0=%s", port_number0)
                continue

            # Port Status
            if len(port_status) == self.ports:
                switch_data[f"port_{port_number}_status"] = (
                    "on"
                    if self.port_status[port_number].get("status")
                    in PORT_STATUS_CONNECTED
                    else "off"
                )
                switch_data[f"port_{port_number}_modus_speed"] = (
                    self.port_status[port_number].get("modus_speed") in PORT_MODUS_SPEED
                )
                port_connection_speed = self.port_status[port_number].get(
                    "connection_speed"
                )
                if port_connection_speed == "1000M":
                    port_connection_speed = 1000
                elif port_connection_speed == "100M":
                    port_connection_speed = 100
                elif port_connection_speed == "10M":
                    port_connection_speed = 10
                elif port_connection_speed in ["Nicht verbunden"]:
                    port_connection_speed = 0
                else:
                    port_connection_speed = 0
                switch_data[f"port_{port_number}_connection_speed"] = (
                    port_connection_speed
                )

            # Lowpass-Filter
            port_traffic_rx = max(port_traffic_rx, 0)
            port_traffic_tx = max(port_traffic_tx, 0)
            port_traffic_crc_err = max(port_traffic_crc_err, 0)
            port_speed_bps_rx = max(port_speed_bps_rx, 0)
            port_speed_bps_tx = max(port_speed_bps_tx, 0)
            port_speed_bps_io = max(port_speed_bps_io, 0)

            # Access old data if value is 0
            port_status_is_connected = (
                switch_data.get(f"port_{port_number}_status", "off") == "on"
            )
            if port_status_is_connected:
                if port_sum_rx <= 0:
                    port_sum_rx = self._previous_data["rx"][port_number0]
                    current_data["rx"][port_number0] = port_sum_rx
                    if port_status_is_connected:
                        _LOGGER.info(
                            "Fallback to previous data: port_nr=%s port_sum_rx=%s",
                            port_number,
                            port_sum_rx,
                        )
                if port_sum_tx <= 0:
                    port_sum_tx = self._previous_data["tx"][port_number0]
                    current_data["tx"][port_number0] = port_sum_tx
                    if port_status_is_connected:
                        _LOGGER.info(
                            _LOGGER.info(
                                "Fallback to previous data: port_nr=%s port_sum_tx=%s",
                                port_number,
                                port_sum_tx,
                            )
                        )
                if port_speed_bps_io <= 0:
                    port_speed_bps_io = self._previous_data["io"][port_number0]
                    current_data["io"][port_number0] = port_speed_bps_io
                    if port_status_is_connected:
                        _LOGGER.info(
                            "Fallback to previous data: \
port_nr=%s port_speed_bps_io=%s",
                            port_number,
                            port_speed_bps_io,
                        )

            # Highpass-Filter (max 1e9 B/s = 1GB/s per port)
            hp_max_traffic = 1e9 * sample_time
            port_traffic_rx = min(port_traffic_rx, hp_max_traffic)
            port_traffic_tx = min(port_traffic_tx, hp_max_traffic)
            port_traffic_crc_err = min(port_traffic_crc_err, hp_max_traffic)

            # Highpass-Filter (max 1e9 B/s = 1GB/s per port)
            # speed is already normalized to 1s
            hp_max_speed = 1e9
            port_speed_bps_rx = min(port_speed_bps_rx, hp_max_speed)
            port_speed_bps_tx = min(port_speed_bps_tx, hp_max_speed)

            sum_port_traffic_rx += port_traffic_rx
            sum_port_traffic_tx += port_traffic_tx
            sum_port_traffic_crc_err += port_traffic_crc_err
            sum_port_speed_bps_rx += port_speed_bps_rx
            sum_port_speed_bps_tx += port_speed_bps_tx

            # set for later (previous data)
            current_data["io"][port_number0] = port_speed_bps_io

            switch_data[f"port_{port_number}_traffic_rx_mbytes"] = _reduce_digits(
                port_traffic_rx
            )
            switch_data[f"port_{port_number}_traffic_tx_mbytes"] = _reduce_digits(
                port_traffic_tx
            )
            switch_data[f"port_{port_number}_speed_rx_mbytes"] = _reduce_digits(
                port_speed_bps_rx
            )
            switch_data[f"port_{port_number}_speed_tx_mbytes"] = _reduce_digits(
                port_speed_bps_tx
            )
            switch_data[f"port_{port_number}_speed_io_mbytes"] = _reduce_digits(
                port_speed_bps_io
            )
            switch_data[f"port_{port_number}_crc_errors"] = port_traffic_crc_err
            switch_data[f"port_{port_number}_sum_rx_mbytes"] = _reduce_digits(
                port_sum_rx
            )
            switch_data[f"port_{port_number}_sum_tx_mbytes"] = _reduce_digits(
                port_sum_tx
            )

        switch_data["sum_port_traffic_rx"] = _reduce_digits(sum_port_traffic_rx)
        switch_data["sum_port_traffic_tx"] = _reduce_digits(sum_port_traffic_tx)
        switch_data["sum_port_traffic_crc_err"] = sum_port_traffic_crc_err
        switch_data["sum_port_speed_bps_rx"] = sum_port_speed_bps_rx
        switch_data["sum_port_speed_bps_tx"] = sum_port_speed_bps_tx
        switch_data["sum_port_speed_bps_io"] = _reduce_digits(
            v=sum_port_speed_bps_rx + sum_port_speed_bps_tx
        )

        # set previous data
        self._previous_timestamp = time.perf_counter()
        self._previous_data = {
            "rx": current_data["rx"],
            "tx": current_data["tx"],
            "crc": current_data["crc"],
            "io": current_data["io"],
        }

        return switch_data

    def switch_poe_port(self, poe_port: int, state: str) -> bool:
        """Switch poe port on or off."""
        if state not in SWITCH_STATES:
            return False
        if poe_port in self.poe_ports:
            for template in self.switch_model.POE_PORT_CONFIG_TEMPLATES:
                url = template["url"].format(ip=self.host)
                data = {
                    "hash": self._client_hash,
                    "ACTION": "Apply",
                    "portID": poe_port - 1,
                    "ADMIN_MODE": 1 if state == "on" else 0,
                }
                resp = self._request("post", url, data=data)
                if resp.status_code == requests.codes.ok:
                    self._loaded_switch_infos[f"port_{poe_port}_poe_power_active"] = (
                        state
                    )
                    return True
        return False

    def turn_on_poe_port(self, poe_port: int) -> bool:
        """Turn on power of a PoE port."""
        return self.switch_poe_port(poe_port, "on")

    def turn_off_poe_port(self, poe_port: int) -> bool:
        """Turn off power of a PoE port."""
        return self.switch_poe_port(poe_port, "off")

    def power_cycle_poe_port(self, poe_port: int) -> bool:
        """Cycle the power of a PoE port."""
        if poe_port in self.poe_ports:
            for template in self.switch_model.POE_PORT_CONFIG_TEMPLATES:
                url = template["url"].format(ip=self.host)
                data = {
                    "hash": self._client_hash,
                    "ACTION": "Reset",
                    "port" + str(poe_port - 1): "checked",
                }
                resp = self._request("post", url, data=data)
                if (
                    resp.status_code == requests.codes.ok
                    and str(resp.content.strip()) == "b'SUCCESS'"
                ):
                    return True
                _LOGGER.warning(
                    "NetgearSwitchConnector.power_cycle_poe_port response was %s",
                    resp.content.strip(),
                )
        return False
