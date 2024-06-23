# ckw-ha-gs108e
HomeAssistant Netgear Switch Integration

## What it does
Grabs statistical network data from your Netgear GS108Ev3

## How it works
1. Detecting Switch Model/Product in login.cgi
2. Connects to the Switch and asks for a cookie (`http://IP_OF_SWITCH/login.cgi`)
3. HTTP-Request send to the Switch twice (`http://IP_OF_SWITCH/portStatistics.cgi`) and compared with previous data ("in response time)

## Which entities
- overall Switch statistics as attributes
  - Diagnostic Sensor: `switch_ip` - IP of the Switch
  - Diagnostic Sensor: `response_time_s` - Response time of two requests send to the Switch to calculate the traffic speed
  - ...
- statistics for each Port (8 Ports for GS108Ev3) as attributes
  - `port_{port}_receiving` - receiving traffic on {port} in MB/s
  - `port_{port}_total_received` - total received traffic on {port} in MB
  - `port_{port}_total_transferred` - total transferred traffic on {port} in MB
  - ...
- status for each port
  - Binary Sensor: `port_{port}_status` - port cable connected/disconnected
  - Sensor: `port_{port}_connection_speed` - port transmission speed (100M/1000M)

### List of port sensors

| Sensor Name                      | Platform      | mapped key from `get_switch_infos()`    | Unit                                 |
|----------------------------------|---------------|-----------------------------------------|--------------------------------------|
| Port {port} Traffic Received     | SENSOR        | `port_{port}_traffic_rx_mbytes`         | MB (in response time)                |
| Port {port} Traffic Transferred  | SENSOR        | `port_{port}_traffic_tx_mbytes`         | MB (in response time)                |
| Port {port} Receiving            | SENSOR        | `port_{port}_speed_rx_mbytes`           | MB/s                                 |
| Port {port} Transferring         | SENSOR        | `port_{port}_speed_tx_mbytes`           | MB/s                                 |
| Port {port} IO                   | SENSOR        | `port_{port}_speed_io_mbytes`           | MB/s                                 |
| Port {port} Total Received       | SENSOR        | `port_{port}_sum_rx_mbytes`             | MB (since last switch reboot/reset)  |
| Port {port} Total Transferred    | SENSOR        | `port_{port}_sum_tx_mbytes`             | MB (since last switch reboot/reset)  |
| Port {port} Connection Speed     | SENSOR        | `port_{port}_connection_speed`          | MB/s                                 |
| Port {port} Status               | BINARY_SENSOR | `port_{port}_status`                    | "on"/"off"                           |

### List of aggregated sensors

| Sensor Name                      | Platform      | mapped key from `get_switch_infos()`    | Unit                                 |
|----------------------------------|---------------|-----------------------------------------|--------------------------------------|
| Switch IO                        | SENSOR        | `sum_port_speed_bps_io`                 | MB/s                                 |
| Switch Traffic Received          | SENSOR        | `sum_port_traffic_rx`                   | MB (in response time)                |
| Switch Traffic Transferred       | SENSOR        | `sum_port_traffic_tx`                   | MB (in response time)                |


## How to integrate in your HomeAssistant

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ckarrie&repository=ckw-ha-gs108e&category=integration)

1. Goto [HACS > Integrations](http://homeassistant.lan/redirect/hacs/integrations)
2. Click on the right corner on the vertical dots and select "Custom Repositories"
3. Add "https://github.com/ckarrie/ckw-ha-gs108e" as Integration

After adding the integration go to [Add Integration](https://my.home-assistant.io/redirect/integrations/) and select **Netgear GS108e Integration**.


![image](https://user-images.githubusercontent.com/4140156/118571964-9ac0fa80-b77f-11eb-951e-a5e393157bd0.png)


## Supported and tested Netgear Models/Products and firmwares

| Model    | Ports    | Firmwares                                    | Bootloader          |
|----------|----------|----------------------------------------------|---------------------|
| GS105E   | 5        | ?                                            |                     |
| GS108E   | 8        | V1.00.11                                     | V1.00.03            |
| GS105Ev3 | 5        | ?                                            |                     |
| GS108Ev3 | 8        | V2.00.05, V2.06.10, V2.06.17, V2.06.24       | V2.06.02, V2.06.03  |

Supported firmware languages: GR (German), EN (English)

## ToDo
- move integrated gs108e module into a seperate Python library (get rid of gs108e wording)
- add GS308x support
  - PoE ports status
  - turn on/off PoE ports

## API Level

### create a python venv with `requests` and `lxml`

```shell
python3 -m venv test-netgear
cd test-netgear
source bin/activate
pip install lxml requests
```

Using this VENV go to your local source folder

### Example calls

```shell
cd ~/workspace/src/ckw-ha-gs108e/custom_components/ckw_hass_gs108e
python3
```

```python
ip = '192.168.178.68'
p = 'fyce4gKZemkqjDY'
import gs108e
sw = gs108e.NetgearSwitchConnector(ip, p)
sw.autodetect_model()
sw.get_login_cookie()

data = sw.get_switch_infos()
print(sw.switch_model.MODEL_NAME)
print(data["port_1_sum_rx_mbytes"])
print(data)
```



