"""Definitions of auto-detectable Switch models."""


class AutodetectedSwitchModel:
    MODEL_NAME = None
    PORTS = None
    POE_PORTS = None
    POE_MAX_POWER_ALL_PORTS = None
    POE_MAX_POWER_SINGLE_PORT = None
    POE_SCHEDULING = False
    CHECKS_AND_RESULTS = []

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


class GS3xxSeries(AutodetectedSwitchModel):
    pass


class GS305EP(GS3xxSeries):
    MODEL_NAME = "GS305EP"
    PORTS = 5
    POE_PORTS = [1, 2, 3, 4]
    POE_MAX_POWER_ALL_PORTS = 63
    CHECKS_AND_RESULTS = [
        ("check_login_form_rand", [True]),
        ("check_login_title_tag", ["GS305EP"]),
    ]
    DASHBOARD_CGI_URL_TMPL = "http://{ip}/dashboard.cgi"


class GS308EP(GS3xxSeries):
    MODEL_NAME = "GS308EP"
    PORTS = 8
    POE_PORTS = [1, 2, 3, 4, 5, 6, 7, 8]
    POE_MAX_POWER_ALL_PORTS = 62
    CHECKS_AND_RESULTS = [
        ("check_login_form_rand", [True]),
        ("check_login_title_tag", ["GS308EP"]),
    ]
    DASHBOARD_CGI_URL_TMPL = "http://{ip}/dashboard.cgi"


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