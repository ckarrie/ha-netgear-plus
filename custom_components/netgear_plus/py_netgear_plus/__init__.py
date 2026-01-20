"""Netgear API."""

import logging
import time
from contextlib import suppress
from pathlib import Path
from typing import Any

from .fetcher import (
    BaseResponse,
    LoginFailedError,
    MaxSessionsError,
    NotLoggedInError,
    PageFetcher,
    PageFetcherConnectionError,
    PageNotLoadedError,
    Response,
    status_code_no_response,
    status_code_not_found,
    status_code_unauthorized,
)
from .models import (
    MODELS,
    AutodetectedSwitchModel,
    MultipleModelsDetectedError,
    SwitchModelNotDetectedError,
)
from .parsers import NetgearPlusPageParserError, create_page_parser

__version__ = "0.4.7"

DEFAULT_PAGE = "index.htm"
MAX_AUTHENTICATION_FAILURES = 3
PORT_STATUS_CONNECTED = ["Aktiv", "Up", "UP", "CONNECTED"]
PORT_MODUS_SPEED = ["Auto"]
SWITCH_STATES = ["on", "off"]

_LOGGER = logging.getLogger(__name__)


def _from_bytes_to_megabytes(v: float) -> float:
    bytes_to_mbytes = 1e-6
    return float(f"{round(v * bytes_to_mbytes, 2):.2f}")


class InvalidPortStatusError(Exception):
    """Number of statusses do not match number of ports."""


class InvalidSwitchStateError(Exception):
    """State should be one of the options in SWITCH_STATES."""


class InvalidPoEPortError(Exception):
    """Port is not a PoE port."""


class NetgearSwitchConnector:
    """Representation of a Netgear Switch."""

    def __init__(self, host: str, password: str) -> None:
        """Initialize Connector Object."""
        self.host = host

        # initial values
        self.switch_model = AutodetectedSwitchModel
        self._page_fetcher = PageFetcher(host)
        self._page_parser = create_page_parser()
        self.ports = 0
        self.poe_ports = []
        self._switch_bootloader = "unknown"

        # sleep time between requests
        self.sleep_time = 0.25

        # Login related instance variables
        # plain login password
        self._password = password
        # Model page template param variables
        self._client_hash = None
        self._gambit = None

        self._authentication_failure_count = 0

        # previous data calculation
        self._previous_timestamp = time.perf_counter()
        self._previous_data = {}

        # current data
        self._loaded_switch_metadata = {}

        _LOGGER.debug(
            "[NetgearSwitchConnector] instance (v%s) created for IP=%s",
            __version__,
            self.host,
        )
        _LOGGER.debug(
            "[NetgearSwitchConnector] DEBUG logging enabled. "
            "Your logs may contain sensitve information like "
            "passwords or session cookies. Do not use in production."
        )

    def turn_on_offline_mode(self, path_prefix: str) -> None:
        """Turn on offline mode."""
        self._page_fetcher.turn_on_offline_mode(path_prefix)

    def turn_on_online_mode(self) -> None:
        """Turn on online mode."""
        self._page_fetcher.turn_on_online_mode()

    def get_offline_mode(self) -> bool:
        """Get offline mode status."""
        return self._page_fetcher.offline_mode

    def autodetect_model(self) -> type[AutodetectedSwitchModel]:
        """Detect switch model from login page contents."""
        _LOGGER.debug(
            "[NetgearSwitchConnector.autodetect_model] called for IP=%s", self.host
        )
        for template in AutodetectedSwitchModel.AUTODETECT_TEMPLATES:
            response = None
            url = template["url"].format(ip=self.host)
            method = template["method"]
            with suppress(PageFetcherConnectionError):
                response = self._page_fetcher.request(
                    method,
                    url,
                )

            if response and self._page_fetcher.has_ok_status(response):
                passed_checks_by_model = {}
                matched_models = []
                for mdl_cls in MODELS:
                    mdl = mdl_cls()
                    mdl_name = mdl.MODEL_NAME
                    passed_checks_by_model[mdl_name] = {}
                    autodetect_funcs = mdl.get_autodetect_funcs()
                    for func_name, expected_results in autodetect_funcs:
                        func_result = getattr(self._page_parser, func_name)(response)
                        check_successful = func_result in expected_results
                        passed_checks_by_model[mdl_name][func_name] = check_successful

                        # check_login_switchinfo_tag beats them all
                        if (
                            func_name == "check_login_switchinfo_tag"
                            and check_successful
                        ):
                            matched_models.append(mdl)

                    values_for_current_mdl = passed_checks_by_model[mdl_name].values()
                    if all(values_for_current_mdl) and mdl not in matched_models:
                        matched_models.append(mdl)

                if len(matched_models) == 1:
                    # set local settings
                    self._set_instance_attributes_by_model(matched_models[0])
                    _LOGGER.info(
                        "[NetgearSwitchConnector.autodetect_model] found %s switch.",
                        matched_models[0].MODEL_NAME,
                    )
                    if self.switch_model:
                        self._page_parser = create_page_parser(
                            self.switch_model.MODEL_NAME
                        )
                        return self.switch_model
                if len(matched_models) > 1:
                    raise MultipleModelsDetectedError(str(matched_models))
                _LOGGER.debug(
                    "[NetgearSwitchConnector.autodetect_model] "
                    "passed_checks_by_model=%s matched_models=%s",
                    passed_checks_by_model,
                    matched_models,
                )
        raise SwitchModelNotDetectedError

    def _set_instance_attributes_by_model(
        self, switch_model: type[AutodetectedSwitchModel]
    ) -> None:
        self.switch_model = switch_model
        self.ports = switch_model.PORTS
        self.poe_ports = switch_model.POE_PORTS
        self._previous_data = {
            "traffic_tx": [0] * self.ports,
            "traffic_rx": [0] * self.ports,
            "crc_errors": [0] * self.ports,
            "speed_io": [0] * self.ports,
            "sum_rx": [0] * self.ports,
            "sum_tx": [0] * self.ports,
        }

    def get_unique_id(self) -> str:
        """Return unique identifier from switch model and ip address."""
        if self.switch_model.MODEL_NAME == "":
            _LOGGER.debug(
                "[NetgearSwitchConnector.get_unique_id] switch_model is None, "
                "try NetgearSwitchConnector.autodetect_model"
            )
            self.autodetect_model()
            _LOGGER.debug(
                "[NetgearSwitchConnector.get_unique_id] now switch_model is %s",
                str(self.switch_model),
            )
        model_lower = self.switch_model.MODEL_NAME.lower()
        return model_lower + "_" + self.host.replace(".", "_")

    def _handle_soft_authentication_failure(
        self, response: Response | BaseResponse
    ) -> None:
        """Handle soft authentication failure."""
        # Clear cached login data
        self._page_fetcher.clear_login_page_response()

        if "content" not in dir(response):
            message = "No content in login form response."
            raise LoginFailedError(message)

        # Handling Error Messages
        error_msg = self._page_parser.parse_error(response)
        response_text = response.content.decode("utf-8").lower()

        # Check for maximum sessions error
        if "maximum" in response_text and "session" in response_text:
            _LOGGER.warning(
                "[NetgearSwitchConnector.handle_soft_authentication_failure]"
                " [IP: %s] Maximum sessions reached on switch",
                self.host,
            )
            raise MaxSessionsError(
                "Maximum number of sessions reached. "
                "Please log out of the switch's web interface or restart the switch."
            )

        if error_msg:
            _LOGGER.warning(
                "[NetgearSwitchConnector.handle_soft_authentication_failure]"
                ' [IP: %s] Response from switch: "%s"',
                self.host,
                error_msg,
            )
        else:
            _LOGGER.debug(
                "[NetgearSwitchConnector.handle_soft_authentication_failure]"
                " No error message found in response:\n\n%s",
                response.content.decode("utf-8"),
            )

        self._authentication_failure_count += 1
        if self._authentication_failure_count >= MAX_AUTHENTICATION_FAILURES:
            count = self._authentication_failure_count
            message = f"Too many authentication failures ({count})."
            raise LoginFailedError(message)

    def get_login_cookie(self) -> bool:
        """Login and save returned cookie."""
        if not self.switch_model or self.switch_model.MODEL_NAME == "":
            self.autodetect_model()
        if not self._page_fetcher.get_login_page_response():
            self._page_fetcher.check_login_url(self.switch_model)
        rand = self._page_parser.parse_login_form_rand(
            self._page_fetcher.get_login_page_response()
        )

        response = self._page_fetcher.get_login_response(
            self.switch_model, self._password, rand
        )

        _LOGGER.debug(
            "[NetgearSwitchConnector.get_login_cookie] looking for cookies: %s",
            ", ".join(self.switch_model.ALLOWED_COOKIE_TYPES),
        )
        # GS31xEP(P) series switches return the cookie value in a hidden form element
        self._gambit = self._page_parser.parse_gambit_tag(response)
        if self._gambit:
            self._page_fetcher.set_cookie(
                self.switch_model.ALLOWED_COOKIE_TYPES[0], self._gambit
            )
            _LOGGER.debug("[NetgearSwitchConnector.get_login_cookie] Found Gambit tag:")
            _LOGGER.debug(
                "[NetgearSwitchConnector.get_login_cookie] Setting cookie %s=%s",
                self.switch_model.ALLOWED_COOKIE_TYPES[0],
                str(self._gambit),
            )
            self._authentication_failure_count = 0
            return True
        # Other switches return a cookie on successful login
        for ct in self.switch_model.ALLOWED_COOKIE_TYPES:
            cookie = response.cookies.get(ct, None)
            if cookie:
                _LOGGER.debug(
                    "[NetgearSwitchConnector.get_login_cookie] Found cookie %s", ct
                )
                self._page_fetcher.set_cookie(ct, cookie)
                self._authentication_failure_count = 0
                return True
        _LOGGER.debug(
            "[NetgearSwitchConnector.get_login_cookie] "
            "No Gambit tag or valid cookie found."
        )
        self._handle_soft_authentication_failure(response)
        return False

    def get_cookie(self) -> tuple[str | None, str | None]:
        """Return cookie."""
        return self._page_fetcher.get_cookie()

    def set_cookie(self, name: str, content: str) -> None:
        """Return cookie."""
        if name == "gambitCookie":
            self._gambit = content
        return self._page_fetcher.set_cookie(name, content)

    def delete_login_cookie(self) -> bool:
        """Logout and delete cookie."""
        """Only used while testing. Prevents "Maximum number of sessions" error."""
        if not self.switch_model or self.switch_model.MODEL_NAME == "":
            self.autodetect_model()
        response = BaseResponse()
        for template in self.switch_model.LOGOUT_TEMPLATES:
            url = template["url"].format(ip=self.host)
            method = template["method"]
            data = {}
            self._page_fetcher.set_data_from_template(template, self, data)

            if not self.get_offline_mode():
                try:
                    response = self._page_fetcher.request(method, url, data)
                    break  # Exit the loop if the request is successful
                except NotLoggedInError:
                    response.status_code = status_code_unauthorized
                    response.content = b""
                    break
                except PageFetcherConnectionError:
                    _LOGGER.debug(
                        "NetgearSwitchConnector.fetch_page: "
                        "caught PageFetcherConnectionError"
                    )
                    response.status_code = status_code_no_response
                    response.content = b""
                    break  # Stop retrying after a connection error
            else:
                response = self._page_fetcher.get_page_from_file(url)

            if response.status_code != status_code_not_found:
                break

        _LOGGER.debug(
            "[NetgearSwitchConnector.delete_login_cookie] "
            "logout response status code=%s",
            response.status_code,
        )
        self._page_fetcher.clear_cookie()
        return response.status_code != status_code_not_found

    def reboot(self) -> bool:
        """Reboot the switch."""
        if not self.switch_model.has_reboot_button():
            _LOGGER.info("[NetgearSwitchConnector.reboot] Reboot button not available.")
            return False

        response = BaseResponse()
        for template in self.switch_model.SWITCH_REBOOT_TEMPLATES:
            url = template["url"].format(ip=self.host)
            method = template["method"]
            data = {}
            if not self.get_offline_mode():
                self._page_fetcher.set_data_from_template(template, self, data)
            response = self.fetch_page(method, url, data)
            if self._page_parser.parse_reboot_success(response):
                return True

        _LOGGER.debug(
            "[NetgearSwitchConnector.reboot] failed to load any page of templates: %s",
            self.switch_model.SWITCH_REBOOT_TEMPLATES,
        )
        return False

    def fetch_page(self, method: str, url: str, data: dict) -> Response | BaseResponse:
        """Fetch url and retry when first response is a redirect to the login page."""
        response = BaseResponse()
        if not self.get_offline_mode():
            for attempt in range(2):
                try:
                    response = self._page_fetcher.request(method, url, data)
                    break  # Exit the loop if the request is successful
                except NotLoggedInError as error:
                    if attempt == 0 and self.get_login_cookie():
                        continue  # Retry the request if login cookie is available
                    message = "Not logged in and unable to login."
                    raise LoginFailedError(message) from error
                except PageFetcherConnectionError:
                    _LOGGER.debug(
                        "NetgearSwitchConnector.fetch_page: "
                        "caught PageFetcherConnectionError"
                    )
                    response.status_code = status_code_no_response
                    response.content = b""
                    break  # Stop retrying after a connection error
        else:
            response = self._page_fetcher.get_page_from_file(url)
        return response

    def fetch_page_from_templates(self, templates: list) -> Response | BaseResponse:
        """Return response for 1st successful request from templates."""
        response = BaseResponse()
        for template in templates:
            url = template["url"].format(ip=self.host)
            method = template["method"]
            data = {}
            if not self.get_offline_mode():
                self._page_fetcher.set_data_from_template(template, self, data)
            response = self.fetch_page(method, url, data)
            if self._page_fetcher.has_ok_status(response):
                return response
        message = f"Failed to load any page of templates: {templates}"
        raise PageNotLoadedError(message)

    def get_switch_infos(self) -> dict[str, Any]:
        """Return dict with all available statistics."""
        if not self.switch_model.MODEL_NAME:
            self.autodetect_model()

        current_data = {}
        switch_data = {}

        if not self._loaded_switch_metadata:
            self._get_switch_metadata()
        switch_data.update(**self._loaded_switch_metadata)

        # Fetch Port Status
        time.sleep(self.sleep_time)
        switch_data.update(self._get_port_status())

        # Hold fire
        time.sleep(self.sleep_time)

        _start_time = time.perf_counter()

        current_data = self._initialize_current_data()
        # Parse port statistics html
        current_data.update(self._get_port_statistics())

        if not self.get_offline_mode():
            sample_time = _start_time - self._previous_timestamp
        else:
            sample_time = 0
        switch_data["response_time_s"] = round(sample_time, 1)

        self._update_current_data(current_data, switch_data, sample_time)

        switch_data.update(self._updated_switch_data(current_data))

        # Partially supported models fail parsing below this line
        if not self.switch_model.SUPPORTED:
            return switch_data

        if len(self.switch_model.POE_PORTS):
            time.sleep(self.sleep_time)
            try:
                switch_data.update(self._get_poe_port_config())
            except PageNotLoadedError:
                _LOGGER.warning(
                    "[NetgearSwitchConnector.get_switch_infos] "
                    "Failed to fetch PoE port config for %s, skipping",
                    self.host,
                )
            except PageFetcherConnectionError:
                _LOGGER.warning(
                    "[NetgearSwitchConnector.get_switch_infos] "
                    "Connection error fetching PoE port config for %s, skipping",
                    self.host,
                )
            time.sleep(self.sleep_time)
            try:
                switch_data.update(self._get_poe_port_status())
            except PageNotLoadedError:
                _LOGGER.warning(
                    "[NetgearSwitchConnector.get_switch_infos] "
                    "Failed to fetch PoE port status for %s, skipping",
                    self.host,
                )
            except PageFetcherConnectionError:
                _LOGGER.warning(
                    "[NetgearSwitchConnector.get_switch_infos] "
                    "Connection error fetching PoE port status for %s, skipping",
                    self.host,
                )

        # set previous data
        self._previous_timestamp = time.perf_counter()
        self._previous_data = current_data

        return switch_data

    def _get_switch_metadata(self) -> None:
        if not self.switch_model:
            self.autodetect_model()
        page = self.fetch_page_from_templates(self.switch_model.SWITCH_INFO_TEMPLATES)
        if not page.content:
            return
        switch_metadata = {"switch_ip": self.host}
        self._client_hash = self._page_parser.parse_client_hash(page)

        if self.switch_model.SWITCH_LED_TEMPLATES:
            switch_metadata.update(self._page_parser.parse_led_status(page))

        # Avoid a second call on next get_switch_infos() call
        self._loaded_switch_metadata = (
            switch_metadata | self._page_parser.parse_switch_metadata(page)
        )

    def _get_port_statistics(self) -> dict[str, Any]:
        response = self.fetch_page_from_templates(
            self.switch_model.PORT_STATISTICS_TEMPLATES
        )
        return self._page_parser.parse_port_statistics(response, self.ports)

    def _initialize_current_data(self) -> dict:
        """Initialize current data dictionary with default values."""
        current_data = {}
        for key in [
            "sum_port_traffic_rx",
            "sum_port_traffic_tx",
            "sum_port_crc_errors",
            "sum_port_speed_rx",
            "sum_port_speed_tx",
        ]:
            current_data[key] = 0
        return current_data

    def _update_current_data(
        self, current_data: dict, switch_data: dict, sample_time: float
    ) -> None:
        """Update current data with calculated values."""
        sample_factor = 1 if not sample_time else 1 / sample_time
        for port_number0 in range(self.ports):
            try:
                port_number = port_number0 + 1
                current_data[f"port_{port_number}_traffic_rx"] = (
                    0
                    if (self._previous_data["traffic_rx"][port_number0] == 0)
                    else (
                        current_data["traffic_rx"][port_number0]
                        - self._previous_data["traffic_rx"][port_number0]
                    )
                )
                current_data[f"port_{port_number}_traffic_tx"] = (
                    0
                    if (self._previous_data["traffic_tx"][port_number0] == 0)
                    else (
                        current_data["traffic_tx"][port_number0]
                        - self._previous_data["traffic_tx"][port_number0]
                    )
                )
                current_data[f"port_{port_number}_crc_errors"] = (
                    0
                    if (self._previous_data["crc_errors"][port_number0] == 0)
                    else (
                        current_data["crc_errors"][port_number0]
                        - self._previous_data["crc_errors"][port_number0]
                    )
                )
                current_data[f"port_{port_number}_sum_rx"] = current_data["sum_rx"][
                    port_number0
                ]
                current_data[f"port_{port_number}_sum_tx"] = current_data["sum_tx"][
                    port_number0
                ]
                current_data[f"port_{port_number}_speed_rx"] = int(
                    current_data[f"port_{port_number}_traffic_rx"] * sample_factor
                )
                current_data[f"port_{port_number}_speed_tx"] = int(
                    current_data[f"port_{port_number}_traffic_tx"] * sample_factor
                )
                current_data[f"port_{port_number}_speed_io"] = (
                    current_data[f"port_{port_number}_speed_rx"]
                    + current_data[f"port_{port_number}_speed_tx"]
                )

            except IndexError:
                _LOGGER.debug("IndexError at port_number0=%s", port_number0)
                continue

            # Lowpass-Filter
            keys = [
                "traffic_rx",
                "traffic_tx",
                "crc_errors",
                "speed_rx",
                "speed_tx",
                "speed_io",
            ]
            for key in keys:
                current_data[f"port_{port_number}_{key}"] = max(
                    current_data[f"port_{port_number}_{key}"], 0
                )

            # Access old data if value is 0
            port_status_is_connected = (
                switch_data.get(f"port_{port_number}_status") == "on"
            )
            if port_status_is_connected:
                keys = ["sum_rx", "sum_tx", "speed_io"]
                for key in keys:
                    if current_data[f"port_{port_number}_{key}"] < 0:
                        current_data[f"port_{port_number}_{key}"] = self._previous_data[
                            key
                        ][port_number0]
                        current_data[key][port_number0] = current_data[
                            f"port_{port_number}_{key}"
                        ]
                        _LOGGER.info(
                            "Fallback to previous data: port_nr=%s port_%s=%s",
                            port_number,
                            key,
                            current_data[f"port_{port_number}_{key}"],
                        )

            # Highpass-Filter (max 1e9 B/s = 1GB/s per port)
            hp_max_traffic = 1e9 / sample_factor
            current_data[f"port_{port_number}_traffic_rx"] = min(
                current_data[f"port_{port_number}_traffic_rx"], hp_max_traffic
            )
            current_data[f"port_{port_number}_traffic_tx"] = min(
                current_data[f"port_{port_number}_traffic_tx"], hp_max_traffic
            )
            current_data[f"port_{port_number}_crc_errors"] = min(
                current_data[f"port_{port_number}_crc_errors"], hp_max_traffic
            )

            # Highpass-Filter (max 1e9 B/s = 1GB/s per port)
            # speed is already normalized to 1s
            hp_max_speed = 1e9
            current_data[f"port_{port_number}_speed_rx"] = min(
                current_data[f"port_{port_number}_speed_rx"], hp_max_speed
            )
            current_data[f"port_{port_number}_speed_tx"] = min(
                current_data[f"port_{port_number}_speed_tx"], hp_max_speed
            )

            # Sum up all metrics in key dict
            for key in [
                "traffic_rx",
                "traffic_tx",
                "crc_errors",
                "speed_rx",
                "speed_tx",
            ]:
                current_data[f"sum_port_{key}"] += current_data[
                    f"port_{port_number}_{key}"
                ]

            current_data["sum_port_speed_io"] = (
                current_data["sum_port_speed_rx"] + current_data["sum_port_speed_tx"]
            )

            # set for later (previous data)
            current_data["speed_io"][port_number0] = current_data[
                f"port_{port_number}_speed_io"
            ]

    def _updated_switch_data(self, current_data: dict) -> dict:
        switch_data = {}
        for port_number in range(1, self.ports + 1):
            keys = [
                "traffic_rx",
                "traffic_tx",
                "speed_rx",
                "speed_tx",
                "speed_io",
                "sum_rx",
                "sum_tx",
            ]
            for key in keys:
                switch_data[f"port_{port_number}_{key}_mbytes"] = (
                    _from_bytes_to_megabytes(current_data[f"port_{port_number}_{key}"])
                )

        switch_data["sum_port_traffic_rx"] = _from_bytes_to_megabytes(
            current_data["sum_port_traffic_rx"]
        )
        switch_data["sum_port_traffic_tx"] = _from_bytes_to_megabytes(
            current_data["sum_port_traffic_tx"]
        )
        switch_data["sum_port_speed_rx"] = _from_bytes_to_megabytes(
            current_data["sum_port_speed_rx"]
        )
        switch_data["sum_port_speed_tx"] = _from_bytes_to_megabytes(
            current_data["sum_port_speed_tx"]
        )
        switch_data["sum_port_speed_io"] = _from_bytes_to_megabytes(
            current_data["sum_port_speed_io"]
        )

        switch_data[f"port_{port_number}_crc_errors"] = current_data[
            f"port_{port_number}_crc_errors"
        ]
        switch_data["sum_port_crc_errors"] = current_data["sum_port_crc_errors"]
        return switch_data

    def _get_poe_port_config(self) -> dict:
        response = self.fetch_page_from_templates(
            self.switch_model.POE_PORT_CONFIG_TEMPLATES
        )
        return self._page_parser.parse_poe_port_config(response)

    def _get_poe_port_status(self) -> dict:
        response = self.fetch_page_from_templates(
            self.switch_model.POE_PORT_STATUS_TEMPLATES
        )
        return self._page_parser.parse_poe_port_status(response)

    def _get_port_status(self) -> dict:
        switch_data = {}
        response_portstatus = self.fetch_page_from_templates(
            self.switch_model.PORT_STATUS_TEMPLATES
        )
        port_status = self._page_parser.parse_port_status(
            response_portstatus, self.ports
        )

        for port_number in range(1, self.ports + 1):
            if len(port_status) == self.ports:
                switch_data[f"port_{port_number}_status"] = (
                    "on"
                    if port_status[port_number].get("status") in PORT_STATUS_CONNECTED
                    else "off"
                )
                switch_data[f"port_{port_number}_modus_speed"] = (
                    port_status[port_number].get("modus_speed") in PORT_MODUS_SPEED
                )
                port_connection_speed = (
                    port_status[port_number].get("connection_speed").upper()
                )
                port_connection_speeds = {
                    "10G": 10000,
                    "5G": 5000,
                    "2.5G": 2500,
                    "1G": 1000,
                    "1000M": 1000,
                    "100M": 100,
                    "10M": 10,
                }
                if port_connection_speed in port_connection_speeds:
                    switch_data[f"port_{port_number}_connection_speed"] = (
                        port_connection_speeds[port_connection_speed]
                    )
                else:
                    switch_data[f"port_{port_number}_connection_speed"] = 0
            else:
                message = (
                    f"Number of statusses ({len(port_status)})"
                    f" not equal to number of ports({self.ports})"
                )
                raise InvalidPortStatusError(message)
        return switch_data

    def switch_leds(self, state: str) -> bool:
        """Switch poe port on or off."""
        if not self.switch_model.SWITCH_LED_TEMPLATES:
            message = "No LED templates found."
            raise NotImplementedError(message)
        if state not in SWITCH_STATES:
            message = f'State "{state}" not in {SWITCH_STATES}.'
            raise InvalidSwitchStateError(message)
        for template in self.switch_model.SWITCH_LED_TEMPLATES:
            url = template["url"].format(ip=self.host)
            method = template["method"]
            data = self.switch_model.get_switch_led_data(state)  # type: ignore[report-call-issue]
            self._page_fetcher.set_data_from_template(template, self, data)
            _LOGGER.debug("switch_leds data=%s", data)
            response = BaseResponse
            try:
                response = self._page_fetcher.request(method, url, data)
            except NotLoggedInError as error:
                if self.get_login_cookie():
                    response = self._page_fetcher.request(method, url, data)
                else:
                    message = "Not logged in and unable to login."
                    raise LoginFailedError(message) from error
            if (
                self._page_fetcher.has_ok_status(response)
                and str(response.content.strip()) == "b'SUCCESS'"
            ):
                # Clear cached metadata to refetch led status on next poll
                self._loaded_switch_metadata = {}
                return True
            _LOGGER.warning(
                "NetgearSwitchConnector.switch_leds response was %s",
                response.content.strip(),
            )
        return False

    def turn_on_leds(self) -> bool:
        """Turn on front panel LEDs."""
        return self.switch_leds("on")

    def turn_off_leds(self) -> bool:
        """Turn off front panel LEDs."""
        return self.switch_leds("off")

    def switch_poe_port(self, poe_port: int, state: str) -> bool:
        """Switch poe port on or off."""
        if state not in SWITCH_STATES:
            message = f'State "{state}" not in {SWITCH_STATES}.'
            raise InvalidSwitchStateError(message)
        if poe_port in self.poe_ports:
            for template in self.switch_model.SWITCH_POE_PORT_TEMPLATES:
                url = template["url"].format(ip=self.host)
                data = self.switch_model.get_switch_poe_port_data(poe_port, state)  # type: ignore[report-call-issue]
                self._page_fetcher.set_data_from_template(template, self, data)
                _LOGGER.debug("switch_poe_port data=%s", data)
                response = BaseResponse
                try:
                    response = self._page_fetcher.request("post", url, data)
                except NotLoggedInError as error:
                    if self.get_login_cookie():
                        response = self._page_fetcher.request("post", url, data)
                    else:
                        message = "Not logged in and unable to login."
                        raise LoginFailedError(message) from error
                if (
                    self._page_fetcher.has_ok_status(response)
                    and str(response.content.strip()) == "b'SUCCESS'"
                ):
                    return True
                _LOGGER.warning(
                    "NetgearSwitchConnector.switch_poe_port response was %s",
                    response.content.strip(),
                )
        else:
            message = f"Port {poe_port} not in {self.poe_ports}"
            raise InvalidPoEPortError(message)
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
            for template in self.switch_model.CYCLE_POE_PORT_TEMPLATES:
                url = template["url"].format(ip=self.host)
                data = self.switch_model.get_power_cycle_poe_port_data(poe_port)  # type: ignore[report-call-issue]
                self._page_fetcher.set_data_from_template(template, self, data)
                response = Response
                method = template["method"]
                try:
                    response = self._page_fetcher.request(method, url, data)
                except NotLoggedInError as error:
                    if self.get_login_cookie():
                        response = self._page_fetcher.request(method, url, data)
                    else:
                        message = "Not logged in and unable to login."
                        raise LoginFailedError(message) from error

                if (
                    self._page_fetcher.has_ok_status(response)
                    and str(response.content.strip()) == "b'SUCCESS'"
                ):
                    return True
                _LOGGER.warning(
                    "NetgearSwitchConnector.power_cycle_poe_port response was %s",
                    response.content.strip(),
                )
        return False

    def save_pages(self, path_prefix: str = "") -> None:
        """Save all pages to files for debugging."""
        if not self.switch_model or not self.switch_model.MODEL_NAME:
            self.autodetect_model()
        if not Path(path_prefix).exists():
            Path(path_prefix).mkdir(parents=True)
        for template in [
            *self.switch_model.SWITCH_INFO_TEMPLATES,
            *self.switch_model.PORT_STATUS_TEMPLATES,
            *self.switch_model.PORT_STATISTICS_TEMPLATES,
            *self.switch_model.POE_PORT_CONFIG_TEMPLATES,
            *self.switch_model.POE_PORT_STATUS_TEMPLATES,
        ]:
            url = template["url"].format(ip=self.host)
            try:
                response = self.fetch_page_from_templates([template])
            except PageNotLoadedError:
                _LOGGER.warning(
                    "NetgearSwitchConnector.save_pages could not download %s", url
                )
                continue
            if self._page_fetcher.has_ok_status(response):
                page_name = url.split("/")[-1] or DEFAULT_PAGE
                with Path(f"{path_prefix}/{page_name}").open("wb") as file:
                    file.write(response.content)

                if (
                    template in self.switch_model.SWITCH_INFO_TEMPLATES
                    and not self._client_hash
                ):
                    with suppress(NetgearPlusPageParserError):
                        self._client_hash = self._page_parser.parse_client_hash(
                            response
                        )

            else:
                _LOGGER.warning(
                    "NetgearSwitchConnector.save_pages failed with status %s for %s",
                    response.status_code,
                    url,
                )

    def save_autodetect_templates(self, path_prefix: str = "") -> None:
        """Save all pages used to detect the switch model to files for debugging."""
        # These pages should be called unauthenticated, so logout first
        if self.get_cookie() != (None, None):
            _LOGGER.debug("NetgearSwitchConnector.save_autodetect_templates logout")
            self.delete_login_cookie()
        for template in self.switch_model.AUTODETECT_TEMPLATES:
            url = template["url"].format(ip=self.host)
            response = BaseResponse()
            with suppress(NotLoggedInError):
                response = self._page_fetcher.request("get", url)
            if self._page_fetcher.has_ok_status(response):
                page_name = url.split("/")[-1] or DEFAULT_PAGE
                with Path(f"{path_prefix}/{page_name}").open("wb") as file:
                    file.write(response.content)
