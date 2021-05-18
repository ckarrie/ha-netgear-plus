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

Converting to MB/s

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
```

![image](https://user-images.githubusercontent.com/4140156/118571964-9ac0fa80-b77f-11eb-951e-a5e393157bd0.png)
