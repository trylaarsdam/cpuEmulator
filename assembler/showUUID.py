#!/usr/bin/env python
import glob
import sys
import os
import configparser
import serial

from clint.textui import prompt, puts, colored, validators

ports = glob.glob('/dev/cu.us*')

chosenPort = 1
if (len(ports) > 1):
    chosenPort = prompt.options("Choose the correct port", ports)

print (ports[chosenPort-1])

ser = serial.Serial(ports[chosenPort-1])
ser.write("?".encode())
result = ser.read(36)
print ("UUID: {} ".format(result))
