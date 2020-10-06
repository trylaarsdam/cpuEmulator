#!/usr/bin/env python
import glob
import sys
import os
import configparser
import serial

from clint.textui import prompt, puts, colored, validators

config = configparser.ConfigParser()
config.read('./config.ini')

ports = glob.glob('/dev/cu.us*')

chosenPort = 1
if (len(ports) > 1):
    chosenPort = prompt.options("Choose the correct port", ports)

print (ports[chosenPort-1])
ser = serial.Serial(ports[chosenPort-1])
uuid = config['USER CONFIG']['uuid']
ser.write(uuid.encode())
print ("UUID: {} sent to photon successfully on {}".format(uuid, ports[chosenPort-1]))