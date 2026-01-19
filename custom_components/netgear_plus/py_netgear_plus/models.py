"""Definitions of auto-detectable Switch models."""

from typing import ClassVar

from py_netgear_plus.utils import get_all_child_classes_list


class MultipleModelsDetectedError(Exception):
    """Detection of switch model was not unique."""


class SwitchModelNotDetectedError(Exception):
    """None of the models passed the tests."""


class PortNumberOutofRangeError(Exception):
    """Port number out of range."""


class InvalidCryptFunctionError(Exception):
    """No implementation for the defined CRYPT_FUNCTION."""


class AutodetectedSwitchModel:
    """Base class definition for Netgear Plus Switch Models."""

    SUPPORTED = True
    ALLOWED_COOKIE_TYPES: ClassVar = ["SID"]
    MODEL_NAME = ""
    PORTS = 0
    POE_PORTS: ClassVar = []
    POE_MAX_POWER_ALL_PORTS = None
    POE_MAX_POWER_SINGLE_PORT = None
    POE_SCHEDULING = False
    CHECKS_AND_RESULTS: ClassVar = []

    AUTODETECT_TEMPLATES: ClassVar = [
        {"method": "get", "url": "http://{ip}/login.cgi"},
        {"method": "get", "url": "http://{ip}/login.htm"},
        {"method": "get", "url": "http://{ip}/"},
    ]

    CRYPT_FUNCTION: ClassVar = "merge_hash"
    LOGIN_TEMPLATE: ClassVar = {
        "method": "post",
        "url": "http://{ip}/login.cgi",
        "params": {"password": "_password_hash"},
    }

    SWITCH_INFO_TEMPLATES: ClassVar = [
        {"method": "get", "url": "http://{ip}/switch_info.htm"},
        {"method": "get", "url": "http://{ip}/switch_info.cgi"},
    ]
    SWITCH_LED_TEMPLATES: ClassVar = []
    PORT_STATISTICS_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/portStatistics.cgi",
            "params": {"hash": "_client_hash"},
        },
        {
            "method": "post",
            "url": "http://{ip}/port_statistics.htm",
            "params": {"hash": "_client_hash"},
        },
    ]
    PORT_STATUS_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/status.htm",
            "params": {"hash": "_client_hash"},
        }
    ]
    POE_PORT_CONFIG_TEMPLATES: ClassVar = []
    SWITCH_POE_PORT_TEMPLATES: ClassVar = []
    CYCLE_POE_PORT_TEMPLATES: ClassVar = []
    POE_PORT_STATUS_TEMPLATES: ClassVar = []
    LOGOUT_TEMPLATES: ClassVar = [{"method": "post", "url": "http://{ip}/logout.cgi"}]
    SWITCH_REBOOT_TEMPLATES: ClassVar = []

    def __init__(self) -> None:
        """Empty contructor."""

    def get_autodetect_funcs(self) -> list:
        """Return list with detection functions."""
        return self.CHECKS_AND_RESULTS

    def get_switch_poe_port_data(self, poe__port: int, state: str) -> dict:
        """Return empty dict. Implement on model level."""
        del poe__port, state
        return {}

    def get_power_cycle_poe_port_data(self, poe_port: int) -> dict:
        """Return empty dict. Implement on model level."""
        del poe_port
        return {}

    def has_led_switch(self) -> bool:
        """Return true when front panel LED can be switched."""
        return bool(self.SWITCH_LED_TEMPLATES)

    def get_switch_led_data(self, state: str) -> dict:
        """Return empty dict. Implement on model level."""
        del state
        return {}

    def has_reboot_button(self) -> bool:
        """Return true when switch reboot is supported."""
        return bool(self.SWITCH_REBOOT_TEMPLATES)


class GS105E(AutodetectedSwitchModel):
    """Definition for Netgear GS105E model."""

    MODEL_NAME = "GS105E"
    PORTS = 5
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS105E"]),
    ]


class GS105Ev2(AutodetectedSwitchModel):
    """Definition for Netgear GS105Ev2 model."""

    MODEL_NAME = "GS105Ev2"
    PORTS = 5
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS105Ev2"]),
    ]
    PORT_STATISTICS_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/portStatistics.cgi",
        }
    ]
    PORT_STATUS_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/status.cgi",
        }
    ]
    LOGOUT_TEMPLATES: ClassVar = [{"method": "get", "url": "http://{ip}/logout.cgi"}]


class GS105PE(GS105Ev2):
    """Definition for Netgear GS105PE model."""

    MODEL_NAME = "GS105PE"
    PORTS = 5
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS105PE"]),
    ]


class GS108E(AutodetectedSwitchModel):
    """Definition for Netgear GS108E model."""

    MODEL_NAME = "GS108E"
    PORTS = 8
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS108E"]),
        (
            "parse_login_switchinfo_tag",
            ["GS308E - 8-Port Gigabit Ethernet Smart Managed Plus Switch"],
        ),
    ]
    ALLOWED_COOKIE_TYPES: ClassVar = ["GS108SID", "SID"]


class GS108Ev3(AutodetectedSwitchModel):
    """Definition for Netgear GS108Ev3 model."""

    MODEL_NAME = "GS108Ev3"
    PORTS = 8
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS108Ev3"]),
        (
            "parse_login_switchinfo_tag",
            [
                "GS108Ev3 - 8-Port Gigabit ProSAFE Plus Switch",
                "GS108Ev3 - 8-Port Gigabit Ethernet Smart Managed Plus Switch",
            ],
        ),
    ]
    SWITCH_REBOOT_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/device_reboot.cgi",
            "params": {"CBox": "literal:on", "hash": "_client_hash"},
        }
    ]
    ALLOWED_COOKIE_TYPES: ClassVar = ["GS108SID", "SID"]


class GS108Ev4(AutodetectedSwitchModel):
    """Definition for Netgear GW108Ev4 model."""

    MODEL_NAME = "GS108Ev4"
    PORTS = 8
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS108Ev4"]),
    ]
    SWITCH_INFO_TEMPLATES: ClassVar = [
        {"method": "get", "url": "http://{ip}/dashboard.cgi"}
    ]
    PORT_STATUS_TEMPLATES: ClassVar = [
        {"method": "get", "url": "http://{ip}/dashboard.cgi"}
    ]
    PORT_STATISTICS_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/portStatistics.cgi",
            "params": {"hash": "_client_hash"},
        },
    ]
    ALLOWED_COOKIE_TYPES: ClassVar = ["GS108SID", "SID"]


class GS108PEv3(AutodetectedSwitchModel):
    """Definition for Netgear GS108PEv3 model."""

    MODEL_NAME = "GS108PEv3"
    PORTS = 8
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS108PEv3"]),
        (
            "parse_login_switchinfo_tag",
            [
                "GS108PEv3 - 8-Port Gigabit ProSAFE Plus Switch",
                "GS108PEv3 - 8-Port Gigabit Ethernet Smart Managed Plus Switch",
            ],
        ),
    ]
    ALLOWED_COOKIE_TYPES: ClassVar = ["GS108SID", "SID"]


class GS305E(AutodetectedSwitchModel):
    """Definition for Netgear GS305E model."""

    MODEL_NAME = "GS305E"
    PORTS = 5
    ALLOWED_COOKIE_TYPES: ClassVar = ["SID"]

    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS305E"]),
    ]

    SWITCH_INFO_TEMPLATES: ClassVar = [
        {"method": "get", "url": "http://{ip}/switch_info.cgi"},
    ]

    PORT_STATUS_TEMPLATES: ClassVar = [
        {"method": "get", "url": "http://{ip}/status.cgi"},
    ]

    PORT_STATISTICS_TEMPLATES: ClassVar = [
        {"method": "get", "url": "http://{ip}/portStatistics.cgi"},
    ]


class GS308E(AutodetectedSwitchModel):
    """Definition for Netgear GS308E model."""

    MODEL_NAME = "GS308E"
    PORTS = 8
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS308E"]),
        (
            "parse_login_switchinfo_tag",
            [
                "GS308E - 8-Port Gigabit ProSAFE Plus Switch",
                "GS308E - 8-Port Gigabit Ethernet Smart Managed Plus Switch",
            ],
        ),
    ]
    ALLOWED_COOKIE_TYPES: ClassVar = ["GS108SID", "SID"]


class GS308Ev4(GS108Ev4):
    """Definition for Netgear GS308Ev3 model."""

    MODEL_NAME = "GS308Ev4"
    PORTS = 8
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS308Ev4"]),
    ]
    SWITCH_REBOOT_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/device_reboot.cgi",
            "params": {"hash": "_client_hash"},
        }
    ]
    ALLOWED_COOKIE_TYPES: ClassVar = ["SID"]


class EMxSeries(AutodetectedSwitchModel):
    """Parent class definition for Netgear GSxxxEMX and XSxxxEM models."""

    LOGIN_TEMPLATE: ClassVar = {
        "method": "post",
        "url": "http://{ip}/homepage.html",
        "params": {"LoginPassword": "_password_hash"},
    }
    ALLOWED_COOKIE_TYPES: ClassVar = ["gambitCookie"]
    SWITCH_INFO_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/sysInfo.html",
            "params": {"Gambit": "_gambit"},
        }
    ]
    PORT_STATUS_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/port_settings.html",
            "params": {"Gambit": "_gambit"},
        }
    ]
    PORT_STATISTICS_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/interface_stats.html",
            "params": {"Gambit": "_gambit"},
        }
    ]
    LOGOUT_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/logout.html",
            "params": {"Gambit": "_gambit"},
        }
    ]


class GS110EMX(EMxSeries):
    """Definition for Netgear GS110EMX model."""

    MODEL_NAME = "GS110EMX"
    PORTS = 10
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS110EMX"]),
    ]


class XS512EM(EMxSeries):
    """Definition for Netgear XS512EM model."""

    MODEL_NAME = "XS512EM"
    PORTS = 12
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["XS512EM"]),
    ]


class GS30xSeries(AutodetectedSwitchModel):
    """Parent class definition for Netgear GS30x series."""

    SWITCH_INFO_TEMPLATES: ClassVar = [
        {"method": "get", "url": "http://{ip}/dashboard.cgi"}
    ]
    SWITCH_LED_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/port_led.cgi",
            "params": {"hash": "_client_hash"},
        }
    ]
    PORT_STATUS_TEMPLATES: ClassVar = SWITCH_INFO_TEMPLATES
    PORT_STATISTICS_TEMPLATES: ClassVar = [
        {"method": "get", "url": "http://{ip}/portStatistics.cgi"}
    ]
    POE_PORT_CONFIG_TEMPLATES: ClassVar = [
        {"method": "get", "url": "http://{ip}/PoEPortConfig.cgi"}
    ]
    SWITCH_POE_PORT_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/PoEPortConfig.cgi",
            "params": {"hash": "_client_hash"},
        }
    ]
    CYCLE_POE_PORT_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/PoEPortConfig.cgi",
            "params": {"hash": "_client_hash"},
        }
    ]
    POE_PORT_STATUS_TEMPLATES: ClassVar = [
        {"method": "get", "url": "http://{ip}/getPoePortStatus.cgi"}
    ]

    SWITCH_REBOOT_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/device_reboot.cgi",
            "params": {"hash": "_client_hash"},
        }
    ]

    def get_switch_poe_port_data(self, poe_port: int, state: str) -> dict:
        """Fill dict with form fields for switching a PoE port."""
        return {
            "ACTION": "Apply",
            "portID": poe_port - 1,
            "ADMIN_MODE": 1 if state == "on" else 0,
            "PORT_PRIO": 0,
            "POW_MOD": 3,
            "POW_LIMT_TYP": 0,
            "DETEC_TYP": 2,
            "DISCONNECT_TYP": 2,
        }

    def get_power_cycle_poe_port_data(self, poe_port: int) -> dict:
        """Return empty dict. Implement on model level."""
        return {
            "ACTION": "Reset",
            "port" + str(poe_port - 1): "checked",
        }

    def get_switch_led_data(self, state: str) -> dict:
        """Return empty dict. Implement on model level."""
        return {
            "portled": 0 if state == "on" else 2,
        }


class GS30xEPxSeries(GS30xSeries):
    """Parent class definition for Netgear GS30xEPx series."""

    def get_switch_poe_port_data(self, poe_port: int, state: str) -> dict:
        """Fill dict with form fields for switching a PoE port."""
        return {
            "ACTION": "Apply",
            "portID": poe_port - 1,
            "ADMIN_MODE": 1 if state == "on" else 0,
            "PORT_PRIO": 0,
            "POW_MOD": 3,
            "POW_LIMT_TYP": 2,
            "DETEC_TYP": 2,
            "DISCONNECT_TYP": 2,
        }


class GS305EP(GS30xEPxSeries):
    """Definition for Netgear GS305EP model."""

    MODEL_NAME = "GS305EP"
    PORTS = 5
    POE_PORTS: ClassVar = [1, 2, 3, 4]
    POE_MAX_POWER_ALL_PORTS = 63
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS305EP"]),
    ]


class GS305EPP(GS30xEPxSeries):
    """Definition for Netgear GS305EPP model."""

    MODEL_NAME = "GS305EPP"
    PORTS = 5
    POE_PORTS: ClassVar = [1, 2, 3, 4]
    POE_MAX_POWER_ALL_PORTS = 120
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS305EPP"]),
    ]


class GS308EP(GS30xSeries):
    """Definition for Netgear GS308EP model."""

    MODEL_NAME = "GS308EP"
    PORTS = 8
    POE_PORTS: ClassVar = [1, 2, 3, 4, 5, 6, 7, 8]
    POE_MAX_POWER_ALL_PORTS = 62
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS308EP"]),
    ]


class GS308EPP(GS30xEPxSeries):
    """Definition for Netgear GS308EP model."""

    MODEL_NAME = "GS308EPP"
    PORTS = 8
    POE_PORTS: ClassVar = [1, 2, 3, 4, 5, 6, 7, 8]
    POE_MAX_POWER_ALL_PORTS = 123
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS308EPP"]),
    ]


class GS316Series(GS30xSeries):
    """Parent class definition for Netgear GS316xx models."""

    PORTS = 16
    POE_PORTS: ClassVar = [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
    ]
    POE_SCHEDULING = False  # True
    LOGIN_TEMPLATE: ClassVar = {
        "method": "post",
        "url": "http://{ip}/homepage.html",
        "params": {"LoginPassword": "_password_hash"},
    }
    ALLOWED_COOKIE_TYPES: ClassVar = ["gambitCookie"]
    SWITCH_INFO_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/dashboard.html",
            "params": {"Gambit": "_gambit"},
        }
    ]
    SWITCH_LED_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/iss/specific/leds.html",
            "params": {"Gambit": "_gambit"},
        }
    ]
    PORT_STATUS_TEMPLATES: ClassVar = SWITCH_INFO_TEMPLATES
    PORT_STATISTICS_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/interface_stats.html",
            "params": {"Gambit": "_gambit"},
        }
    ]
    POE_PORT_CONFIG_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/poePortConf.html",
            "params": {"Gambit": "_gambit"},
        }
    ]
    SWITCH_POE_PORT_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/iss/specific/poePortConf.html",
            "params": {"Gambit": "_gambit"},
        }
    ]
    CYCLE_POE_PORT_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/iss/specific/poePortConf.html",
            "params": {"Gambit": "_gambit"},
        }
    ]
    POE_PORT_STATUS_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/poePortStatus.html",
            "params": {"Gambit": "_gambit", "GetData": "literal:TRUE"},
        }
    ]
    LOGOUT_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/logout.html",
            "params": {"Gambit": "_gambit"},
        }
    ]

    SWITCH_REBOOT_TEMPLATES: ClassVar = []

    def get_switch_poe_port_data(self, poe_port: int, state: str) -> dict:
        """Fill dict with form fields for switching a PoE port."""
        return {
            "TYPE": "submitPoe",
            "PORT_NO": poe_port,
            "POWER_LIMIT_VALUE": 300,
            "PRIORITY": "NOTSET",
            "POWER_MODE": "NOTSET",
            "POWER_LIMIT_TYPE": "NOTSET",
            "DETECTION": "NOTSET",
            "ADMIN_STATE": 1 if state == "on" else 0,
            "DISCONNECT_TYPE": "NOTSET",
        }

    def get_power_cycle_poe_port_data(self, poe_port: int) -> dict:
        """Return form fields for PoE port cycle."""
        if poe_port not in self.POE_PORTS:
            message = f"Port number {poe_port} out of range."
            raise PortNumberOutofRangeError(message)
        poeport_string = ["0"] * len(self.POE_PORTS)
        poeport_string[poe_port - 1] = "1"
        return {
            "TYPE": "resetPoe",
            "PoePort": "".join(poeport_string),
        }

    def get_switch_led_data(self, state: str) -> dict:
        """Return empty dict. Implement on model level."""
        return {
            "PORT_LED_STATUS": 1 if state == "on" else 0,
        }


class GS316EP(GS316Series):
    """Definition for Netgear GS316EP model."""

    MODEL_NAME = "GS316EP"
    POE_MAX_POWER_ALL_PORTS = 180
    POE_MAX_POWER_SINGLE_PORT = 30
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS316EP"]),
    ]


class GS316EPP(GS316EP):
    """Definition for Netgear GS316EPP model."""

    MODEL_NAME = "GS316EPP"
    POE_POWER_ALL_PORTS = 231
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["GS316EPP"]),
    ]


class JGSxxxSeries(AutodetectedSwitchModel):
    """Parent class definition for Netgear JGSxxx models."""

    CRYPT_FUNCTION: ClassVar = "hex_hmac_md5"
    LOGIN_TEMPLATE: ClassVar = {
        "method": "post",
        "url": "http://{ip}/login.htm",
        "params": {
            "submitId": "literal:pwdLogin",
            "password": "_password_hash",
            "submitEnd": "literal:",
        },
    }
    SWITCH_INFO_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/config/status_switch_info.htm",
        },
    ]
    PORT_STATUS_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/config/status_status.htm",
        },
    ]
    PORT_STATISTICS_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/config/monitoring_port_statistics.htm",
        }
    ]


class JGS516PE(JGSxxxSeries):
    """Definition for Netgear JGS516PE model."""

    MODEL_NAME = "JGS516PE"
    PORTS = 16
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [False]),
        ("parse_first_script_tag", ["JGS516PE"]),
    ]


class JGS524Ev2(JGSxxxSeries):
    """Definition for Netgear JGS524Ev2 model."""

    MODEL_NAME = "JGS524Ev2"
    PORTS = 24
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [False]),
        ("parse_first_script_tag", ["JGS524Ev2"]),
    ]


class GS116Ev2(JGSxxxSeries):
    """Definition for Netgear GS116Ev2 model."""

    MODEL_NAME = "GS116Ev2"
    PORTS = 16
    POE_PORTS: ClassVar = []
    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [False]),
        ("parse_first_script_tag", ["GS116Ev2"]),
    ]


class MS108EUP(AutodetectedSwitchModel):
    """Definition for Netgear MS108EUP model (Multi-Gig 8-Port PoE++ Ultra60)."""

    MODEL_NAME = "MS108EUP"
    PORTS = 8
    POE_PORTS: ClassVar = [1, 2, 3, 4, 5, 6, 7, 8]
    POE_MAX_POWER_ALL_PORTS = 230  # 230W total PoE budget
    POE_MAX_POWER_SINGLE_PORT = 60  # Ultra60 PoE++

    AUTODETECT_TEMPLATES: ClassVar = [
        {"method": "get", "url": "http://{ip}/wmi/login"},
    ]

    CHECKS_AND_RESULTS: ClassVar = [
        ("check_login_form_rand", [True]),
        ("parse_login_title_tag", ["MS108EUP"]),
    ]

    LOGIN_TEMPLATE: ClassVar = {
        "method": "post",
        "url": "http://{ip}/homepage.html",
        "params": {"LoginPassword": "_password_hash"},
    }
    ALLOWED_COOKIE_TYPES: ClassVar = ["gambitCookie"]

    SWITCH_INFO_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/dashboard.html",
            "params": {"Gambit": "_gambit"},
        }
    ]

    SWITCH_LED_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/iss/specific/leds.html",
            "params": {"Gambit": "_gambit"},
        }
    ]

    PORT_STATUS_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/dashboard.html",
            "params": {"Gambit": "_gambit"},
        }
    ]

    PORT_STATISTICS_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/interface_stats.html",
            "params": {"Gambit": "_gambit"},
        }
    ]

    POE_PORT_CONFIG_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/poePortConf.html",
            "params": {"Gambit": "_gambit"},
        }
    ]

    SWITCH_POE_PORT_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/iss/specific/poePortConf.html",
            "params": {"Gambit": "_gambit"},
        }
    ]

    CYCLE_POE_PORT_TEMPLATES: ClassVar = [
        {
            "method": "post",
            "url": "http://{ip}/iss/specific/poePortConf.html",
            "params": {"Gambit": "_gambit"},
        }
    ]

    POE_PORT_STATUS_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/poePortStatus.html",
            "params": {"Gambit": "_gambit", "GetData": "literal:TRUE"},
        }
    ]

    LOGOUT_TEMPLATES: ClassVar = [
        {
            "method": "get",
            "url": "http://{ip}/iss/specific/logout.html",
            "params": {"Gambit": "_gambit"},
        }
    ]

    SWITCH_REBOOT_TEMPLATES: ClassVar = []

    def get_switch_poe_port_data(self, poe_port: int, state: str) -> dict:
        """Fill dict with form fields for switching a PoE port."""
        return {
            "TYPE": "submitPoe",
            "PORT_NO": poe_port,
            "POWER_LIMIT_VALUE": 600,  # 60W max for Ultra60
            "PRIORITY": "NOTSET",
            "POWER_MODE": "NOTSET",
            "POWER_LIMIT_TYPE": "NOTSET",
            "DETECTION": "NOTSET",
            "ADMIN_STATE": 1 if state == "on" else 0,
            "DISCONNECT_TYPE": "NOTSET",
        }

    def get_power_cycle_poe_port_data(self, poe_port: int) -> dict:
        """Return form fields for PoE port cycle."""
        if poe_port not in self.POE_PORTS:
            message = f"Port number {poe_port} out of range."
            raise PortNumberOutofRangeError(message)
        poeport_string = ["0"] * len(self.POE_PORTS)
        poeport_string[poe_port - 1] = "1"
        return {
            "TYPE": "resetPoe",
            "PoePort": "".join(poeport_string),
        }

    def get_switch_led_data(self, state: str) -> dict:
        """Return form fields for LED control."""
        return {
            "PORT_LED_STATUS": 1 if state == "on" else 0,
        }


MODELS = get_all_child_classes_list(AutodetectedSwitchModel, "MODEL_NAME")
