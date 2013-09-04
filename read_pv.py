#!/usr/bin/python

# script to poll growatt PV inverter and spit out values
# Andrew Elwell <Andrew.Elwell@gmail.com> 2013-09-01

from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import time

result = {}
result['timestamp'] = time.time()

client = ModbusClient(method='rtu', port='/dev/ttyUSB0', baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
client.connect()

# can'r read the whole lot in one pass, so grab each chunk
# addr / descriptions  lifted from http://code.google.com/p/pvbeancounter/source/browse/trunk_v2/PVSettings/Device_Growatt.xml
rr = []
rr = client.read_input_registers(2,3)
result['PV_W'], result['PV_V'], result['PV_A'] = rr.registers

rr = []
rr = client.read_input_registers(12,3)
result['Out_W'], result['AC_Hz'], result['AC_V'] = rr.registers

#rr = client.read_input_registers(17, 1)
#result['wtf2'] = rr.registers[0]

#rr = client.read_input_registers(29,3)
#print rr.registers

client.close()

print result,
