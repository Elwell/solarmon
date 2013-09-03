#!/usr/bin/python

# script to poll growatt PV inverter and spit out values
# Andrew Elwell <Andrew.Elwell@gmail.com> 2013-09-01

from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import time
import sys

start = int(sys.argv[1])
count = int(sys.argv[2])

client = ModbusClient(method='rtu', port='/dev/ttyUSB0', baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
client.connect()

rr = client.read_input_registers(start,count)
print rr.registers
client.close()
