# ckw-ha-gs108e
HomeAssistant Netgear Switch Integration

## What it does
Grabs statistical network data from your Netgear GS108Ev3

## How it works
1. Connects to the Switch and asks for a cookie (`http://IP_OF_SWITCH/login.cgi`)
2. ~~Stores the cookie in a local temp directory (`/tmp/.gs108ecookie192.168.178.34`)~~
3. HTTP-Request send to the Switch twice (`http://IP_OF_SWITCH/portStatistics.cgi`)

## Which statistics
- overall Switch statistics as attributes
  - `switch_ip` - IP of the Switch
  - `response_time_s` - Response time of two requests send to the Switch to calculate the traffic speed
  - `sum_port_traffic_rx` - Received traffic (sum all ports)
  - `sum_port_traffic_tx` - Transferred traffic (sum all ports)
  - `sum_port_traffic_crc_err` - CRC Errors (sum all ports)
  - `sum_port_speed_bps_rx` - Received traffic speed (bit/s)
  - `sum_port_speed_bps_rx` - Transferred traffic speed (bit/s)
  - `sum_port_speed_bps_io` - Received and transferred traffic speed 
  - `ports` - List of statistics for each Switch port
- statistics for each Port (8 Ports for GS108Ev4) as attributes
  - `port_nr`
  - `traffic_rx_bytes`
  - `traffic_tx_bytes`
  - `speed_rx_bytes`
  - `speed_tx_bytes`
  - `speed_io_bytes`
  - `crc_errors`


## How to integrate in your HomeAssistant
1. Goto [HACS > Integrations](http://homeassistant.lan/redirect/hacs/integrations)
2. Click on the right corner on the vertical dots and select "Custom Repositories"
3. Add "https://github.com/ckarrie/ckw-ha-gs108e" as Integration

After adding the integration go to [Add Integration](https://my.home-assistant.io/redirect/integrations/) and select *CKW GS108e Integration*.


![image](https://user-images.githubusercontent.com/4140156/118571964-9ac0fa80-b77f-11eb-951e-a5e393157bd0.png)
