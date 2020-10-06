#!/usr/bin/env python
import uuid
import csv
import pprint
import re
import enum
import json
import sys
import os
import socket
import serial
from pyfiglet import Figlet
import argparse
from clint.textui import puts, indent, colored, prompt
import configparser
import platform

print(str(sys.argv))

parser = argparse.ArgumentParser(
    description="CPU Assembler"
#    epilog="Enjoy!"      
)
parser.add_argument("file", help="file to assemble")
parser.add_argument("--development", help="running under development")
parser.add_argument("-n", action="store", dest="name", nargs="?", default="CPU", help="CPU name")
parser.add_argument("-c", action="store", dest="controlMap", nargs="?", default="./controlmap.json", help="Control signals for components config file")
if(platform.system() == "Windows"):
    parser.add_argument("-o", action="store", dest="opcodes", nargs="?", default="../opcodes.json", help="point to your opcodes.json file")
elif(platform.system() == "Darwin"):
    parser.add_argument("-o", action="store", dest="opcodes", nargs="?", default="../../../opcodes.json", help="point to your opcodes.json file")
else:
    parser.add_argument("-o", action="store", dest="opcodes", nargs="?", default="./opcodes.json", help="point to your opcodes.json file")
parser.add_argument("-s", action="store", dest="server", nargs="?", default="cpu.thewcl.com", help="url to cloud server accepting assembled binary to send to your CPU")
parser.add_argument("-p", action="store", dest="port", nargs="?", default="11000", help="port server is listening on, default is 11000")
parser.add_argument("-u", action="store", dest="uuid", help="uuid of your project to keep unique from other users")
#parser.add_argument("-wc", action="store", dest="wc", nargs="0", help="will overwrite config.ini with current settings")
args, leftovers = parser.parse_known_args()

config = configparser.ConfigParser()
if (args.development == '1'):
    config_ini = "./config.ini"
    code_asm = "./assembler/code.asm"
    assembled_o = "./assembler/assembled.o"
    print("development mode")
elif(platform.system() == "Windows"):
    config_ini = "./assembler/config.ini"
    code_asm = "./assembler/code.asm"
    assembled_o = "./assembler/assembled.o"
elif(platform.system() == "Darwin"):
    config_ini = "../../../assembler/config.ini"
    code_asm = "../../../assembler/code.asm"
    assembled_o = "../../../assembler/assembled.o"
else:
    config_ini = "./assembler/config.ini"
    code_asm = "./assembler/code.asm"
    assembled_o = "./assembler/assembled.o"

config.read(config_ini)
if (len(config.sections()) == 0):
    config['USER CONFIG'] = { 'server' : "", 'port' : '11000', 'uuid' : '' }
    with open(config_ini, 'w') as configfile:
        config.write(configfile)

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
#if args.name is not None:
#    config['USER CONFIG']['controlMap'] = args.controlMap

def attemptValidUUID():
    genUUID = prompt.query("Would you like me to generate a valid UUID for you now?", default="Y")
    if (genUUID == "y" or genUUID == "Y"):
        newUUID = str(uuid.uuid4())
        puts(colored.magenta(newUUID))
        return newUUID
    else:
        return ""

def isValidUUID(uuid):
    x = re.search("^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", config['USER CONFIG']['uuid'].lower())
    if x is None:
        return False
    return True

if not isValidUUID(config['USER CONFIG']['uuid']):
    puts(colored.red("Not a valid UUID! {}".format(config['USER CONFIG']['uuid'])))
    config['USER CONFIG']['uuid'] = attemptValidUUID()
    with open(config_ini, 'w') as configfile:
        config.write(configfile)

if 'uuid' not in config['USER CONFIG'].keys():
    puts(colored.red("You must supply a UUID to have your assembled code sent to the cloud and then automatically downloaded to your RAM module."))
    config['USER CONFIG']['uuid'] = attemptValidUUID()
    with open(config_ini, 'w') as configfile:
        config.write(configfile)

print(args)

f = Figlet(font='slant')

class AddressingModes(enum.Enum):
    Implied = 0   # Use actual number
    Immediate = 1
    Indirect = 2

tabSpacing = 18

def addressingMode(line):
    if (hasNumbers(line)):
        if line.find('#') >= 0:
            return AddressingModes.Immediate
        return AddressingModes.Indirect
    tokens = line.split(' ')
    if (len(tokens) > 1):
        return AddressingModes.Immediate
    return AddressingModes.Implied

def hasLabel(line):
    loc = line.find(":")
    if loc >= 0:
        return True
    return False

def getLabel(line):
    loc = line.find(":")
    return line[0:loc].replace(' ','')

def removeComments(line):
#    line = line.upper()
    loc = line.find(";")
    if loc >= 0:
        line = line[0:loc]
    return line

def labelAtMemoryLocation(loc):
    for label in labels:
        if labels[label] == loc:
            return label
    return ""

def isBlank(line):
    line = line.replace(' ','')
    if len(line) == 0:
        return True
    return False

def getNumber(argument):
    if (len(argument) == 0):
        return 0
    argument = argument.replace('#','')
    loc = argument.find('0x')
    if (loc == 0):
        number = argument[loc+2:]
        return (int(number, base=16))
    try:
        val = int(argument)
        return val
    except ValueError:
        if argument in labels.keys():
            return (int(labels[argument]))
        else:
            return -1

def getTokens(line):
    return re.split(' ',line)

def hasNumbers(line):
    return any(char.isdigit() for char in line)

def modeString(mode):
    if (mode == AddressingModes.Immediate):
         return "immediate"
    if (mode == AddressingModes.Indirect):
         return "indirect"
    if (mode == AddressingModes.Implied):
         return "implied"
    # if (mode == AddressingModes.Register):
    #      return "register"

def referencesLabel(line):
    items = line.split(' ')
    if (len(items) == 1):
        return False
    if (items[1][0].isdigit()):
        return False
    if (items[1][0] == "#"):
        if items[1][1].isdigit():
            return False
    text = items[1].replace("#","")
    if (text in labels.keys()):
        return text
    else:
        print("Error: {} is not defined".format(items[1]))
        quit()
    return False

def convertOpcodeToByte(opcode):
    if (opcode[0:2] == "0x"):
        return int(opcode[2:],16)
    if (opcode[0] == "#"):
        opcode = opcode[1:]
    else:
        return int(opcode)

def checkForDuplicateOpcodes(codes): 
    opcodesEncountered = {}
    duplicateOpcodes = {}
    errorCode = 0 #returns 0 if all is well, otherwise 1
    for key in codes:
        print(key)
        for mode in codes[key]:
            value = codes[key][mode]
            opcode =value['opcode']['value']
            if (opcode in opcodesEncountered.keys()):
                duplicateOpcodes[opcode] = 1
            else:
                duplicateOpcodes[opcode] = 0
            opcodesEncountered[opcode] = 1
            if (duplicateOpcodes[opcode] == 0):
                print("    {} - opcode: {}".format(mode, opcode))
            else:
                errorCode = 1
                print("    {} - opcode: {} **Error, duplicate Opcode".format(mode, opcode))
    return errorCode

codes = {}
params = {}
labels = {}
count = 0
opcodesPath = config['USER CONFIG']['opcodes']
print(os.getcwd())
if (args.development == '1'):
    opcodesPath = './opcodes.json'

with open(opcodesPath) as json_file:
    codes = json.load(json_file)

print(f.renderText(config['USER CONFIG']['name'] + ' Assembler'))

if (checkForDuplicateOpcodes(codes) == 1):
    print("Error, duplicate opcodes encountered.")
    quit()

count = 0
ram = bytearray()
labels = {}

memoryCount = 0
with open(code_asm) as fp:
    line = fp.readline()
    while line:
        line = removeComments(line)
        originalLine = line.rstrip('\n')
        if (hasLabel(line)):
            labelName = getLabel(line)
            if labelName in labels:
                print("Assembler error: Label {} on line {} is already declared".format(labelName, line))
                quit()
            else:
                labels[labelName] = memoryCount
                line = line[line.find(":")+1:]
                line = fp.readline()
                continue
        line =' '.join(line.split())
        if (len(line) == 0):
            line = fp.readline()
            continue
        loc = line.find(' ')
        if (loc >= 0):
            arguments = line[loc:].replace(' ','')
            mnemonic = line[0:loc]
        else:
            mnemonic = line
        if (hasNumbers(line)):
            if (line.find(",") >= 0):
                mnemonic = line[0:line.find(",")]
            elif (line.find(" ") >= 0):
                mnemonic = line[0:line.find(" ")]

        if mnemonic in codes:
            mode = modeString(addressingMode(line))
            if mode in codes[mnemonic]:
                memoryCount += int(codes[mnemonic][mode]["size"])
            else:
                print("Error, mnemonic {} mode {} not defined".format(mnemonic, mode))
        else:
            if (mnemonic != "DB"):
                print("Error, mnemonic {} not defined".format(mnemonic))
            else:
                value = getNumber(arguments)
                # ram.append(value)
                memoryCount = memoryCount + 1

        line = fp.readline()

with open(code_asm) as fp:
    line = fp.readline()
    while line:
        line = removeComments(line)
        count += 1
        originalLine = line.rstrip('\n')
        labelName = ""
        if (hasLabel(line)):
            labelName = getLabel(line)
            line = line[line.find(":")+1:]
        line = line.strip()
        if isBlank(line) == False:
            currentAddress = len(ram)
            line =' '.join(line.split())
            theLabel = referencesLabel(line)
            if theLabel:
                line = line.replace(referencesLabel(line), str(labels[theLabel]))
            loc = line.find(' ')
            arguments = ""
            mnemonic = ""
            if (loc >= 0):
                arguments = line[loc:].replace(' ','')
                mnemonic = line[0:loc]
            number = getNumber(arguments)
            mode = addressingMode(line)
            if (mnemonic == "DB"):
                value = getNumber(arguments)
                ram.append(value)
                puts(colored.yellow("{}\t0x{:04x}: 0x{:02x}\t{}\tData".format(labelAtMemoryLocation(currentAddress), currentAddress, value,line).expandtabs(tabSpacing)))
                line = fp.readline()
                continue

            if (mode == AddressingModes.Implied):
                opcode = codes[line]["implied"]["opcode"]["value"] #entire line is mnemonic
                ram.append(int(opcode[2:],16))
                puts(colored.green("{}\t0x{:04x}: 0x{:02x}\t{}\tImplied".format(labelAtMemoryLocation(currentAddress), currentAddress, int(opcode[2:],16),line).expandtabs(tabSpacing)))

            elif (mode == AddressingModes.Indirect):
                mnemonic = line[0:line.find(' ')]
                operand = int(line[line.find(' ')+1:],16)
                opcode = codes[mnemonic]["indirect"]["opcode"]["value"]
                ram.append(int(opcode[2:],16))
                size = int(codes[mnemonic]["indirect"]["size"])
                if (size == 2):
                    ram.append(operand)
                    puts(colored.blue("{}\t0x{:04x}: 0x{:02x}{:02x}\t{}\tIndirect".format(labelAtMemoryLocation(currentAddress), currentAddress, int(opcode[2:],16), ram[len(ram)-1], line).expandtabs(tabSpacing)))
                else:
                    ram.append(int(operand/256))
                    ram.append(operand % 256)
                    print("{}\t0x{:04x}: 0x{:02x}{:02x}{:02x}\t{}\tIndirect".format(labelAtMemoryLocation(currentAddress), currentAddress, int(opcode[2:],16), ram[len(ram)-2], ram[len(ram)-1], line).expandtabs(tabSpacing))
            
            elif (mode == AddressingModes.Immediate):
                opcode = codes[mnemonic]["immediate"]["opcode"]["value"]
                ram.append(int(opcode[2:],16))
                operand = number
                size = int(codes[mnemonic]["immediate"]["size"])
                if (size == 2):
                    ram.append(int(operand))
                    print("{}\t0x{:04x}: 0x{:02x}{:02x}\t{}\tImmediate".format(labelAtMemoryLocation(currentAddress), currentAddress, int(opcode[2:],16), ram[len(ram)-1], line).expandtabs(tabSpacing))
                else:
                    ram.append(int(operand/256))
                    ram.append(operand % 256)
                    print("{}\t0x{:04x}: 0x{:02x}{:02x}{:02x}\t{}\tImmediate".format(labelAtMemoryLocation(currentAddress), currentAddress, int(opcode[2:],16), ram[len(ram)-2], ram[len(ram)-1], line).expandtabs(tabSpacing))

        line = fp.readline()

ramSize = len(ram)
print("Total Memory: {}".format(ramSize))

f = open(assembled_o, 'wb')
f.write(bytes([ramSize.to_bytes(2, 'big')[0]]))
f.write(bytes([ramSize.to_bytes(2, 'big')[1]]))
f.write(ram)
f.close()

if 'uuid' in config['USER CONFIG'].keys():
    preamble = bytearray(config['USER CONFIG']['uuid'], 'utf-8')

    ram[0:0] = bytes([ramSize.to_bytes(2, 'big')[0]])
    ram[1:0] = bytes([ramSize.to_bytes(2, 'big')[1]])
    preamble.extend(ram)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # print("attempting connect to %s:%s" % (config['USER CONFIG']["server"], config['USER CONFIG']["port"]))
        s.connect((config['USER CONFIG']["server"],int(config['USER CONFIG']['port'])))
        s.send(preamble)
    except Exception as e:
        puts(colored.red("Unable to connect to %s at port %s. Check that you have a good internet connection" % (config['USER CONFIG']["server"], config['USER CONFIG']["port"])))
    finally:
        s.close()
else:
    puts(colored.yellow("No UUID supplied, so no contact with server was attempted."))
print("Labels:")
pprint.pprint(labels)
