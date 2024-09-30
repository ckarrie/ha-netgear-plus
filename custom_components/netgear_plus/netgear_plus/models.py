"""Definitions of auto-detectable Switch models."""


class AutodetectedSwitchModel:
    ALLOWED_COOKIE_TYPES = ["SID"]
    MODEL_NAME = None
    PORTS = None
    POE_PORTS = []
    POE_MAX_POWER_ALL_PORTS = None
    POE_MAX_POWER_SINGLE_PORT = None
    POE_SCHEDULING = False
    CHECKS_AND_RESULTS = []

    AUTODETECT_TEMPLATES = [
        { "method": "get",
          "url": "http://{ip}/login.cgi" },
        { "method": "get",
          "url": "http://{ip}/login.htm" },
        { "method": "get",
          "url": "http://{ip}/" },
    ]

    LOGIN_TEMPLATE = { "method": "post",
                       "url": "http://{ip}/login.cgi",
                        "key": "password" }

    SWITCH_INFO_TEMPLATES = [
        { "method": "get",
          "url": "http://{ip}/switch_info.htm" },
        { "method": "get",
          "url": "http://{ip}/switch_info.cgi" }
    ]
    PORT_STATISTICS_TEMPLATES = [
        { "method": "post",
          "url": "http://{ip}/portStatistics.cgi" }
    ]
    PORT_STATUS_TEMPLATES = [
        { "method": "post",
          "url": "http://{ip}/status.htm" }
    ]
    POE_PORT_CONFIG_TEMPLATES = [

    ]
    LOGOUT_TEMPLATES = [
        { "method": "post",
          "url": "http://{ip}/logout.cgi" }
    ]


    def __init__(self) -> None:
        pass

    def get_autodetect_funcs(self):
        return self.CHECKS_AND_RESULTS


class GS105E(AutodetectedSwitchModel):
    MODEL_NAME = "GS105E"
    PORTS = 5
    CHECKS_AND_RESULTS = [
        ("check_login_form_rand", [True]),
        ("check_login_title_tag", ["GS105E"]),
    ]


class GS105Ev2(AutodetectedSwitchModel):
    MODEL_NAME = "GS105Ev2"
    PORTS = 5
    CHECKS_AND_RESULTS = [
        ("check_login_form_rand", [True]),
        ("check_login_title_tag", ["GS105Ev2"]),
    ]


class GS108E(AutodetectedSwitchModel):
    MODEL_NAME = "GS108E"
    PORTS = 8
    CHECKS_AND_RESULTS = [
        ("check_login_form_rand", [True]),
        ("check_login_title_tag", ["GS108E"]),
        (
            "check_login_switchinfo_tag",
            ["GS308E - 8-Port Gigabit Ethernet Smart Managed Plus Switch"],
        ),
    ]
    ALLOWED_COOKIE_TYPES = ["GS108SID", "SID"]


class GS108Ev3(AutodetectedSwitchModel):
    MODEL_NAME = "GS108Ev3"
    PORTS = 8
    CHECKS_AND_RESULTS = [
        ("check_login_form_rand", [True]),
        ("check_login_title_tag", ["GS108Ev3"]),
        (
            "check_login_switchinfo_tag",
            [
                "GS108Ev3 - 8-Port Gigabit ProSAFE Plus Switch",
                "GS108Ev3 - 8-Port Gigabit Ethernet Smart Managed Plus Switch",
            ],
        ),
    ]
    ALLOWED_COOKIE_TYPES = ["GS108SID", "SID"]


class GS3xxSeries(AutodetectedSwitchModel):
    SWITCH_INFO_TEMPLATES = [
        { "method": "get",
          "url": "http://{ip}/dashboard.cgi" }
    ]
    PORT_STATISTICS_TEMPLATES = [
        { "method": "get",
          "url": "http://{ip}/portStatistics.cgi" }
    ]
    POE_PORT_CONFIG_TEMPLATES = [
        { "method": "get",
          "url": "http://{ip}/PoEPortConfig.cgi" }
    ]
    POE_PORT_STATUS_TEMPLATES = [
        { "method": "get",
          "url": "http://{ip}/getPoePortStatus.cgi" }
    ]


class GS305EP(GS3xxSeries):
    MODEL_NAME = "GS305EP"
    PORTS = 5
    POE_PORTS = [1, 2, 3, 4]
    POE_MAX_POWER_ALL_PORTS = 63
    CHECKS_AND_RESULTS = [
        ("check_login_form_rand", [True]),
        ("check_login_title_tag", ["GS305EP"]),
    ]


class GS308EP(GS3xxSeries):
    MODEL_NAME = "GS308EP"
    PORTS = 8
    POE_PORTS = [1, 2, 3, 4, 5, 6, 7, 8]
    POE_MAX_POWER_ALL_PORTS = 62
    CHECKS_AND_RESULTS = [
        ("check_login_form_rand", [True]),
        ("check_login_title_tag", ["GS308EP"]),
    ]


class GS316EP(GS3xxSeries):
    MODEL_NAME = "GS316EP"
    PORTS = 16
    POE_PORTS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    POE_MAX_POWER_ALL_PORTS = 180
    POE_MAX_POWER_SINGLE_PORT = 30
    POE_SCHEDULING = True
    CHECKS_AND_RESULTS = [
        ("check_login_form_rand", [True]),
        ("check_login_title_tag", ["GS316EP"]),
    ]
    LOGIN_TEMPLATE = { "method": "post",
                       "url": "http://{ip}/redirect.html",
                       "key": "LoginPassword" }


class GS316EPP(GS316EP):
    MODEL_NAME = "GS316EPP"
    POE_POWER_ALL_PORTS = 231
    CHECKS_AND_RESULTS = [
        ("check_login_form_rand", [True]),
        ("check_login_title_tag", ["GS316EPP"]),
    ]


MODELS = [
    GS105E,
    GS105Ev2,
    GS108E,
    GS108Ev3,
    GS305EP,
    GS308EP,
    GS316EP,
    GS316EPP,
]
