# Installing MS108EUP Support for Home Assistant

This guide explains how to install the Netgear Plus integration with MS108EUP switch support.

## Supported Switch

**Netgear MS108EUP** - Multi-Gig 8-Port PoE++ Ultra60 Managed Switch

Features supported:
- Switch information (name, firmware, serial number, MAC address)
- Port status and connection speeds
- Port traffic statistics (RX/TX)
- PoE status per port (power draw, delivery status)
- PoE control (turn ports on/off)

## Installation Methods

### Method 1: Manual Installation (Recommended)

1. **Download the integration**

   Download the ZIP file from GitHub:
   ```
   https://github.com/ripple7511/ha-netgear-plus/archive/refs/heads/main.zip
   ```

2. **Extract and copy files**

   - Extract the ZIP file
   - Copy the `custom_components/netgear_plus` folder to your Home Assistant's `custom_components/` directory

   Your folder structure should look like:
   ```
   config/
   └── custom_components/
       └── netgear_plus/
           ├── __init__.py
           ├── config_flow.py
           ├── manifest.json
           ├── py_netgear_plus/
           │   ├── __init__.py
           │   ├── models.py
           │   ├── parsers.py
           │   └── ...
           └── ...
   ```

3. **Restart Home Assistant**

   Go to Settings > System > Restart

4. **Add the integration**

   - Go to Settings > Devices & Services
   - Click "+ Add Integration"
   - Search for "NETGEAR Plus"
   - Enter your switch's IP address and password

### Method 2: Git Clone

If you have SSH/terminal access to your Home Assistant:

```bash
cd /config/custom_components
git clone https://github.com/ripple7511/ha-netgear-plus.git temp_netgear
mv temp_netgear/custom_components/netgear_plus ./netgear_plus
rm -rf temp_netgear
```

Then restart Home Assistant.

## Configuration

When adding the integration, you'll need:

| Field | Description |
|-------|-------------|
| Host | IP address of your MS108EUP switch (e.g., `192.168.1.5`) |
| Password | The admin password for your switch |

## Troubleshooting

### "Maximum sessions reached" error

The MS108EUP has a limit on concurrent web sessions. To fix:
1. Log out of the switch's web interface in your browser
2. Or restart the switch to clear all sessions
3. Try adding the integration again

### Switch not detected

- Ensure the switch is on the same network (or VLAN) as Home Assistant
- Verify you can access the switch's web interface at `http://<switch-ip>/`
- Check that port 80 is not blocked by a firewall

### Connection timeout

- Verify the IP address is correct
- Ensure the switch is powered on and connected to the network

## Entities Created

For each MS108EUP switch, the integration creates:

- **Sensors**: Port status, connection speeds, traffic statistics, PoE power per port
- **Binary Sensors**: Port link status (connected/disconnected)
- **Switches**: PoE power control for each port (turn PoE on/off)
- **Buttons**: Refresh data

## Support

- Issues: https://github.com/ripple7511/ha-netgear-plus/issues
- Upstream project: https://github.com/ckarrie/ha-netgear-plus

## Credits

- Original ha-netgear-plus integration by [@ckarrie](https://github.com/ckarrie)
- Original py-netgear-plus library by [@foxey](https://github.com/foxey)
- MS108EUP support added by [@ripple7511](https://github.com/ripple7511)
