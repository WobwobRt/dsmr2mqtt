# dsmr2mqtt
Python library for parsing Dutch Smart Meter (DSMR) to MQTT

Installation:
1. Copy config.yaml, dsmr2mqtt.py and dsmr2mqtt.service to /opt/dsmr2mqtt
2. Configure using config.yaml
3. Enable service:
  * cd /etc/systemd/
  * sudo ln -s /opt/dsmr2mqtt/dsmr2mqtt.service
  * sudo systemctl enable dsmr2mqtt
4. Start service:
  * sudo systemctl start dsmr2mqtt
5. Victory!
