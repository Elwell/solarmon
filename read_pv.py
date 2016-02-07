#!/usr/bin/env python
# -*- coding: utf-8 -*-

 # new improved version that should run in background and poll / post on timer loop rather than one-off via cron

import time
import ConfigParser
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import requests
import paho.mqtt.client as mqtt

errcodes = {24: 'Auto Test Failed', 25:'No AC Connection', 26: 'PV Isolation Low', 27:'Residual Current High',
		28:'DC Current High', 29: 'PV Voltage High', 30: 'AV V Outrange', 31: 'AC Freq Outrange', 32: 'Module Hot'}
# errcodes 1-23 are 'Error: (errorcode+99)


# read settings from config file
config = ConfigParser.ConfigParser()
config.read('/boot/pvoutput.txt')
SYSTEMID = config.get('pvoutput','SYSTEMID')
APIKEY = config.get('pvoutput','APIKEY')
port = config.get('connection','Inverter')

t_date = format(time.strftime('%Y%m%d'))
t_time = format(time.strftime('%H:%M'))

check = time.time()
interval = 300
com_str='None'


# connect to MQTT Broker
mqttc = mqtt.Client()
mqttc.connect(config.get('mqtt','broker'))
topic = config.get('mqtt','topic')
mqttc.loop_start()

# default state at poweron will be 'waiting'
laststate = 1
statetxt = {0: "Waiting", 1: "Normal", 3: "Fault"}


def post_pvoutput():
    # we only attempt to upload to pvoutput if inverter online
    if invstate == 1:
        pv_headers = {'X-Pvoutput-Apikey': APIKEY, 'X-Pvoutput-SystemId':SYSTEMID }
        payload1 = {'d':t_date, 't':t_time, 'v1':(info['Etoday']*1000), 'v2':info['Pac'], 'v5':info['Tinverter'], 'v6':info['Vpv1'], 'c1':0, 'v7':info['Vac1'], 'v8':info['Fac'] }
        r = requests.post('http://pvoutput.org/service/r2/addstatus.jsp',headers=pv_headers,data=payload1)
        print r.content,payload1
    else:
        print "Not uploading to pvoutput - Inverter Status != Normal"

# Read data from inverter
# pdf says that we can't read more than 45 registers in one go.
inverter = ModbusClient(method='rtu', port=port, baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
inverter.connect()
while True:
  try:
    now = time.time()
    info = {} # we'll build this up with the parsed output from the registers
    rr = inverter.read_input_registers(0,33)
    #print rr.registers
    invstate=rr.registers[0]
    info['Status'] = statetxt[invstate]
    mqttc.publish(topic + '/status', statetxt[invstate])
    if (invstate != laststate):
        print "Changed state from %s to %s" % (laststate, invstate)
        pushover = {'token':config.get('pushover','app_token'), 'user':config.get('pushover','user_key'), 'title': 'Inverter debug', 'priority': -1,
		'message': "State changed from " + statetxt[laststate] + " to "+ statetxt[invstate], 'url':'http://pvoutput.org/intraday.jsp?sid=22888'}
        r = requests.post('https://api.pushover.net/1/messages.json',data=pushover)
        print r.content
        if invstate == 3:
            EC = inverter.read_input_registers(40,1)
            if 1 <= EC <= 23: # No specific text defined
                errstr = "Error Code " + str(99+EC)
            else:
                errstr = errcodes[EC.registers[0]]
            print "Inverter FAULT: %s" % errstr
            pushover = {'token':config.get('pushover','app_token'), 'user':config.get('pushover','user_key'), 'title': 'Inverter Fault', 'message': errstr }
            r = requests.post('https://api.pushover.net/1/messages.json',data=pushover)
            print r.content
        laststate = invstate

    info['Ppv'] = float((rr.registers[1]<<16) + rr.registers[2])/10 # Input Power

    info['Vpv1'] = float(rr.registers[3])/10 # PV1 Voltage
    info['PV1Curr'] = float(rr.registers[4])/10 # PV1 Input Current
    info['PV1Watt'] = float((rr.registers[5]<<16) + rr.registers[6])/10 # PV1 input watt

    # PV2 would be the same, but I only have one string connected
    #info['Vpv2'] = float(rr.registers[7])/10
    #info['PV2Curr'] = float(rr.registers[8])/10
    #info['PV2Watt'] = float((rr.registers[9]<<16) + rr.registers[10])/10

    # Total outputs for the inverter
    info['Pac'] = float((rr.registers[11]<<16) + rr.registers[12])/10 # Output Power
    info['Fac'] = float(rr.registers[13])/100 # Grid Frequency

    # Single phase users just see the 1st set of these
    info['Vac1'] = float(rr.registers[14])/10 # Single Phase (L1) grid voltage
    info['Iac1'] = float(rr.registers[15])/10 # Single Phase (L1) grid output current
    info['Pac1'] = float((rr.registers[16]<<16) + rr.registers[17])/10 # Single Phase (L1) grid output watt

    #info['Vac2'] = float(rr.registers[18])/10 # L2 grid voltage
    #info['Iac2'] = float(rr.registers[19])/10 # L2 grid output current
    #info['Pac2'] = float((rr.registers[20]<<16) + rr.registers[21])/10 # L2 grid output watt

    #info['Vac3'] = float(rr.registers[22])/10 # L3 grid voltage
    #info['Iac3'] = float(rr.registers[23])/10 # L3 grid output current
    #info['Pac3'] = float((rr.registers[24]<<16) + rr.registers[25])/10 # L3 grid output watt

    info['Etoday'] = float((rr.registers[26]<<16) + rr.registers[27])/10
    info['Etotal'] = float((rr.registers[28]<<16) + rr.registers[29])/10
    info['ttotal'] = float((rr.registers[30]<<16) + rr.registers[31])/2 # seconds
    info['Tinverter'] = float(rr.registers[32])/10  # Inverter temp

    #print info
    mqttc.publish(topic + '/raw', str(info))

    if (((now - check) % interval) < 2):
          post_pvoutput()
          check = now

  #except SerialException:
  except:
     print 'Serial Read Error?'
  time.sleep(1)




mqttc.loop_stop()
inverter.close()
