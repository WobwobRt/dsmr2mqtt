**NOTE:** This repo is based on the work of Antonie Blom (https://github.com/antonijn/mqtt4dsmr). As the work continues, I'll update the relevant documentation.</Warning>

# DSMR Smart Meter MQTT Client

Lightweight containerized Dutch Smart Meter (_Slimme Meter_) to MQTT
daemon, with automatic Home Assistant integration.

Uses [paho-mqtt](https://pypi.org/project/paho-mqtt/) and
[ndokter/dsmr_parser](https://github.com/ndokter/dsmr_parser) to do the
heavy lifting.

![Automatic Home Assistant Discovery Demo](./sensor.png)

## Usage

### Docker compose
If you have little experience with containers and/or are running on
Raspberry Pi OS, this is the recommended method.

Example `compose.yaml`:

```yaml
version: "3"

services:
  dsmr2mqtt:
    image: wobwobrt/dsmr2mqtt:latest
    environment:
      MQTT_HOST: "mqtt.home.example.org"
      MQTT_PORT: "1883"
      MQTT_CLIENT_ID: "dsmr2mqtt"
      MQTT_USERNAME: "my_user"
      MQTT_PASSWORD: "my_password"
    devices:
      - "/dev/serial/by-id/usb-MY_DEVICE:/dev/ttyDSMR"
    restart: always
```

Use additional environment variables as required, per the documentation
below.

Run `docker compose up -d` to start the application. There are multiple
ways to enable docker compose at system start-up. One method is to place
the above configuration in `/etc/docker/compose/mqtt4dsmr/docker-compose.yml`,
and follow [this guide](https://gist.github.com/mosquito/b23e1c1e5723a7fd9e6568e5cf91180f/18a4efee062cda1a5b6807e440f891fd6bfb4f78).
Running `systemctl enable --now docker-compose@mqtt4dsmr` should then
do the trick.

Use additional environment variables as required, per the documentation
below.

Enable the container using `systemctl --user start mqtt4dsmr`. To
automatically start the daemon at system start-up while using rootless
containers, enable lingering for your user: `loginctl enable-linger <my-user>`.

## Options
Options must be given to the container as environment variables.
| Option | Description | Default |
|--------|-------------|---------|
| `MQTT_HOST` | IP address or URL for MQTT broker. | |
| `MQTT_PORT` | Broker MQTT port. If set to 8883 and `MQTT_TLS` is not explicitly defined, then `MQTT_TLS` defaults to `true`. (Optional) | 1883 |
| `MQTT_CLIENT_ID` | Client ID as communicated with thte broker. | dsmr2mqtt |
| `MQTT_USERNAME` | MQTT username. (Optional) | |
| `MQTT_PASSWORD` | MQTT password. (Optional if `MQTT_USERNAME` is not set) | | 
| `MQTT_TLS` | Use MQTT over TLS. If set to `true` and `MQTT_PORT` is not explicitly defined, then `MQTT_PORT` defaults to 8883. (Optional) | `false` |
| `MQTT_TLS_INSECURE` | Disable hostname verification for MQTT over TLS. (Optional) | `false` |
| `MQTT_CA_CERTS` | CA bundle file for broker verification. Only relevant for MQTT over TLS. (Optional) | |
| `MQTT_CERTFILE` | Client certificate for authentication. (Optional) | |
| `MQTT_KEYFILE` | Client keyfile for authentication. (Optional) | |
| `MQTT_TOPIC_PREFIX` | Topic prefix for application MQTT traffic. You should probably not change the default values unless you know it will conflict. (Optional) | `dsmr` |
| `HA_DEVICE_ID` | Home Assistant internal device ID. You should probably not change the default values unless you know it will conflict. This setting can be made empty to disable Home Assistant discovery. (Optional) | `dsmr` |
| `HA_DISCOVERY_PREFIX` | Home Assistant discovery prefix. This should match the value you have configured in your Home Assistant MQTT integration.  If you have not configured such a value, then don't change this option. (Optional) | `homeassistant` |
| `DSMR_VERSION` | Dutch Smart Meter Specification version. Can be one of `AUSTRIA_ENERGIENETZE_STEIERMARK`, `BELGIUM_FLUVIUS`, `EON_HUNGARY`, `ISKRA_IE`, `LUXEMBOURG_SMARTY`, `Q3D`, `SAGEMCOM_T210_D_R`, `SWEDEN`, `V2_2`, `V3`, `V4`, `V5`. See [ndokter/dsmr_parser](https://github.com/ndokter/dsmr_parser) for more information. (Optional) | `V4` |
| `SERIAL_SETTINGS` | Serial settings. Is probably related to your `DSMR_VERSION` setting. Worth playing around with if things don't work initially. Can be one of `V2_2`, `V4`, `V5`. See [ndokter/dsmr_parser](https://github.com/ndokter/dsmr_parser) for more information. (Optional) | `V4` | 
| `SERIAL_DEVICE` | Path to serial device file.<br><br>**NOTE:** This option is for testing purposes only. When running in a container, `SERIAL_DEVICE` always has the value `/dev/ttyDSMR` and cannot be overridden. Make sure to map the host device accordingly. |  |
| `MESSAGE_INTERVAL` | Minimum average interval between messages in seconds. Set to positive value to enable rate limiting. (Optional) | 0 |
| `LOG_LEVEL` | Logging level. Must be `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`. (Optional) | `INFO` | 
| `DSMR_INTERFACE` | Interface for smart meter communication. Must be one of `serial` or `tcp`. (Optional) | `serial` | 
| `DSMR_TCP_HOST` | Host to connect to the TCP stream of your smart meter. Required if `DSMR_INTERFACE` is set to `tcp`. | |
| `DSMR_TCP_PORT` | Port to connect to the TCP stream of your smart meter. (Optional) | `23` |

## Hardware support
Automated builds are available for AMD64, ARM64 and ARMv7. This means
dsmr2mqtt should run on any x86-based personal computer, all
second generation (or newer) Raspberry Pis and all second generation
(or newer) Raspberry Pi Zeros.

First generation Raspberry Pis are not supported at the moment, since
ARMv6 builds are currently not possible. This is because recent versions
of the `cryptography` package (required by `dlms-cosem`, in turn
required by `dsmr-parser`) are
[broken on ARMv6](https://github.com/antonijn/mqtt4dsmr/issues/2#issuecomment-1937367419).
