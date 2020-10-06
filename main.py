from __future__ import print_function
import time
from flask import Flask
from flask import render_template
from flask import request
from flask import send_from_directory
from emulator import Emulator
import sys
import os
import logging
import platform
import paho.mqtt.client as mqtt
logging.basicConfig(filename="emulator.log", level=logging.DEBUG, style='{', format='{asctime} [{levelname}] [{module}]: {message}')
logger = logging.getLogger(__name__)

buttonIncrementValue = 0
bus = Emulator.Bus()
print(bus)
uuid = ''
mqttStatus = False
#bus.constructSystem('../../controlmap.json')\
if(platform.system() == 'Darwin'):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(os.getcwd())
    bus.constructSystem("../../../controlmap.json", "../../../opcodes.json")
elif(platform.system() == 'Windows'):
    bus.constructSystem("./controlmap.json", "./opcodes.json")
else:
    bus.constructSystem("./controlmap.json", "./opcodes.json")
print(bus._components)
numOfComponents = len(bus._components) 
bus.componentReference['CTRL'].sendOutControlWords()

app = Flask(__name__, static_url_path='/')
buttonTestArray = ["button1", "button2", "button3"]

@app.route("/", defaults={'inputData' : 'not specified'})
@app.route("/<inputData>")
def hello(inputData):
    bus.scan()
    print("python-started rendering")
    global numOfComponents
    component_list = []
    for i, c in enumerate(bus._components):
        component_list.append(i)
    with app.app_context():
        rendered = render_template('index_template.html', \
            title = "CPU Emulator", \
            buttonClicked = inputData, \
            buttonArray = [{"name": "button1"}, {"name": "button2"}, {"name": "button3"}], \
            component = ['A'], \
            numberOfComponents = numOfComponents, \
            component_list = component_list, \
            emulatorData = bus._components)
        return rendered

@app.route("/setRealComponents")
def handleSetReal():
    bus.scan()
    component_list = []
    for i, c in enumerate(bus._components):
        component_list.append(i)
    with app.app_context():
        rendered = render_template('selection_template.html', \
            title = "Component Selection", \
            numberOfComponents = numOfComponents, \
            component_list = component_list, \
            emulatorData = bus._components)
        return rendered

@app.route("/test1")
def test1():
    return "blank"

@app.route("/devaccess/checkbusstatus")
def checkBusStatus():
    if (bus._components != None):
        return "bus has been loaded"
    else:
        return "bus not loaded"

@app.route("/checkBoxClicked/<checkboxID>/<state>")
def checkBoxClicked(checkboxID, state):
    items = checkboxID.split('_')
    print(items)
    componentName = items[0]
    bitID = int(items[1])
    print(bus.componentsFromLabels[componentName])
    cw = bus.componentsFromLabels[componentName][0].controlWord
    print(cw)
    if (state == '1'):
        bus.componentsFromLabels[componentName][0].setControlWord(Emulator.setKthBit(cw, bitID))
        print(str(bitID) + " set")
        print(bus.componentsFromLabels[componentName][0].controlWord)
    elif (state == '0'): 
        bus.componentsFromLabels[componentName][0].setControlWord(Emulator.clearKthBit(cw, bitID))
        print(str(bitID) + " cleared")
        print(bus.componentsFromLabels[componentName][0].controlWord)
    bus.scan()
    return bus.exportBusdata()

@app.route('/devaccess/busvalue')
def printBusValue():
    return str(bus.currentValue)

@app.route('/mqtt/controlUp/<component>/<ctrlWord>')
def mqttHandleControlWord(component, ctrlWord):
    logger.debug("mqttHandleControlWord: " + str(bus.componentByPosition[int(component)].controlWord))
    bus.componentByPosition[int(component)].controlWord = int(ctrlWord)
    bus.scan()
    logger.debug("mqttHandleControlWord after: " + str(bus.componentByPosition[int(component)].controlWord))
    return bus.exportBusdata()

@app.route('/mqtt/ctrlLines/<component>/<ctrlLine>/<state>')
def mqttHandleCtrlLines(component, ctrlLine, state):
    print(bus.componentByPosition[int(component)].busPosition)
    bitID = int(ctrlLine)
    cw = bus.componentByPosition[int(component)].controlWord
    if (int(state) == 1):
        bus.componentByPosition[int(component)].setControlWord(Emulator.setKthBit(cw, bitID))
        print(str(bitID) + " set")
        print(bus.componentByPosition[int(component)].controlWord)
    elif (int(state) == 0):
        bus.componentByPosition[int(component)].setControlWord(Emulator.clearKthBit(cw, bitID))
        print(str(bitID) + " cleared")
        print(bus.componentByPosition[int(component)].controlWord)
    bus.scan()
    return get_bus_json()

@app.route('/mqtt/setUUID/<inputUUID>')
def mqttHandleUUID(inputUUID):
    print("mqttUUID" + inputUUID)
    uuid = inputUUID
    if(uuid != ""):
        enableMQTT(True)
    else:
        enableMQTT(False)

@app.route('/mqtt/enableMQTT/<status>')
def enableMQTT(status):
    print("mqttSET" + status)
    if(status == "true" or True):
        mqttStatus = True
    elif(status == "false" or False):
        mqttStatus = False
    else:
        mqttStatus = False

@app.route('/mqtt/busValue/<busValue>/<driver>')
def mqttHandleSetBusValue(busValue, driver): 
    logger.debug(driver)
    if(driver != "none"):
        bus.currentValue = int(busValue)
        bus.componentsFromLabels[driver][0]._currentValue = int(busValue)
    bus.scan()
    bus.addClockStrike()
    for i in range(len(bus._components)):
            c = bus._components[i]
            if c != None:
                c.clockFallingEdge()
    logger.debug("bus.clockRisingEdge")
    for i in range(len(bus._components)):
        c = bus._components[i]
        if c != None:
            c.clockRisingEdge()
    bus.scan()
    logger.debug(bus.exportBusdata())
    return bus.exportBusdata()

@app.route('/devaccess/buslist')
def dev_listbus():
    returnValue = ""
    for component in bus._components:
        returnValue.append(component)
    return returnValue

@app.route('/devaccess/ram/<start>/<amount>')
def dev_accessRAM(start, amount):
    returnValue = ""
    if(start[1] == "x" or start[1] == "X"):
        returnValue += start
        returnValue += ": "
    else:
        returnValue += "0x"
        returnValue += start
        returnValue += ": "
    for i in range(int(amount, base=10)):
        if(bus.componentsFromLabels['RAM'][0]._ram[int(start, base=16) + i] != None):
            returnValue += str(hex(bus.componentsFromLabels['RAM'][0]._ram[int(start, base=16) + i]))[2:].zfill(2)
        else:
            returnValue += "None"
        returnValue += " "
    return returnValue

@app.route('/devaccess/bus-access')
def get_bus_json():
    #logger.debug("/devaccess/bus-access returning")
    bus.scan()
    #publishToMQTT()
    return bus.exportBusdata()

@app.route('/js/<path:path>')
def send_js(path):
    print(path)
    return send_from_directory('js', path)

@app.route("/mode/<mode>")
def setMode(mode):
    if(int(mode, 10) == 0):
        Emulator.mode = 0
    elif(int(mode, 10) == 1):
        Emulator.mode = 1
    return "Mode set"

@app.route("/stop-backend")
def stop():
    logger.warn("Manually stopped")
    sys.exit("Manually Stopped")
    return

@app.route("/<buttonID>/buttonClicked")
def buttonClicked(buttonID):
    if(buttonID == 'debugComponentList'):
        returnValue = ""
        for component in bus._components:
            returnValue = returnValue + str(component)
        bus.scan()
        return get_bus_json()
    elif(buttonID == 'clock'):
        logger.debug("clock triggered from buttonClick")
        return clockTriggered()
    elif(buttonID == 'reset'):
        return resetemulator()
    elif(buttonID == 'assembler'):
        if(platform.system() == 'Windows'):
            os.system('start /wait cmd /k python ./assembler/main.py ./assembler/code.asm -o ./opcodes.json')
        elif(platform.system() == 'Darwin'):
            os.system('/Library/Frameworks/Python.framework/Versions/3.8/bin/python3 ../../../assembler/main.py ../../../assembler/code.asm')
        else:
            os.system('python3 ../../assembler/main.py ../../assembler/code.asm')
        return get_bus_json()
    elif(buttonID == 'microassembler'):
        if(platform.system() == 'Windows'):
            os.system('start /wait cmd /k python .\microassembler\main.py -c .\controlmap.json -o .\opcodes.json')
        elif(platform.system() == 'Darwin'):
            os.system('/Library/Frameworks/Python.framework/Versions/3.8/bin/python3 ../../../microassembler/main.py -c ../../../controlmap.json -o ../../../opcodes.json')
        else:
            os.system('python3 ../../microassembler/main.py -c ../../controlmap.json -o ../../opcodes.json')
        return get_bus_json()
    else:
        #returnValue = ""
        items = buttonID.split('_')
        #print(items[0])
        #print(items[1])
        print(bus.componentsFromLabels[items[0]])
        bus.componentsFromLabels[items[0]][0]._currentValue = bus.componentsFromLabels[items[0]][0]._currentValue + 1
        #returnValue = str(bus.componentsFromLabels[items[0]][0]._currentValue)
        #print(returnValue)
        bus.scan()
        return bus.exportBusdata()

def clockTriggered():
    logger.debug("bus.clockFallingEdge")
    bus.scan()
    bus.addClockStrike()
    for i in range(len(bus._components)):
            c = bus._components[i]
            if c != None:
                c.clockFallingEdge()
    logger.debug("bus.clockRisingEdge")
    for i in range(len(bus._components)):
        c = bus._components[i]
        if c != None:
            c.clockRisingEdge()
    bus.scan()
    return get_bus_json()

def resetemulator():
    bus.clearClockStrikes()
    for c in range(len(bus._components)):
        comp = bus._components[c]
        if(comp != None):
            comp.reset()
    bus.scan()
    return get_bus_json()

def publishToMQTT():
    if(mqttStatus == True or mqttStatus == False):
        for c in range(len(bus._components)):
            comp = bus._components[c]
            res = [int(i) for i in list('{0:0b}'.format(comp.controlWord))] 
            for c in range(8):
                client.publish("CPU-WCL/" + uuid + "/components/" + str(comp.busPosition) + "/" + str(c), res[c])
    else:
        return

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("cpu-bus/trylaarsdam/pythonDevChannel")

def on_message(client, userdata, msg):
    print(msg.topic+ " " + str(msg.payload))

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("lab.thewcl.com", 1883, 60)
    print(buttonClicked('debugComponentList'))
    client.loop_start()
    app.run(host='127.0.0.1', port=5000)

    #bus.componentsFromLabels["A"][0]._currentValue = 1
    #bus.scan()
    #bus.componentByPosition[7].setControlWord(int('10101011', 2)) #1010 1011
    #bus.scan()
    #clockTriggered()
    #bus.scan()