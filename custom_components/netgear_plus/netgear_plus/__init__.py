"""Netgear API."""

import logging
import time

from lxml import html
import requests

from . import models, netgear_crypt

LOGIN_HTM_URL_TMPL = "http://{ip}/login.htm"
LOGIN_CGI_URL_TMPL = "http://{ip}/login.cgi"
SWITCH_INFO_HTM_URL_TMPL = "http://{ip}/switch_info.htm"
SWITCH_INFO_CGI_URL_TMPL = "http://{ip}/switch_info.cgi"
PORT_STATISTICS_URL_TMPL = "http://{ip}/portStatistics.cgi"
PORT_STATUS_URL_TMPL = "http://{ip}/status.htm"
POE_PORT_CONFIG_CGI_URL = "http://{ip}/PoEPortConfig.cgi"
ALLOWED_COOKIE_TYPES = ["GS108SID", "SID"]

API_V2_CHECKS = {
    "bootloader": ["V1.00.03", "V2.06.01", "V2.06.02", "V2.06.03"],
    "firmware": ["V2.06.24GR", "V2.06.24EN"],
}


def _reduce_digits(v):
    bytes_to_mbytes = 1e-6
    return float("{:.2f}".format(round(v * bytes_to_mbytes, 2)))


PORT_STATUS_CONNECTED = ["Aktiv", "Up", "UP"]
PORT_MODUS_SPEED = ["Auto"]
PORT_POE_POWER_IS_ON_VALUES = []


MODELS = [
    models.GS105E,
    models.GS105Ev2,
    models.GS108E,
    models.GS108Ev3,
    models.GS305EP,
    models.GS308EP,
    models.GS316EP,
    models.GS316EPP,
]

_LOGGER = logging.getLogger(__name__)


class MultipleModelsDetected(Exception):
    pass


class MissingSwitchModel(Exception):
    pass


class NetgearSwitchConnector:
    """Representation of a Netgear Switch."""

    LOGIN_URL = "http://{ip}/login.cgi"
    LOGIN_URL_REQUEST_TIMEOUT = 15

    def __init__(self, host, password):
        self.host = host

        # initial values
        self.switch_model = None
        self.ports = 0
        self.poe_ports = None
        self.port_status = {}
        self._switch_bootloader = "unknown"

        # sleep time between requests
        self.sleep_time = 0.25

        # plain login password
        self._password = password
        # response of login page request
        self._login_page_response = None
        # cryped password if md5
        self._login_page_form_password = None
        # cookie/hash data
        self.cookie_name = None
        self.cookie_content = None
        self._client_hash = None

        # previous data calculation
        self._previous_timestamp = time.perf_counter()
        self._previous_data = {}

        # current data
        self._loaded_switch_infos = {}

    def autodetect_model(self):
        _LOGGER.info(
            "[NetgearSwitchConnector.autodetect_model] called for IP=%s", self.host
        )
        passed_checks_by_model = {}
        if self._login_page_response is None:
            self.check_login_url()
        # Fallback to self._login_page.LOGIN_URL = "http://{ip}/login.htm" if cgi does not exists
        matched_models = []
        for mdl_cls in MODELS:
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
            if all(values_for_current_mdl):
                if mdl not in matched_models:
                    matched_models.append(mdl)

        _LOGGER.info(
            f"[NetgearSwitchConnector.autodetect_model] passed_checks_by_model={passed_checks_by_model} matched_models={matched_models}"  # noqa: G004
        )

        # print(
        #    "[NetgearSwitchConnector.autodetect_model] passed_checks_by_model=",
        #    passed_checks_by_model,
        #    "matched_models=",
        #    matched_models,
        # )

        if len(matched_models) == 1:
            # set local settings
            self._set_instance_attribes_by_model(switch_model=matched_models[0])
            return self.switch_model
        if len(matched_models) > 1:
            raise MultipleModelsDetected(str(matched_models))
        return False

    def _set_instance_attribes_by_model(
        self, switch_model: models.AutodetectedSwitchModel
    ):
        if switch_model:
            self.switch_model = switch_model
            self.ports = switch_model.PORTS
            self.poe_ports = switch_model.POE_PORTS
            self._previous_data = {
                "tx": [0] * self.ports,
                "rx": [0] * self.ports,
                "crc": [0] * self.ports,
                "io": [0] * self.ports,
            }

    def check_login_url(self):
        """Request login page and saves response, checks for HTTP Status 200."""
        url = self.LOGIN_URL.format(ip=self.host)
        _LOGGER.info(
            "[NetgearSwitchConnector.check_login_url] calling request for url=%s", url
        )
        resp = requests.get(
            url, allow_redirects=False, timeout=self.LOGIN_URL_REQUEST_TIMEOUT
        )
        self._login_page_response = resp
        return resp.status_code == 200

    def check_login_form_rand(self):
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

    def check_login_title_tag(self):
        """For new firmwares V2.06.10, V2.06.17, V2.06.24."""
        tree = html.fromstring(self._login_page_response.content)
        title_elems = tree.xpath("//title")
        if title_elems:
            return title_elems[0].text.replace("NETGEAR", "").strip()
        return False

    def check_login_switchinfo_tag(self):
        """For old firmware V2.00.05, return False or something like "GS108Ev3 - 8-Port Gigabit ProSAFE Plus Switch". Newer firmwares contains that too."""
        tree = html.fromstring(self._login_page_response.content)
        switchinfo_elems = tree.xpath('//div[@class="switchInfo"]')
        if switchinfo_elems:
            return switchinfo_elems[0].text
        return False

    def get_unique_id(self):
        if self.switch_model is None:
            _LOGGER.info(
                "[NetgearSwitchConnector.get_unique_id] switch_model is None, try NetgearSwitchConnector.autodetect_model"
            )
            self.autodetect_model()
            _LOGGER.info(
                "[NetgearSwitchConnector.get_unique_id] now switch_model is %s",
                str(self.switch_model),
            )
        if self.switch_model:
            model_lower = self.switch_model.MODEL_NAME.lower()
            return model_lower + "_" + self.host.replace(".", "_")
        raise MissingSwitchModel

    def get_login_password(self):
        if self._login_page_form_password is None:
            if self._login_page_response is None:
                self.check_login_url()
            self.check_login_form_rand()
        return self._login_page_form_password

    def get_login_cookie(self):
        login_password = self.get_login_password()
        url = LOGIN_CGI_URL_TMPL.format(ip=self.host)
        _LOGGER.info(
            "[NetgearSwitchConnector.get_login_cookie] calling request.post for url=%s with login_password=%s",
            url,
            login_password,
        )
        response = requests.post(
            url,
            data={"password": login_password},
            allow_redirects=True,
            timeout=self.LOGIN_URL_REQUEST_TIMEOUT,
        )
        for ct in ALLOWED_COOKIE_TYPES:
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
                f'[ckw_hass_gs108e.get_login_cookie] [IP: {self.host}] Response from switch: "{error_msg}"'
            )
        return False

    def _request(self, method, url, data=None, timeout=None, allow_redirects=False):
        if not self.cookie_name or not self.cookie_content:
            return None
        if timeout is None:
            timeout = self.LOGIN_URL_REQUEST_TIMEOUT
        jar = requests.cookies.RequestsCookieJar()
        jar.set(self.cookie_name, self.cookie_content, domain=self.host, path="/")
        request_func = requests.post if method == "post" else requests.get
        _LOGGER.info(
            "[NetgearSwitchConnector._request] calling request for url=%s", url
        )
        try:
            return request_func(
                url,
                data=data,
                cookies=jar,
                timeout=timeout,
                allow_redirects=allow_redirects,
            )
        except requests.exceptions.Timeout:
            return None

    def fetch_switch_infos(self, url_tmpl=SWITCH_INFO_HTM_URL_TMPL):
        if isinstance(self.switch_model, (models.GS3xxSeries)):
            url_tmpl = self.switch_model.DASHBOARD_CGI_URL_TMPL
        url = url_tmpl.format(ip=self.host)
        method = "get"
        resp = self._request(url=url, method=method)
        if isinstance(resp, requests.Response) and resp.status_code == 404:
            return self.fetch_switch_infos(url_tmpl=SWITCH_INFO_CGI_URL_TMPL)
        return resp

    def fetch_port_statistics(self, client_hash=None):
        url = PORT_STATISTICS_URL_TMPL.format(ip=self.host)
        data = None
        if isinstance(self.switch_model, models.GS3xxSeries):
            method = "get"
        else:
            method = "post"
            if client_hash is not None:
                data = {"hash": client_hash}
        return self._request(url=url, method=method, data=data, allow_redirects=False)

    def fetch_port_status(self, client_hash=None):
        url = PORT_STATUS_URL_TMPL.format(ip=self.host)
        method = "get"
        return self._request(url=url, method=method)

    def fetch_poeportconfig(self):
        if isinstance(self.switch_model, models.GS3xxSeries):
            url = POE_PORT_CONFIG_CGI_URL.format(ip=self.host)
            method = "get"
            data = None
            return self._request(
                url=url, method=method, data=data, allow_redirects=False
            )

    def _parse_port_statistics(self, tree):
        # convert to int
        def convert_to_int(lst, output_elems, base=10, attr_name="text"):
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

        def convert_gs3xx_to_int(input_1, input_2, base=10):
            int32 = 4294967296
            return int(input_1, base) * int32 + int(input_2, base)

        if isinstance(self.switch_model, models.GS3xxSeries):
            rx = []
            tx = []
            crc = []
            port_i = 0

            for port0 in range(self.ports):
                page_inputs = tree.xpath(
                    '//*[@id="settingsStatusContainer"]/div/ul/input'
                )
                # print("port_i", port_i, "page_inputs", page_inputs)
                input_1_text = page_inputs[port_i].value
                input_2_text = page_inputs[port_i + 1].value
                rx_value = convert_gs3xx_to_int(input_1_text, input_2_text)
                rx.append(rx_value)

                input_3_text = page_inputs[port_i + 2].value
                input_4_text = page_inputs[port_i + 3].value
                tx_value = convert_gs3xx_to_int(input_3_text, input_4_text)
                tx.append(tx_value)

                crc.append(0)

                # print(port_i, rx_value)

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

    def _parse_port_status(self, tree):
        status_by_port = {}

        if isinstance(self.switch_model, (models.GS3xxSeries)):
            for port0 in range(self.ports):
                port_nr = port0 + 1
                xtree_port = tree.xpath(f'//div[@name="isShowPot{port_nr}"]')[0]
                port_state_text = xtree_port[1][0].text

                modus_speed_text = tree.xpath(f'//input[@class="Speed"]')[port0].value
                if modus_speed_text == "1":
                    modus_speed_text = "Auto"
                connection_speed_text = tree.xpath(f'//input[@class="LinkedSpeed"]')[
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
                # port_elems = tree.xpath('//tr[@class="portID"]/td[2]')
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
        # print("Port Status", self.port_status)
        return status_by_port

    def _parse_poe_port_status(self, tree):
        status_by_port = {}
        poe_port_power_x = tree.xpath('//input[@id="hidPortPwr"]')
        for i, x in enumerate(poe_port_power_x):
            status_by_port[i + 1] = "on" if x.value == "1" else "off"
        return status_by_port

    def _get_gs3xx_switch_info(self, tree, text):
        span_node = tree.xpath(f'//span[text()="{text}"]')
        if span_node:
            for child_span in (
                span_node[0].getparent().getnext().iterchildren(tag="span")
            ):
                return child_span.text
        return None

    def get_switch_infos(self):
        switch_data = {}

        if not self._loaded_switch_infos:
            page = self.fetch_switch_infos()
            if not page:
                return None
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

                # print("switch_name", switch_name)
                # print("switch_bootloader", switch_bootloader)
                # print("client_hash", client_hash)
                # print("switch_firmware", switch_firmware)
                # print("switch_serial_number", switch_serial_number)

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

        response_portstatistics = self.fetch_port_statistics(
            client_hash=self._client_hash
        )
        if not response_portstatistics:
            return None

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
            response_dashboard = self.fetch_switch_infos()
            tree_response_dashboard = html.fromstring(response_dashboard.content)
            port_status = self._parse_port_status(tree=tree_response_dashboard)
        else:
            response_portstatus = self.fetch_port_status(client_hash=self._client_hash)
            tree_portstatus = html.fromstring(response_portstatus.content)
            port_status = self._parse_port_status(tree=tree_portstatus)

        # Fetch POE Port Status
        if isinstance(self.switch_model, (models.GS3xxSeries)):
            time.sleep(self.sleep_time)
            response_poeportconfig = self.fetch_poeportconfig()
            tree_poeportconfig = html.fromstring(response_poeportconfig.content)
            poe_port_status = self._parse_poe_port_status(tree=tree_poeportconfig)

            for poe_port_nr, poe_power_status in poe_port_status.items():
                switch_data[f"port_{poe_port_nr}_poe_power_active"] = poe_power_status

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
                # print("IndexError at port_number0", port_number0)
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
            if port_speed_bps_io < 0:
                port_speed_bps_io = 0

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
                            f"Fallback to previous data: port_nr={port_number} port_sum_rx={port_sum_rx}"
                        )
                if port_sum_tx <= 0:
                    port_sum_tx = self._previous_data["tx"][port_number0]
                    current_data["tx"][port_number0] = port_sum_tx
                    if port_status_is_connected:
                        _LOGGER.info(
                            f"Fallback to previous data: port_nr={port_number} port_sum_rx={port_sum_tx}"
                        )
                if port_speed_bps_io <= 0:
                    port_speed_bps_io = self._previous_data["io"][port_number0]
                    current_data["io"][port_number0] = port_speed_bps_io
                    if port_status_is_connected:
                        _LOGGER.info(
                            f"Fallback to previous data: port_nr={port_number} port_speed_bps_io={port_speed_bps_io}"
                        )

            # Highpass-Filter (max 1e9 B/s = 1GB/s per port)
            hp_max_traffic = 1e9 * sample_time
            if port_traffic_rx > hp_max_traffic:
                port_traffic_rx = hp_max_traffic
            if port_traffic_tx > hp_max_traffic:
                port_traffic_tx = hp_max_traffic
            if port_traffic_crc_err > hp_max_traffic:
                port_traffic_crc_err = hp_max_traffic

            # Highpass-Filter (max 1e9 B/s = 1GB/s per port)
            # speed is already normalized to 1s
            hp_max_speed = 1e9
            if port_speed_bps_rx > hp_max_speed:
                port_speed_bps_rx = hp_max_speed
            if port_speed_bps_tx > hp_max_speed:
                port_speed_bps_tx = hp_max_speed

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

    def turn_on_poe_port(self, poe_port, turn_on=True):
        if poe_port in self.poe_ports:
            url = POE_PORT_CONFIG_CGI_URL.format(ip=self.host)
            data = {
                "hash": self._client_hash,
                "ACTION": "Apply",
                "portID": poe_port - 1,
                "ADMIN_MODE": 1 if turn_on else 0,
            }
            # print("turn_on_poe_port data=", data)
            resp = self._request("post", url, data=data)
            successful = resp.status_code == 200
            if successful:
                self._loaded_switch_infos[f"port_{poe_port}_poe_power_active"] = (
                    "on" if turn_on else "off"
                )
            return resp.status_code == 200
        return False

    def turn_off_poe_port(self, poe_port):
        return self.turn_on_poe_port(poe_port=poe_port, turn_on=False)


def scan_lan_for_netgear_switches(start_ip="192.168.178.1"):
    found_switches = {}
