#!/usr/bin/env python3
# Python script om P1 telegram weer te geven

import datetime
import sys
import signal
from json import dumps
import re
import serial
import paho.mqtt.client as paho
import ssl
import yaml
import certifi

with open("config.yaml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

mqttc=paho.Client(cfg['mqtt']['client_id']) #create client object

mqttc.username_pw_set(cfg['mqtt']['user'],cfg['mqtt']['password'])
if(cfg['mqtt']['tls_enabled']):
        mqttc.tls_set(cfg['mqtt'])
        mqttc.tls_insecure_set(cfg['mqtt'])

mqttc.connect(cfg['mqtt']['broker'],cfg['mqtt']['port'],60) #establish connection

# Seriele poort confguratie
ser = serial.Serial()

# DSMR 4.0/4.2 > 115200 8N1:
ser.baudrate = cfg['serial']['baudrate']
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE

ser.xonxoff = 0
ser.rtscts = 0
ser.timeout = 12
ser.port = cfg['serial']['port']
ser.close()

dsmr_version = "" # Version information for P1 output
dsmr_eid = "" # Equipment identifier
dsmr_dt1 = 0 # Meter reading electricity delivered to client (tariff 1) in 0,001kWh
dsmr_dt2 = 0 # Meter reading electricity delivered to client (tariff 2) in 0,001kWh
dsmr_ct = 0 # Tariiff indicator
dsmr_apd = 0 # Actual power delivered in 1Wat resolution
dsmr_npf = 0 # Number of power failures in any phas
dsmr_nlpf = 0 # Number of long power failures in any phase
dsmr_pfel = "" # Power failure event log (long power failures)
dsmr_nvdp1 = 0 # Number of voltage dips in phase L1
dsmr_nvdp2 = 0 # Number of voltage dips in phase L2
dsmr_nvdp3 = 0 # Number of voltage dips in phase L3
dsmr_nvsp1 = 0 # Number of voltage swells in phase L1
dsmr_nvsp2 = 0 # Number of voltage swells in phase L2
dsmr_nvsp3 = 0 # Number of voltage swells in phase L3
dsmr_tmsg = "" # Text messages max 1024 characters

def log(msg, level="WARN"):
        ts = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S")
        print(f"{ts} [{level}] {msg}")

def signal_handler(sig, frame):
        # exit immediately upon receiving a second SIGINT
        global is_exiting

        if is_exiting:
                os._exit(1)

        is_exiting = True
        exit_gracefully(0)

def exit_gracefully(rc, skip_mqtt=False):
        global topics, mqttc

        log("Exiting app...")

        if mqttc is not None and mqttc.is_connected() and skip_mqtt == False:
                mqtt_publish(topics["status"], "offline", exit_on_error=False)
                mqttc.disconnect()

        # Use os._exit instead of sys.exit to ensure an MQTT disconnect event causes the program to exit correctly as they
        # occur on a separate thread
        os._exit(rc)

def on_mqtt_disconnect(client, userdata, rc):
        if rc != 0:
                log(f"Unexpected MQTT disconnection", level="ERROR")
                exit_gracefully(rc, skip_mqtt=True)

def mqtt_publish(topic, mqtt_msg, exit_on_error=True, json=False):
        global mqttc

        msg = mqttc.publish(
                cfg['mqtt']['topic_prefix'], payload=(dumps(mqtt_msg) if json else mqtt_msg), qos=cfg['mqtt']['qos'], retain=cfg['mqtt']['retain']
        )

        if msg.rc == paho.MQTT_ERR_SUCCESS:
                msg.wait_for_publish()
                return

        log(f"Error publishing MQTT message: {paho.error_string(msg.rc)}", level="ERROR")

        if exit_on_error:
                exit_gracefully(msg.rc, skip_mqtt=True)

while True:
        try:
                ser.open()
        except SerialError as SE:
                log(f"Error making serial connection", level="ERROR")
                exit_gracefully(ser.ri)

        checksum_found = False
        # gasflag = 0

        while not checksum_found:
                telegram_line = ser.readline() # Lees een seriele lijn in.
                telegram_line = bytes(telegram_line.decode('ascii').strip(), 'utf-8') # Strip spaties en blanke regels

                # print (telegram_line) #debug

                if re.match(b'(?=1-3:0.2.8)', telegram_line): # dsmr_version
                        # 1-3:0.2.8(42)
                        dsmr_version = telegram_line[10:-1].decode()
                if re.match(b'(?=0-0:96.1.1)', telegram_line): # dsmr_eid
                        # 0-0:96.1.1(4530303238303030303032323239363136)
                        dsmr_eid = telegram_line[11:-1].decode()
                if re.match(b'(?=1-0:1.8.1)', telegram_line): # dsmr_dt1
                        dsmr_dt1 = float(telegram_line[10:-5])
                if re.match(b'(?=1-0:1.8.2)', telegram_line): # dsmr_dt2
                        dsmr_dt2 = float(telegram_line[10:-5])
                if re.match(b'(?=0-0:96.14.0)', telegram_line): # dsmr_ct
                        # 0-0:96.14.0(0002)
                        dsmr_ct = int(telegram_line[12:-1])
                if re.match(b'(?=1-0:1.7.0)', telegram_line): # dsmr_apd
                        # 1-0:1.7.0(0000.54*kW)
                        kw = telegram_line[10:-4].decode() # Knip het kW gedeelte eruit (0000.54)
                        dsmr_apd = float(kw) * 1000 # vermengvuldig met 1000 voor conversie naar Watt (540.0)
                        dsmr_apd = int(dsmr_apd) # rond float af naar heel getal (540)
                if re.match(b'(?=0-0:96.7.21)', telegram_line): # dsmr_npf
                        dsmr_npf = int(telegram_line[13:17].decode())
                if re.match(b'(?=0-0:96.7.9)', telegram_line): # dsmr_nlpf
                        dsmr_nlpf = int(telegram_line[12:16].decode())
                if re.match(b'(?=1-0:99.97.0)', telegram_line): # dsmr_pfel
                        dsmr_pfel = "" # Dit nog een keer uitzoeken
                if re.match(b'(?=1-0:32.32.0)', telegram_line): # dsmr_nvdp1
                        dsmr_nvdp1 = int(telegram_line[13:17].decode())
                if re.match(b'(?=1-0:52.32.0)', telegram_line): # dsmr_nvdp2
                        dsmr_nvdp2 = int(telegram_line[13:17].decode())
                if re.match(b'(?=1-0:72.32.0)', telegram_line): # dsmr_nvdp3
                        dsmr_nvdp3 = int(telegram_line[13:17].decode())
                if re.match(b'(?=1-0:32.36.0)', telegram_line): # dsmr_nvsp1
                        dsmr_nvsp1 = int(telegram_line[13:17].decode())
                if re.match(b'(?=1-0:52.36.0)', telegram_line): # dsmr_nvsp2
                        dsmr_nvsp2 = int(telegram_line[13:17].decode())
                if re.match(b'(?=1-0:72.36.0)', telegram_line): # dsmr_nvsp3
                        dsmr_nvsp3 = int(telegram_line[13:17].decode())

                # Check wanneer het uitroepteken ontvangen wordt (einde telegram)
                if re.match(b'(?=!)', telegram_line):
                        checksum_found = True

        ser.close()

######################################
# MQTT PUBLISH
######################################

        mqtt_msg = dumps({
                "version": dsmr_version,
                "equipment_id": dsmr_eid,
                "delivered_tariff1": dsmr_dt1,
                "delivered_tariff2": dsmr_dt2,
                "current_tariff": dsmr_ct,
                "actual_power_delivery": dsmr_apd,
                "power_failures":dsmr_npf,
                "long_power_failures": dsmr_nlpf,
                "power_failure_log": dsmr_pfel,
                "voltage_dips_l1": dsmr_nvdp1,
                "voltage_dips_l2": dsmr_nvdp2,
                "voltage_dips_l3": dsmr_nvdp3,
                "voltage_swell_l1": dsmr_nvsp1,
                "voltage_swell_l2": dsmr_nvsp2,
                "voltage_swell_l3": dsmr_nvsp3,
                "tmsg": dsmr_tmsg })

        # mqttc.publish(mqtt_topic,mqtt_msg)
        mqtt_publish(cfg['mqtt']['topic_prefix'], mqtt_msg)
