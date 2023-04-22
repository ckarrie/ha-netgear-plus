import requests
from lxml import html
from . import netgear_crypt


class NetgearSwitchModel:
    LOGIN_URL = 'http://{ip}/login.htm'
    PORTS = 0
    POE_SUPPORT = False
    AUTODETECT_FUNCS = []  # List of (function names, args, [return values to check])

    def __init__(self, host, password=None):
        self.host = host
        self.password = password

    def get_autodetect_funcs(self):
        return self.AUTODETECT_FUNCS


class LoginRequired(NetgearSwitchModel):
    def __init__(self, host, password):
        super(LoginRequired, self).__init__(host, password)
        self._login_url_response = None
        self._form_password = None

    def get_autodetect_funcs(self):
        funcs = super(LoginRequired, self).get_autodetect_funcs()
        funcs.append(('check_login_url', [200]))
        funcs.append(('check_login_form_rand', [200]))
        return funcs

    def check_login_url(self):
        url = self.LOGIN_URL.format(ip=self.host)
        resp = requests.get(url, allow_redirects=False)
        self._login_url_response = resp
        return resp.status_code

    def check_login_form_rand(self):
        tree = html.fromstring(self._login_url_response.content)
        input_rand_elems = tree.xpath('//input[@id="rand"]')
        print(input_rand_elems)
        user_password = self.password
        if input_rand_elems:
            input_rand = input_rand_elems[0].value
            merged = netgear_crypt.merge(user_password, input_rand)
            md5 = netgear_crypt.make_md5(merged)
            self._form_password = md5
            return True
        return False


class GS105E(LoginRequired):
    PORTS = 5
    LOGIN_URL = 'http://{ip}/login.htm'

    def get_autodetect_funcs(self):
        funcs = super(GS105E, self).get_autodetect_funcs()
        funcs.append(('check_login_form_rand', [True]))
        return funcs


class GS105Ev2(LoginRequired):
    PORTS = 5

    def get_autodetect_funcs(self):
        funcs = super(GS105Ev2, self).get_autodetect_funcs()
        funcs.append(('check_login_form_rand', [True]))
        return funcs


class GS108E(LoginRequired):
    PORTS = 8

    def get_autodetect_funcs(self):
        funcs = super(GS108E, self).get_autodetect_funcs()
        funcs.append(('check_login_form_rand', [True]))
        return funcs


class GS305EP(LoginRequired):
    PORTS = 5
    POE_SUPPORT = True
    LOGIN_URL = 'http://{ip}/login.cgi'

    def get_autodetect_funcs(self):
        funcs = super(GS305EP, self).get_autodetect_funcs()
        funcs.append(('check_login_form_rand', [True]))
        return funcs


class GS308EP(LoginRequired):
    PORTS = 8
    POE_SUPPORT = True
    LOGIN_URL = 'http://{ip}/login.cgi'

    def get_autodetect_funcs(self):
        funcs = super(GS308EP, self).get_autodetect_funcs()
        funcs.append(('check_login_form_rand', [True]))
        return funcs

