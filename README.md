# Home Assistant NETGEAR Plus Switches Integration

## Warning for users of version <= v0.6.1 installed through HACS

Due to the renaming of the integration and the repository, HACS gets confused and installs the new version next to the old one instead of replacing the old version. Please remove the old version first before installing the latest release.

## What it does

Grabs statistical network data from [supported NETGEAR Switches](#supported-and-tested-netgear-modelsproducts-and-firmwares) from the
[Plus Managed Network Switch](https://www.netgear.com/business/wired/switches/plus/) line. These switches can only be managed using a
Web interface and not through SNMP or cli. This integration uses web scraping to collect the switch configuration, statistics and
some basic configuration updates.

## How it works

1. Detecting Switch Model/Product in login.cgi
2. Connects to the Switch and asks for a cookie (`http://IP_OF_SWITCH/login.cgi`)
3. HTTP-Request send to the Switch twice (`http://IP_OF_SWITCH/portStatistics.cgi`) and compared with previous data ("in response time")

## Which entities

- overall Switch statistics as attributes
  - Diagnostic Sensor: `switch_ip` - IP of the Switch
  - Diagnostic Sensor: `response_time_s` - Response time of two requests send to the Switch to calculate the traffic speed
  - ...
- statistics for each Port (8 Ports for GS108Ev3) as attributes
  - `port_{port}_receiving` - receiving traffic on `{port}` in MB/s
  - `port_{port}_total_received` - total received traffic on `{port}` in MB
  - `port_{port}_total_transferred` - total transferred traffic on `{port}` in MB
  - ...
- status for each port
  - Binary Sensor: `port_{port}_status` - port cable connected/disconnected
  - Sensor: `port_{port}_connection_speed` - port transmission speed (100M/1000M)

### List of port sensors

| Sensor Name                     | Platform      | mapped key from `get_switch_infos()` | Unit                                |
| ------------------------------- | ------------- | ------------------------------------ | ----------------------------------- |
| Port {port} Traffic Received    | SENSOR        | `port_{port}_traffic_rx_mbytes`      | MB (in response time)               |
| Port {port} Traffic Transferred | SENSOR        | `port_{port}_traffic_tx_mbytes`      | MB (in response time)               |
| Port {port} Receiving           | SENSOR        | `port_{port}_speed_rx_mbytes`        | MB/s                                |
| Port {port} Transferring        | SENSOR        | `port_{port}_speed_tx_mbytes`        | MB/s                                |
| Port {port} IO                  | SENSOR        | `port_{port}_speed_io_mbytes`        | MB/s                                |
| Port {port} Total Received      | SENSOR        | `port_{port}_sum_rx_mbytes`          | MB (since last switch reboot/reset) |
| Port {port} Total Transferred   | SENSOR        | `port_{port}_sum_tx_mbytes`          | MB (since last switch reboot/reset) |
| Port {port} Connection Speed    | SENSOR        | `port_{port}_connection_speed`       | MB/s                                |
| Port {port} Status              | BINARY_SENSOR | `port_{port}_status`                 | "on"/"off"                          |
| Port {poe_port} POE Power       | SWITCH        | `port_{poe_port}_poe_power_active`   | "on"/"off"                          |

### List of aggregated sensors

| Sensor Name                | Platform | mapped key from `get_switch_infos()` | Unit                  |
| -------------------------- | -------- | ------------------------------------ | --------------------- |
| Switch IO                  | SENSOR   | `sum_port_speed_bps_io`              | MB/s                  |
| Switch Traffic Received    | SENSOR   | `sum_port_traffic_rx`                | MB (in response time) |
| Switch Traffic Transferred | SENSOR   | `sum_port_traffic_tx`                | MB (in response time) |

## Supported and tested NETGEAR Models/Products and firmware versions

| Model     | Ports | Firmware versions                      | Bootloader versions |
| --------- | ----- | -------------------------------------- | ------------------- |
| GS105E    | 5     | ?                                      |                     |
| GS105Ev2  | 5     | V1.6.0.15                              | V1.4.0.5-VB         |
| GS105PE   | 5     | V1.6.0.17                              | V1.6.0.2-VB         |
| GS108E    | 8     | V1.00.11                               | V1.00.03            |
| GS105Ev3  | 5     | ?                                      |                     |
| GS108Ev3  | 8     | V2.00.05, V2.06.10, V2.06.17, V2.06.24 | V2.06.01 - V2.06.03 |
| GS108Ev4  | 8     | V1.0.1.3                               |                     |
| GS108PEv3 | 8     | V2.06.24                               | V2.06.01            |
| GS110EMX  | 10    | V1.0.2.8                               |                     |
| GS116Ev2  | 16    | ?                                      | ?                   |
| GS305E    | 5     | V1.0.0.16                              | V1.0.0.2            |
| GS305EP   | 5     | V1.0.1.1                               |                     |
| GS305EPP  | 5     | V1.0.1.4                               |                     |
| GS308E    | 8     | V1.00.11                               | V1.00.03            |
| GS308EP   | 8     | V1.0.0.10, V1.0.1.4                    |                     |
| GS308EPP  | 8     | V1.0.1.4                               |                     |
| GS316EP   | 16    | V1.0.4.4                               |                     |
| GS316EPP  | 16    | V1.0.4.4                               |                     |
| JGS516PE  | 16    | V2.6.0.48                              |                     |
| JGS24Ev2  | 24    | V2.6.0.48                              |                     |
| XS512EM   | 12    | V1.0.2.8                               |                     |

Supported firmware languages: GR (German), EN (English)

## Unsupported models

| Model    | Support status                                                  |
| -------- | --------------------------------------------------------------- |
| JGS524PE | See [#93](https://github.com/ckarrie/ha-netgear-plus/issues/93) |
| MS108EUP | See [#91](https://github.com/ckarrie/ha-netgear-plus/issues/91) |

Do you have a NETGEAR Plus switch model that is currently not supported, open a [GitHub issue](https://github.com/ckarrie/ha-netgear-plus/issues/new?template=feature_request.yml). The actual API to the switch is implemented in the [py-netgear-plus](https://github.com/foxey/py-netgear-plus) library. Are you willing to contribute, please read the [instruction on adding your model](https://github.com/foxey/py-netgear-plus/blob/main/HOWTO_Add_New_Models.md) to this library and create a pull request for [py-netgear-plus](https://github.com/foxey/py-netgear-plus) first.

## How to integrate in Home Assistant

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ckarrie&repository=ha-netgear-plus&category=integration)

1. In your Home Assistant instance, goto **HACS** (Search: ">hacs")
2. Click on the right corner on the vertical dots and select "Custom Repositories"
3. Add "https://github.com/ckarrie/ha-netgear-plus" as Integration

After adding the integration go to [Add Integration](https://my.home-assistant.io/redirect/integrations/) and select **NETGEAR Plus**.

### Lovelace examples

Example with [ha-sankey-chart](https://github.com/MindFreeze/ha-sankey-chart)

![image](https://github.com/ckarrie/ckw-ha-gs108e/assets/4140156/9e8ca08f-bd64-4b49-8408-2135107c53f5)

Example with [mini-graph-card](https://github.com/kalkih/mini-graph-card)

![image](https://github.com/ckarrie/ckw-ha-gs108e/assets/4140156/9f390bab-6d3e-4e9c-83df-39bd230d7309)

```yaml
type: custom:mini-graph-card
entities:
  - entity: sensor.gs108ev3_192_168_178_8_port_1_io
    show_points: false
    name: QNAP
  - entity: sensor.gs108ev3_192_168_178_8_port_2_io
    show_points: false
    name: P2
  - entity: sensor.gs108ev3_192_168_178_8_port_3_io
    show_points: false
    name: rpi4-001
  - entity: sensor.gs108ev3_192_168_178_8_port_4_io
    show_points: false
    name: Telefon
  - entity: sensor.gs108ev3_192_168_178_8_port_5_io
    show_points: false
    name: Unraid
  - entity: sensor.gs108ev3_192_168_178_8_port_6_io
    show_points: false
    name: Drucker
  - entity: sensor.gs108ev3_192_168_178_8_port_7_io
    show_points: false
    name: Beelink (HA)
  - entity: sensor.gs108ev3_192_168_178_8_port_8_io
    show_points: false
    name: HomeOffice und WLAN
hours_to_show: 0.1
points_per_hour: 1000
name: 192.168.178.8 - GS108Ev3 Büro
line_width: 1
animate: true
```

## API Level

### Create a python virtual environment

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install py-netgear-plus
```

Using this VENV go to your local source folder

### Example calls

```shell
cd src
python3
```

```python
ip = '192.168.178.68' # replace with IP address of your switch
p = 'fyce4gKZemkqjDY' # replace with your password
import py_netgear_plus
sw = py_netgear_plus.NetgearSwitchConnector(ip, p)
sw.autodetect_model()
sw.get_login_cookie()

data = sw.get_switch_infos()
print(sw.switch_model.MODEL_NAME)
print(data["port_1_sum_rx_mbytes"])
print(data)
sw.turn_off_poe_port(1) # Supported only on PoE capable models
sw.turn_on_poe_port(1)
```
