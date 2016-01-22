#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import ConfigParser
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pyowm import OWM
import requests

# read settings from config file
config = ConfigParser.ConfigParser()
config.read('/boot/pvoutput.txt')
SYSTEMID = config.get('pvoutput','SYSTEMID')
APIKEY = config.get('pvoutput','APIKEY')
OWMKey = config.get('weather','Key')
OWMLon = float(config.get('weather','Longitude'))
OWMLat = float(config.get('weather','Latitude'))
NoInvert = int(config.get('connection','Inverters'))

t_date = format(time.strftime('%Y%m%d'))
t_time = format(time.strftime('%H:%M'))

#pv_volts=0.0
#pv_power=0.0
#Wh_today=0
#current_temp=0.0
com_str='None'

for i in range(NoInvert):
# Read data from inverter
# pdf says that we can't read more than 45 registers in one go.
  inverter = ModbusClient(method='rtu', port='/dev/ttyUSB'+str(i), baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
  inverter.connect()
  rr = inverter.read_input_registers(0,45)
  inverter.close()
  print rr.registers
  invstate=rr.registers[0]
  if invstate == 0:
	print "Inverter State: Waiting - insufficent output"
  elif invstate == 3:
	print "Inverter State: FAULT"
  elif invstate == 1:
	print "Inverter State: Normal"
  else:
	print "WARNING: Unknown Inverter Status"

  Ppv = float((rr.registers[1]<<8) + rr.registers[2])/10 # Input Power
  print 'Ppv: %s W' % Ppv

  Vpv1 = float(rr.registers[3])/10 # PV1 Voltage
  PV1Curr = float(rr.registers[4])/10 # PV1 Input Current
  PV1Watt = float((rr.registers[5]<<8) + rr.registers[6])/10 # PV1 input watt

  print 'Vpv1: %s V' % Vpv1
  print 'PV1Curr: %s A' % PV1Curr
  print 'PV1Watt: %s W' % PV1Watt

  # PV2 would be the same, but I only have one string connected
  Vpv2 = float(rr.registers[7])/10
  PV2Curr = float(rr.registers[8])/10
  PV2Watt = float((rr.registers[9]<<8) + rr.registers[10])/10
  #print 'Vpv2: %s V' % Vpv2
  #print 'PV2Curr: %s A' % PV2Curr
  #print 'PV2Watt: %s W' % PV2Watt

  Pac = float((rr.registers[11]<<8) + rr.registers[12])/10 # Output Power
  Fac = float(rr.registers[13])/100 # Grid Frequency
  Vac1 = float(rr.registers[14])/10 # Single Phase grid voltage
  Iac1 = float(rr.registers[15])/10 # Single Phase grid output current
  Pac1 = float((rr.registers[16]<<8) + rr.registers[17])/10 # Single Phase grid output watt

  print 'Pac: %s W' % Pac
  print 'Fac: %s Hz' % Fac
  print 'Vac1: %s V' % Vac1
  print 'Iac1: %s A' % Iac1
  print 'Pac1: %s VA' % Pac1

  Etoday = float((rr.registers[26]<<8) + rr.registers[27])/10
  Etotal = float((rr.registers[28]<<8) + rr.registers[29])/10
  ttotal = float((rr.registers[30]<<8) + rr.registers[31])/2
  Tinverter = float(rr.registers[32])/10

  print "Etoday: %s KWh, Etotal: %s KWh, Total Time: %s s, Inverter Temp: %s C" % (Etoday,Etotal,ttotal,Tinverter)



if OWMKey<>'':
  owm = OWM(API_key=OWMKey)
  obs = owm.weather_at_coords(OWMLat, OWMLon)
  w = obs.get_weather()
  w_stat = w.get_detailed_status()
  temp = w.get_temperature(unit='celsius')
  current_temp = temp['temp']
  cloud_pct = w.get_clouds()
  com_str= ('%s with a cloud coverage of %s percent' %(w_stat,cloud_pct))

pv_headers = {'X-Pvoutput-Apikey': APIKEY, 'X-Pvoutput-SystemId':SYSTEMID }
payload1 = {'d':t_date, 't':t_time, 'v1':Etoday, 'v2':Pac, 'v5':Tinverter, 'v6':Vpv1, 'c1':0, 'v7':Vac1, 'v8':Fac }
print payload1
r = requests.post('http://pvoutput.org/service/r2/addstatus.jsp',headers=pv_headers,data=payload1)
print r.content

if Etoday>0:
  payload2 = {'d':t_date, 'g':Etoday, 'cm':com_str, 'cd':w_stat}
  r = requests.post('http://pvoutput.org/service/r2/addoutput.jsp',headers=pv_headers,data=payload2)
  print r.content
