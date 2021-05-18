# ckw-ha-gs108e
HomeAssistant Netgear Switch Integration

*configuration.yaml:*

```
sensor:
  - platform: ckw_hass_gs108e
    host: 192.168.178.34
    name: GS108Ev4 Buero

  - platform: ckw_hass_gs108e
    host: 192.168.178.35
    name: GS108Ev4 Werkstatt
```

Converting bytes/s to MB/s

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
