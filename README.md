# dsmr2mqtt
Python library for parsing Dutch Smart Meter (DSMR) to MQTT

1. Configure using config.yaml
2. Enable service:
  * cd /etc/systemd/
  * sudo ln -s /opt/dsmr2mqtt/dsmr2mqtt.service
  * sudo systemctl enable dsmr2mqtt
3. Start service:
  * sudo systemctl start dsmr2mqtt
