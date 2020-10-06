#!/usr/bin/env python
import csv
import pprint
import re
import enum
import json
import sys
import socket
import argparse
import configparser
import platform

config = configparser.ConfigParser()

params = {}
codes = {}
controlMap = {}
ram = bytearray()

if(platform.system() == 'Windows'):
    config.read('./microassembler/config.ini')
    if (len(config.sections()) == 0):
        config['USER CONFIG'] = { 'server' : "cpu.thewcl.com", 'port' : '12000', 'uuid' : '113DA078-56E6-4A4E-A355-BCB6F9C391F2' }
        with open('./microassembler/config.ini', 'w') as configfile:
            config.write(configfile)
elif(platform.system() == 'Darwin'):
    config.read('../../../microassembler/config.ini')
    if (len(config.sections()) == 0):
        config['USER CONFIG'] = { 'server' : "cpu.thewcl.com", 'port' : '12000', 'uuid' : '113DA078-56E6-4A4E-A355-BCB6F9C391F2' }
        with open('../../../microassembler/config.ini', 'w') as configfile:
            config.write(configfile)
else:
    config.read('./config.ini')
    if (len(config.sections()) == 0):
        config['USER CONFIG'] = { 'server' : "cpu.thewcl.com", 'port' : '12000', 'uuid' : '113DA078-56E6-4A4E-A355-BCB6F9C391F2' }
        with open('./microassembler/config.ini', 'w') as configfile:
            config.write(configfile)

parser = argparse.ArgumentParser(
    description="CPU Assembler"
#    epilog="Enjoy!"      
)
parser.add_argument("-n", action="store", dest="name", nargs="?", default="CPU", help="CPU name")
parser.add_argument("-c", action="store", dest="controlMap", nargs="?", default="../controlmap.json", help="Control signals for components config file")
parser.add_argument("-o", action="store", dest="opcodes", nargs="?", default="../opcodes.json", help="point to your opcodes.json file")
parser.add_argument("-s", action="store", dest="server", nargs="?", default="cpu.thewcl.com", help="url to cloud server accepting assembled binary to send to your CPU")
parser.add_argument("-p", action="store", dest="port", nargs="?", default="12000", help="port server is listening on, default is 11000")
parser.add_argument("-u", action="store", dest="uuid", help="uuid of your project to keep unique from other users")
args, leftovers = parser.parse_known_args()

if args.uuid is not None:
    config['USER CONFIG']['uuid'] = args.uuid
if args.server is not None:
    config['USER CONFIG']['server'] = args.server
if args.port is not None:
    config['USER CONFIG']['port'] = args.port
if args.opcodes is not None:
    config['USER CONFIG']['opcodes'] = args.opcodes
if args.name is not None:
    config['USER CONFIG']['name'] = args.name
if args.name is not None:
   config['USER CONFIG']['controlMap'] = args.controlMap

with open(config['USER CONFIG']['opcodes'] ) as json_file:
    codes = json.load(json_file)
with open(config['USER CONFIG']['controlMap']) as json_file:
    controlMap = json.load(json_file)
#pprint.pprint(params)

def toggleKthBit(n, k): 
    return (n ^ (1 << (k))) & 0xff

def getComponent(value):
    loc = value.find("_")
    return value[0:loc]

def getControlLine(value):
    loc = value.find("_")
    return value[loc+1:]

def getInitialControlWord(component):
    if component == None:
        return 0
    ctrlWord = component["activePolarity"]
    ctrlWord = int(ctrlWord,2)  
    ctrlWord = ~ctrlWord   # all lines are now in the NOT active polarity
    return ctrlWord & 0xff

def initialAllControlWords(busSlots):
    ctrlWords = [0] * len(busSlots)
    for i in range(len(busSlots)):
        component = busSlots[i]
        if (component != None):
            keys = list(component.keys())
            componentUniqueName = keys[0]
            ctrlWords[i] = getInitialControlWord(component[componentUniqueName])
    return ctrlWords

def assertSignal(component, ctrlWord, signal):
    bitNumber = controlMap[component]["controlLinesBitPosition"][signal]
    ctrlWord = toggleKthBit(ctrlWord, bitNumber)
    return ctrlWord

def serialize(data):
    _data = {}
    for k in data:
        _data[k] = hex(data[k])
    return json.dumps(_data, indent=4)

def writeControlWords(data, busSlots):
    ram.append(len(data["microcode"]))  # number of time slots for this instruction
    for timeSlot in range(len(data["microcode"])): # we support of 16 timeslots 0-15
        ctrlWords = initialAllControlWords(busSlots)
        assertions = data["microcode"][timeSlot]
        for assertion in assertions:
            component = getComponent(assertion) # get component reference
            controlLineBitNumber = controlMap[component]["controlLinesBitPosition"][getControlLine(assertion)]
            busIndex = controlMap[component]["busPosition"]
            ctrlWords[busIndex] = toggleKthBit(ctrlWords[busIndex], controlLineBitNumber)
        for cw in ctrlWords:
            ram.append(cw)
# RAM Construction
# [MSB][LSB] - RAM COUNT
# [COMPONENT COUNT] 
# [OPCODE][TIMESLOT][BUSPOSITION][CONTROLWORD]

# for mnemonic in controlMap:
#     ctrlWord = controlMap[mnemonic]["activePolarity"]
#     ctrlWord = int(ctrlWord,2)
#    print(ctrlWord)

# print ("Components: ", end=" "),
# for key in controlMap:
#     print(key + " ", end=" "),
# print()
# ctrlWords = initialAllControlWords()

componentCount = 0
for (key, value) in controlMap.items():
    componentCount = max(componentCount, value["busPosition"])
componentCount = componentCount + 1
print(componentCount)
ram.append(componentCount)  # First byte after length is number of components
busSlots = [None] * componentCount
#print(busSlots)
for (key, value) in controlMap.items():
    busSlots[value["busPosition"]] = {key: value}
#print(busSlots)
for mnemonic in codes:
    for mode in codes[mnemonic]:
        if (mode != "description"):
            opcode = codes[mnemonic][mode]["opcode"]["value"]
            print('Opcode: {} {}'.format(mnemonic, opcode))
            ram.append(int(opcode[2:],16)) # skip 0x at start of string where ,16 means hex
            for flag in codes[mnemonic][mode]["opcode"]["flags"]:
                for i in range(0,4):
                    print('  Flags: ' + bin(i))
                    if flag["value"] == "XX": 
                        ram.append(i)
                        writeControlWords(flag, busSlots)
                    if (flag["value"] == "X0") and (i == 0 or i == 2): 
                        ram.append(i)
                        writeControlWords(flag, busSlots)
                    if (flag["value"] == "X1") and (i == 1 or i == 3): 
                        ram.append(i)
                        writeControlWords(flag, busSlots)
                    if (flag["value"] == "0X") and (i == 0 or i == 1): 
                        ram.append(i)
                        writeControlWords(flag, busSlots)
                    if (flag["value"] == "1X") and (i == 2 or i == 3): 
                        ram.append(i)
                        writeControlWords(flag, busSlots)

ramSize = len(ram)

if(platform.system() == "Windows"):
    f = open('./microassembler/microcode.o', 'wb')
elif(platform.system() == "Darwin"):
    f = open('../../../microassembler/microcode.o', 'wb')
else:
    f = open('./microassembler/microcode.o', 'wb')
f.write(bytes([ramSize.to_bytes(2, 'big')[0]]))
f.write(bytes([ramSize.to_bytes(2, 'big')[1]]))
f.write(ram)
f.close()

# What we send to the server is the following:
# 1. UUID
# 2. RAM Size
# 3. RAM Contents

# preamble = bytearray(config['USER CONFIG']['uuid'], 'utf-8')

# ram[0:0] = bytes([ramSize.to_bytes(2, 'big')[0]])
# ram[1:0] = bytes([ramSize.to_bytes(2, 'big')[1]])
# print(ram)
if 'uuid' in config['USER CONFIG'].keys():
    preamble = bytearray(config['USER CONFIG']['uuid'], 'utf-8')

    ram[0:0] = bytes([ramSize.to_bytes(2, 'big')[0]])
    ram[1:0] = bytes([ramSize.to_bytes(2, 'big')[1]])
    preamble.extend(ram)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print("attempting connect to %s:%s" % (config['USER CONFIG']["server"], config['USER CONFIG']["port"]))
        s.connect((config['USER CONFIG']["server"],int(config['USER CONFIG']['port'])))
        s.send(preamble)
    except Exception as e:
        puts(colored.red("Unable to connect to %s at port %s. Check that you have a good internet connection" % (config['USER CONFIG']["server"], config['USER CONFIG']["port"])))
    finally:
        s.close()
else:
    puts(colored.yellow("No UUID supplied, so no contact with server was attempted."))
