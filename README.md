# ckw-ha-gs108e
HomeAssistant Netgear Switch Integration

## What it does
Grabs statistical network data from your Netgear GS108Ev4

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
Edit your *configuration.yaml*, each *platform: ckw_hass_gs108e* section represents a Switch instance.

Configuration options:

- *host*: IP of Netgear Switch
- *name*: Name of Switch (your choice)
- *password*: Admin-Password for the Web UI (default: admin)

```
sensor:
  - platform: ckw_hass_gs108e
    host: 192.168.178.34
    name: GS108Ev4 Buero
    password: admin

  - platform: ckw_hass_gs108e
    host: 192.168.178.35
    name: GS108Ev4 Werkstatt
```

## Examples

### Converting bytes/s to MB/s

The Switch gives us bytes/s, if we want MB/s we have to create a template sensor in *configuration.yaml*:

```
sensor:
  ...
  - platform: template
    sensors:
      t_gs108ev3_buero_up_mb:
        friendly_name: "GS108Ev3 Büro Up"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_buero','transmission_rate_up') | float / 1000000 }}"

      t_gs108ev3_buero_down_mb:
        friendly_name: "GS108Ev3 Büro Down"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_buero','transmission_rate_down') | float / 1000000 }}"

      t_gs108ev3_werkstatt_up_mb:
        friendly_name: "GS108Ev3 Werkstatt Up"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_werkstatt','transmission_rate_up') | float / 1000000 }}"

      t_gs108ev3_werkstatt_down_mb:
        friendly_name: "GS108Ev3 Werkstatt Down"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_werkstatt','transmission_rate_down') | float / 1000000 }}"

      t_gs108ev3_scheune_up_mb:
        friendly_name: "GS108Ev3 Scheune Up"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_scheune','transmission_rate_up') | float / 1000000 }}"

      t_gs108ev3_scheune_down_mb:
        friendly_name: "GS108Ev3 Scheune Down"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_scheune','transmission_rate_down') | float / 1000000 }}"
      ...   
      # Ports:  
      ...    
      t_gs108ev3_werkstatt_down_p1_mb:
        friendly_name: "Port 1"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_werkstatt','ports_1_speed_rx_bytes') | float / 1000000 }}"

      t_gs108ev3_werkstatt_down_p2_mb:
        friendly_name: "Port 2"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_werkstatt','ports_2_speed_rx_bytes') | float / 1000000 }}"

      t_gs108ev3_werkstatt_down_p3_mb:
        friendly_name: "Port 3"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_werkstatt','ports_3_speed_rx_bytes') | float / 1000000 }}"

      t_gs108ev3_werkstatt_down_p4_mb:
        friendly_name: "Port 4"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_werkstatt','ports_4_speed_rx_bytes') | float / 1000000 }}"

      t_gs108ev3_werkstatt_down_p5_mb:
        friendly_name: "Port 5"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_werkstatt','ports_5_speed_rx_bytes') | float / 1000000 }}"

      t_gs108ev3_werkstatt_down_p6_mb:
        friendly_name: "Port 6"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_werkstatt','ports_6_speed_rx_bytes') | float / 1000000 }}"

      t_gs108ev3_werkstatt_down_p7_mb:
        friendly_name: "Port 7"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_werkstatt','ports_7_speed_rx_bytes') | float / 1000000 }}"

      t_gs108ev3_werkstatt_down_p8_mb:
        friendly_name: "Port 8"
        unit_of_measurement: 'MB/s'
        value_template: "{{ state_attr('sensor.gs108ev4_werkstatt','ports_8_speed_rx_bytes') | float / 1000000 }}"
  ...
```

![image](https://user-images.githubusercontent.com/4140156/118571964-9ac0fa80-b77f-11eb-951e-a5e393157bd0.png)
