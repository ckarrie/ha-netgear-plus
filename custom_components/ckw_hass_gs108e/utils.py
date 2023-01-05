import time
import requests
from lxml import html

sleep_time = 0.25
cookies_by_switch = {}

# Get login cookie
# Parameters: (string) Switch IP, (strong) Switch Password
# Return: (string) Cookie name, (string) Cookie content
def get_login_cookie(switch_ip, switch_password):
    # Login through the web interface and retrieve a session key
    url = 'http://' + switch_ip + '/login.cgi'
    data = dict(password=switch_password)

    r = requests.post(url, data=data, allow_redirects=True)

    # Check that we have authenticated correctly. Cookie must be set
    cookie = r.cookies.get('GS108SID')
    if cookie is not None:
        return 'GS108SID', cookie

    cookie = r.cookies.get('SID')
    if cookie is not None:
        return 'SID', cookie

    # If we've got here, then authentication error or cannot find the auth cookie.
    return (None), (None)


# Check if cookie is valid
# Parameters: (string) Switch IP, (string) Cookie name, (string) Cookie contents
# Return: True or False
def check_login_cookie_valid(switch_ip, cookie_name, cookie_content):
    # Checks that our login cookie is indeed valid. We check the port stats page, if that page loads correctly, (y).
    # Return: bool
    url = 'http://' + switch_ip + '/portStatistics.cgi'
    jar = requests.cookies.RequestsCookieJar()
    jar.set(cookie_name, cookie_content, domain=switch_ip, path='/')
    r = requests.post(url, cookies=jar, allow_redirects=False)
    tree = html.fromstring(r.content)
    title = tree.xpath('//title')
    if title[0].text != "Port Statistics":
        return False
    else:
        return True


def get_switch_infos(switch_ip, switch_password):
    switch_cookie_name = None
    switch_cookie_content = None
    login_cookie_valid = False
    cookie_by_switch = cookies_by_switch.get(switch_ip, None)
    if cookie_by_switch:
        switch_cookie_name = cookie_by_switch.get('name')
        switch_cookie_content = cookie_by_switch.get('content')
        login_cookie_valid = check_login_cookie_valid(switch_ip, switch_cookie_name, switch_cookie_content)

    if not login_cookie_valid:
        # Old Cookie / First run
        switch_cookie_name, switch_cookie_content = get_login_cookie(switch_ip, switch_password)
        cookies_by_switch[switch_ip] = {'name': switch_cookie_name, 'content': switch_cookie_content}

        if switch_cookie_name is None:
            print("Exiting, no switch_cookie_name", switch_cookie_name)
            exit(1)

    # Set up our cookie jar
    jar = requests.cookies.RequestsCookieJar()
    jar.set(switch_cookie_name, switch_cookie_content, domain=switch_ip, path='/')

    # Get the port stats page
    url = 'http://' + switch_ip + '/portStatistics.cgi'
    try:
        page = requests.get(url, cookies=jar, timeout=15.000)
    except requests.exceptions.Timeout:
        return None
    start_time = time.perf_counter()
    tree = html.fromstring(page.content)

    rx1 = tree.xpath('//tr[@class="portID"]/td[2]')
    tx1 = tree.xpath('//tr[@class="portID"]/td[3]')
    crc1 = tree.xpath('//tr[@class="portID"]/td[4]')

    # Hold fire
    time.sleep(sleep_time)

    # Get the port stats page again! We need to compare two points in time
    try:
        page = requests.get(url, cookies=jar, timeout=15.000)
    except requests.exceptions.Timeout:
        return None
    end_time = time.perf_counter()
    tree = html.fromstring(page.content)

    rx2 = tree.xpath('//tr[@class="portID"]/td[2]')
    tx2 = tree.xpath('//tr[@class="portID"]/td[3]')
    crc2 = tree.xpath('//tr[@class="portID"]/td[4]')

    sample_time = end_time - start_time
    sample_factor = 1 / sample_time

    # print("It took us " + str(sample_time) + " seconds.")
    ports = min([len(tx1), len(tx2)])

    # Test code, print all values.
    for i in range(0, len(tx2)):
        # Convert Hex to Int, get bytes traffic
        port_traffic = int(tx2[i].text, 10) - int(tx1[i].text, 10)
        port_speed_bps = port_traffic * sample_factor
        # print("Port " + str(i) + ": " + "{0:.2f}".format(port_speed_bps/1024, ) + "kb/s.", tx2[i].text, "-", tx1[i].text)

    ports_data = []

    # GS105Ev2
    # Values are already in Int

    sum_port_traffic_rx = 0
    sum_port_traffic_tx = 0
    sum_port_traffic_crc_err = 0
    sum_port_speed_bps_rx = 0
    sum_port_speed_bps_tx = 0

    for port_number in range(ports):
        try:
            port_traffic_rx = int(rx2[port_number].text, 10) - int(rx1[port_number].text, 10)
            port_traffic_tx = int(tx2[port_number].text, 10) - int(tx1[port_number].text, 10)
            port_traffic_crc_err = int(crc2[port_number].text, 10) - int(crc1[port_number].text, 10)
            port_speed_bps_rx = int(port_traffic_rx * sample_factor)
            port_speed_bps_tx = int(port_traffic_tx * sample_factor)
            port_name = "Port " + str(port_number)
        except IndexError:
            print("IndexError at port_number", port_number)
            continue

        # print(
        #    "Port", port_name,
        #    "Traffic In", port_speed_bps_rx,
        #    "Traffic Out", port_speed_bps_tx,
        #    "CRC Errors", port_traffic_crc_err
        # )

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

        ports_data.append({
            'port_nr': port_number + 1,
            'port_name': port_name,
            'traffic_rx_bytes': port_traffic_rx,
            'traffic_tx_bytes': port_traffic_tx,
            'speed_rx_bytes': port_speed_bps_rx,
            'speed_tx_bytes': port_speed_bps_tx,
            'speed_io_bytes': port_speed_bps_rx + port_speed_bps_tx,
            'crc_errors': port_traffic_crc_err,
        })

    return {
        'switch_ip': switch_ip,
        'response_time_s': sample_time,
        'ports': ports_data,
        'sum_port_traffic_rx': sum_port_traffic_rx,
        'sum_port_traffic_tx': sum_port_traffic_tx,
        'sum_port_traffic_crc_err': sum_port_traffic_crc_err,
        'sum_port_speed_bps_rx': sum_port_speed_bps_rx,
        'sum_port_speed_bps_tx': sum_port_speed_bps_tx,
        'sum_port_speed_bps_io': sum_port_speed_bps_rx + sum_port_speed_bps_tx,
    }

# if __name__ == "__main__":
#    switch_ip = '192.168.178.35'
#    switch_password = 'password'
#    port_number = 0
#    switch_infos = get_switch_infos(switch_ip=switch_ip, switch_password=switch_password)
#    pprint(switch_infos)
