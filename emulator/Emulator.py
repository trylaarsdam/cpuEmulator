from enum import Enum
import os
import sys
import json 
import logging
import platform
logging.basicConfig(filename="emulator.log", level=logging.DEBUG, style='{', format='{asctime} [{levelname}] [{module}]: {message}')
logger = logging.getLogger(__name__)
mode = 0

class ControlAssertions(Enum):
    NOT_ASSERTED = 0
    ASSERTED = 1

def bits(n):
    while n:
        b = n & (~n+1)
        yield b
        n ^= b

def clearKthBit(n,k): 
    return (n & ~(1 << (k))) 

def setKthBit(n,k): 
    return ((1 << k) | n) 

def isKthBitSet(n, k): 
    if n & (1 << (k)): 
        return True
    else: 
        return False

class Bus:
    def __init__(self):
        self._components = []
        self.currentValue = 0
        self.isFloating = True
        self.hasConflict = False
        self._numberOfComponents = 0
        self.componentsFromLabels = {}
        self.componentReference = {}
        self.componentByPosition = []
        self.componentByPosition = [None] * 64
        self.disassembly = ""
        self.clockCounter = 0
    
    def getMnemonicForOpcode(self, value, pc):
        theRAM = self.componentReference["RAM"]
        for opcode in self._opcodes:
            modes = self._opcodes[opcode]
            for mode in modes:
                data = modes[mode]
                size = data["size"]
                opcodeValue = int(data["opcode"]["value"],16)
                if opcodeValue == value:
                    if size == 1:
                        return (opcode, mode, size)
                    else:
                        return (opcode, mode, size, theRAM._ram[pc+1])
        return None

    def constructSystem(self, controlMap, opcodes):
        f = open(controlMap)
        self._systemConfig = json.load(f)
        f.close()
        f = open(opcodes)
        self._opcodes = json.load(f)
        f.close()
        for (parameter, value) in self._systemConfig.items():
            self._numberOfComponents = max(self._numberOfComponents, value["busPosition"])
        self._numberOfComponents = self._numberOfComponents + 1
        print(self._numberOfComponents)
        self._components = [None] * self._numberOfComponents
        for (componentName, value) in self._systemConfig.items():
            componentPolarity = 0
            busPosition = None
            controlLineInfo = {}
            if (self._systemConfig[componentName]["type"] == "PC"):
                componentPolarity = self._systemConfig[componentName]["activePolarity"]
                componentPolarity = int(componentPolarity, 2)
                busPosition = self._systemConfig[componentName]["busPosition"]
                controlLineInfo = self._systemConfig[componentName]["controlLinesBitPosition"]
                controlLineData = ['None', 'None', 'None', 'None', 'None', 'None', 'None', 'None']
                for (k, v) in controlLineInfo.items():
                    controlLineData[int(v)] = k
                component = PC(componentPolarity, componentName, busPosition, controlLineData)
                component.setResetControlLine(self._systemConfig[componentName]["clear"])
                self.attachComponent(component, self._systemConfig[componentName]["busPosition"])
                self.componentsFromLabels[componentName] = component, componentName
                self.componentReference[componentName] = component
                self.componentByPosition[self._systemConfig[componentName]["busPosition"]] = component

            if (self._systemConfig[componentName]["type"] == "Register"):
                componentPolarity = self._systemConfig[componentName]["activePolarity"]
                componentPolarity = int(componentPolarity, 2)
                busPosition = self._systemConfig[componentName]["busPosition"]
                controlLineInfo = self._systemConfig[componentName]["controlLinesBitPosition"]
                controlLineData = ['None', 'None', 'None', 'None', 'None', 'None', 'None', 'None']
                for (k, v) in controlLineInfo.items():
                    controlLineData[int(v)] = k
                component = Register(componentPolarity, componentName, busPosition, controlLineData) 
                component.setResetControlLine(self._systemConfig[componentName]["clear"])
                self.attachComponent(component, self._systemConfig[componentName]["busPosition"])
                self.componentsFromLabels[componentName] = component, componentName
                self.componentReference[componentName] = component
                self.componentByPosition[self._systemConfig[componentName]["busPosition"]] = component

            if (self._systemConfig[componentName]["type"] == "MemoryAddressRegister"):
                componentPolarity = self._systemConfig[componentName]["activePolarity"]
                componentPolarity = int(componentPolarity, 2)
                busPosition = self._systemConfig[componentName]["busPosition"]
                controlLineInfo = self._systemConfig[componentName]["controlLinesBitPosition"]
                controlLineData = ['None', 'None', 'None', 'None', 'None', 'None', 'None', 'None']
                for (k, v) in controlLineInfo.items():
                    controlLineData[int(v)] = k
                component = MemoryAddressRegister(componentPolarity, componentName, busPosition, controlLineData)
                component.setResetControlLine(self._systemConfig[componentName]["clear"])
                self.attachComponent(component, self._systemConfig[componentName]["busPosition"])
                self.componentsFromLabels[componentName] = component, componentName
                self.componentReference[componentName] = component
                self.componentByPosition[self._systemConfig[componentName]["busPosition"]] = component

            if (self._systemConfig[componentName]["type"] == "ALU"):
                componentPolarity = self._systemConfig[componentName]["activePolarity"]
                componentPolarity = int(componentPolarity, 2)
                busPosition = self._systemConfig[componentName]["busPosition"]
                controlLineInfo = self._systemConfig[componentName]["controlLinesBitPosition"]
                controlLineData = ['None', 'None', 'None', 'None', 'None', 'None', 'None', 'None']
                for (k, v) in controlLineInfo.items(): 
                    controlLineData[int(v)] = k
                component = ALU(componentPolarity, componentName, busPosition, controlLineData)
                self.attachComponent(component, self._systemConfig[componentName]["busPosition"])
                self.componentsFromLabels[componentName] = component, componentName
                self.componentReference[componentName] = component
                self.componentByPosition[self._systemConfig[componentName]["busPosition"]] = component

            if (self._systemConfig[componentName]["type"] == "RAM"): 
                componentPolarity = self._systemConfig[componentName]["activePolarity"]
                componentPolarity = int(componentPolarity, 2)
                busPosition = self._systemConfig[componentName]["busPosition"]
                controlLineInfo = self._systemConfig[componentName]["controlLinesBitPosition"]
                controlLineData = ['None', 'None', 'None', 'None', 'None', 'None', 'None', 'None']
                for (k, v) in controlLineInfo.items():
                    controlLineData[int(v)] = k
                if (self._systemConfig[componentName]["bits"] == 8):
                    component = RAM(componentPolarity, componentName, busPosition, controlLineData, 0xFF)
                    self.attachComponent(component, self._systemConfig[componentName]["busPosition"])
                    #component.loadAssembly(self._systemConfig[componentName]["assemblerFile"])
                    if(platform.system() == 'Windows'):
                        component.loadAssembly('./assembler/assembled.o')
                    elif(platform.system() == 'Darwin'):
                        component.loadAssembly('../../../assembler/assembled.o')
                    else:
                        component.loadAssembly('./assembler/assembled.o')
                elif (self._systemConfig[componentName]["bits"] == 16):
                    component = RAM(componentPolarity, componentName, busPosition, controlLineData, 0xFFFF)
                    self.attachComponent(component, self._systemConfig[componentName]["busPosition"])
                    #component.loadInstructions(self._systemConfig[componentName]["assemblerFile"])
                    if(platform.system() == 'Windows'):
                        component.loadAssembly('./assembler/assembled.o')
                    elif(platform.system() == 'Darwin'):
                        component.loadAssembly('../../../assembler/assembled.o')
                    else:
                        component.loadAssembly('./assembler/assembled.o')
                self.componentsFromLabels[componentName] = component, componentName
                self.componentReference[componentName] = component
                self.componentByPosition[self._systemConfig[componentName]["busPosition"]] = component

            if (self._systemConfig[componentName]["type"] == "CTRL"): 
                componentPolarity = self._systemConfig[componentName]["activePolarity"]
                componentPolarity = int(componentPolarity, 2)
                busPosition = self._systemConfig[componentName]["busPosition"]
                controlLineInfo = self._systemConfig[componentName]["controlLinesBitPosition"]
                controlLineData = ['None', 'None', 'None', 'None', 'None', 'None', 'None', 'None']
                for (k, v) in controlLineInfo.items():
                    controlLineData[int(v)] = k
                #microcodeFile = self._systemConfig[componentName]["microcodeFile"]
                if(platform.system() == 'Windows'):
                    microcodeFile = './microassembler/microcode.o'
                elif(platform.system() == 'Darwin'):
                    microcodeFile = '../../../microassembler/microcode.o'
                else:
                    microcodeFile = './microassembler/microcode.o'
                component = ControlSequencer(componentPolarity, componentName, self, busPosition, controlLineData, microcodeFile) # polarity, name, bus (self), filename
                self.attachComponent(component, self._systemConfig[componentName]["busPosition"])
                self.componentsFromLabels[componentName] = component, componentName
                self.componentReference[componentName] = component
                self.componentByPosition[self._systemConfig[componentName]["busPosition"]] = component

        for (componentName, componentPointer) in self.componentsFromLabels.items():
            if (type(componentPointer[0]) == RAM):
                toBeAttached = self._systemConfig[componentName]["inputComponents"]
                print(self.componentsFromLabels[toBeAttached[0]])
                componentPointer[0].attachComponent(self.componentsFromLabels[toBeAttached[0]])
            if (type(componentPointer[0]) == ALU):
                toBeAttached1 = self._systemConfig[componentName]["inputComponents"][0]
                toBeAttached2 = self._systemConfig[componentName]["inputComponents"][1]
                print(toBeAttached1[0])
                print(toBeAttached2[0])
                componentPointer[0].attachComponents(self.componentsFromLabels[toBeAttached1], self.componentsFromLabels[toBeAttached2])
            if (type(componentPointer[0]) == ControlSequencer):
                toBeAttached = self._systemConfig[componentName]["inputComponents"]
                print(self.componentsFromLabels[toBeAttached[0]])
                componentPointer[0].attachComponent(self.componentsFromLabels[toBeAttached[0]])

    def attachComponent(self, component, position):
        self._components[position] = component
        component.setComponentIndex(self._components.index(component))

    def setControlWord(self, component, controlWord):
        c = self._components[component]
        c.setControlWord(controlWord)

    def scan(self):
        haveBusDriver = -1
        self.isFloating = True
        self.hasConflict = False
        for c in self._components:
            if (c != None):
                c.busScan()
                c.busValue = self.currentValue
                if c.isDrivingBus():
                    if haveBusDriver == -1:
                        if c.getValue(False) != None:
                            self.currentValue = c.getValue(False)
                        haveBusDriver = self._components.index(c)
                        self.isFloating = False
                    else:
                        self.hasConflict = True
                        print("Bus Conflict!")
                        print("Conflicting Components: " + str(haveBusDriver) + " " + str(self._components.index(c)))

    def clockFallingEdge(self):
        logger.debug("Before clock:" + str(self.exportBusdata()))
        for c in self._components:
            if (c != None):
                c.clockFallingEdge()
        logger.debug("After clock:" + str(self.exportBusdata()))
        return "clock fell"

    def getCurrentValue(self, override):
        return 

    def addClockStrike(self):
        self.clockCounter = self.clockCounter + 1

    def clearClockStrikes(self):
        self.clockCounter = 0

    def exportBusdata(self):
        busData = {}
        ctrlSeq = self.componentReference["CTRL"]
        if ctrlSeq._currentValue == 2:
            instReg = self.componentReference["INST"]
            pc = self.componentReference["PC"]._currentValue
            currentValue = instReg._currentValue
            opcodeData = self.getMnemonicForOpcode(currentValue, pc)
            if(opcodeData == None):
                logger.warn("opcodeData was NoneType")
            else:
                if opcodeData[2] == 1:
                    self.disassembly = "0x{:04X}: {}".format(pc, opcodeData[0])
                else:
                    if opcodeData[3] == None:
                        self.disassembly = "Unknown"
                    else:
                        self.disassembly = "0x{:04X}: {} 0x{:02X}".format(pc, opcodeData[0], opcodeData[3])
        elif ctrlSeq._currentValue > 2:
            pass
        else:
            self.disassembly = "FETCHING"

        for c in self._components:
            if(c != None):
                componentName = c.name
                componentType = c.type
                componentPosition = c.busPosition
                componentControlLineNames = c.controlLineNames
                componentControlLineStatus = [0,0,0,0,0,0,0,0] 
                componentDrivingBus = c._drivingBus
                componentReadingBus = c._readingBus
                if (c.getValue(True) == None):
                    componentValue = "None"
                else:
                    componentValue = c.getValue(True)
                for i in range(0, 8):
                    if(isKthBitSet(c.controlWord, int(i))):
                        componentControlLineStatus[i] = 1
                    else:
                        componentControlLineStatus[i] = 0
                ctrlComponentValue = "t" + str(componentValue)
                if(componentType != "ALU"):
                    busData.update( {componentName : {"currentValue": componentValue, "busPosition": componentPosition, "componentType": componentType, "drivingBus": componentDrivingBus, "readingBus": componentReadingBus, "ctrlLineNames": componentControlLineNames, "ctrlWord": componentControlLineStatus, "ctrlByte": c.controlWord}})
                elif(componentType == "CTRL"):
                    busData.update( {componentName : {"currentValue": ctrlComponentValue, "halt": c.halt,"busPosition": componentPosition, "componentType": componentType, "drivingBus": componentDrivingBus, "readingBus": componentReadingBus, "ctrlLineNames": componentControlLineNames, "ctrlWord": componentControlLineStatus, "ctrlByte": c.controlWord}})
                else:
                    busData.update( {componentName : {"currentValue": componentValue, "busPosition": componentPosition, "componentType": componentType, "drivingBus": componentDrivingBus, "readingBus": componentReadingBus, "ctrlLineNames": componentControlLineNames, "ctrlWord": componentControlLineStatus, "ctrlByte": c.controlWord, "zeroFlag": c.zeroFlag, "carryFlag": c.carryFlag}})
        busData.update( {"bus": {"currentValue": self.currentValue, "isFloating": self.isFloating, "hasConflict": self.hasConflict, "currentOpcode": str(self.disassembly), "clockCounter": str(self.clockCounter)}})
        #logger.debug(busData)6
        #print(json.dumps(busData)) 
        return busData

class Component:
    def __init__(self, ctrlWordActivePolarity, name, busPosition, ctrlLines):
        self._controlLineData = []
        self._polarity = ctrlWordActivePolarity
        self._currentValue = 0
        self._drivingBus = False
        self._readingBus = False
        self.controlWord = 0xff - self._polarity
        self.busValue = 0
        self.resetBitSet = False
        self.resetBit = 0
        self.name = name
        print(busPosition)
        self.busPosition = busPosition
        self.controlLineNames = ctrlLines
        self.name = name
        self.type = ""
    
    def isDrivingBus(self):
        return self._drivingBus

    def setResetControlLine(self, bitNumber):
        self.resetBitSet = True
        self.resetBit = bitNumber

    def reset(self):
        if self.resetBitSet:
            self.doAssertion(self.resetBit, True)
        if(mode):
            self.controlWord = 0xff - self._polarity
            self._drivingBus = False
            self._readingBus = False 

    def setControlWord(self, value):
        if value == None:
            logger.warn(self.name + " setControlWord is None")
        else:
            self.controlWord = value
            self._assertions = 0xff - (self.controlWord ^ self._polarity)
            self.handleAssertions()

    def doAssertion(self, assertionIndex, asserted):
        return # This should be overriden by the subclass.

    def handleAssertions(self):
        for index in range(8):
            if isKthBitSet(self._assertions, index):
                self.doAssertion(index, True)
            else:
                self.doAssertion(index, False)

    def getValue(self, override):
        if self._drivingBus:
            return self._currentValue
        elif override: 
            return self._currentValue
        else:
            return None
    
    def setComponentIndex(self, assignedIndex):
        self._componentIndex = assignedIndex

    def index(self):
        return self._componentIndex

    def clockFallingEdge(self):
        return # This should be overriden by the subclass. 
    
    def clockRisingEdge(self):
        pass

    def busScan(self):
        return 

class Register(Component):
    def __init__(self, ctrlWordActivePolarity, name, busPosition, ctrlLines):
        super().__init__(ctrlWordActivePolarity, name, busPosition, ctrlLines)
        self._currentValue = 0
        try:
            self._OE_CTRL = ctrlLines.index("OE")
        except:
            pass
        try:
            self._CLR_CTRL = ctrlLines.index("CLR")
        except:
            pass
        try:
            self._LOAD_CTRL = ctrlLines.index("LOAD")
        except:
            pass
        self.type = "Register"

    def doAssertion(self, assertionIndex, asserted):
        # print("assertion index: " + str(assertionIndex) + " value: " + str(asserted))
        if assertionIndex == self._OE_CTRL:
            if asserted:  # OE
                self._drivingBus = True
            else:
                self._drivingBus = False
        if assertionIndex == self._CLR_CTRL:
            if asserted:  # CLR
                self._currentValue = 0
        if assertionIndex == self._LOAD_CTRL:
            if asserted:  # LOAD
                self._readingBus = True
            else:
                self._readingBus = False

    def clockFallingEdge(self):
        if self._readingBus:
            self._currentValue = self.busValue
            if self.name == "OUT":
                print("OUT: {}".format(self._currentValue))

class PC(Component):
    def __init__(self, ctrlWordActivePolarity, name, busPosition, ctrlLines):
        super().__init__(ctrlWordActivePolarity, name, busPosition, ctrlLines)
        self._incrementEnable = 0 #enables/disables incrementing on clock strikes
        self._currentValue = 0
        self._resetEnable = 0
        self._LOAD_LSB = ctrlLines.index("LOAD_LSB")
        self._LOAD_MSB = ctrlLines.index("LOAD_MSB")
        self._LOAD16_CTRL = ctrlLines.index("LOAD_16")
        self._INC_CTRL = ctrlLines.index("INC")
        self._OE_CTRL = ctrlLines.index("OE")
        self._RST_CTRL = ctrlLines.index("RST")
        self.type = "PC"

    def doAssertion(self, assertionIndex, asserted):
        if assertionIndex == self._OE_CTRL:
            if asserted: #OE
                self._drivingBus = True
            else:
                self._drivingBus = False
        if assertionIndex == self._LOAD_LSB:
            if asserted: #load LSB 
                self._readingBus = True
            else:
                self._readingBus = False
        if assertionIndex == self._INC_CTRL:
            if asserted: #INC 
                #count up with clock
                self._incrementEnable = 1
            else:
                #do not count up with clock
                self._incrementEnable = 0
        if assertionIndex == self._RST_CTRL:
            if asserted:  # CLR
                self._currentValue = 0
    def clockFallingEdge(self):
        if(self._incrementEnable): #INC
            self._currentValue = 1 + self._currentValue 
        if(self._readingBus): #LOAD LSB
            self._currentValue = self.busValue
        if(self._resetEnable): #RESET   
            self._currentValue = 0      

class RAM(Component):
    def __init__(self, ctrlWordActivePolarity, name, busPosition, ctrlLines, total_size):
        super().__init__(ctrlWordActivePolarity, name, busPosition, ctrlLines)
        self.size = total_size
        self.availableSpace = total_size
        self._usedSpace = self.size - self.availableSpace
        self._ram = [None] * total_size
        self._WE_CTRL = ctrlLines.index("WE")
        self._OE_CTRL = ctrlLines.index("OE")
        self._RST_CTRL = ctrlLines.index("RST")
        self._outputEnable = 0
        self._writeEnable = 0
        self._resetEnable = 0
        self._internalMAR = None #set later in self.attachComponent
        self.type = "RAM"
    
    def reset(self):
        print ("ram reloading from assembler.o file")
        self.loadAssembly(self.fileName)

    def attachComponent(self, attachedComponent):
        self._internalMAR = attachedComponent[0]

    def busScan(self):
        if self._readingBus:
            self._currentValue = self.busValue
        else:
            self._currentValue = self._ram[self._internalMAR._currentValue]
        if self._drivingBus:
            self.busValue = self._currentValue

    def clearRAM(self):
        self._ram = []
        print("RAM_CLEARED")
    
    def loadAssembly(self, fileName):
        #load instruction set from opcodes.json
        self.fileName = fileName
        with open(fileName, 'rb') as f:
            bytes = f.read(2)
            msb = bytes[0]
            msb = msb * 256
            lsb = bytes[1]
            size = msb + lsb
            for i in range(size):
                byte = f.read(1)
                self._ram[i] = byte[0]
            f.close()
        #logger.debug(self._ram)

    def getSize(self):
        return len(self._ram)

    def storeAt(self, location, data):
        self._ram[location] = data
    
    def dataAt(self, location):
        print(self._ram[location])

    def doAssertion(self, assertionIndex, asserted):
        if(assertionIndex == self._OE_CTRL):
            if asserted:
                self._drivingBus = 1
            else:
                self._drivingBus = 0
        if(assertionIndex == self._WE_CTRL):
            if asserted:
                self._readingBus = 1
            else:
                self._readingBus = 0
        if(assertionIndex == self._RST_CTRL):
            if asserted:
                self.reset()
    
    def clockFallingEdge(self):
        if(self._readingBus):
            self._ram[self._internalMAR._currentValue] = self.busValue

class ControlSequencer(Component):
    def __init__(self, ctrlWordActivePolarity, name, bus, busPosition, ctrlLines, fileName):
        super().__init__(ctrlWordActivePolarity, name, busPosition, ctrlLines)
        self.instructionRegister = None
        self._memory = [None] * 2**18
        self.loadMicrocode(fileName)
        self.filename = fileName
        self.timeSequence = 0
        self._bus = bus
        self._resetSequenceCountOnNextClockCycle = False
        self.type = "CTRL"
        self.halt = False

    def attachComponent(self, instReg):
        self.instructionRegister = instReg[0]

    def getFlags(self):
        for c in self._bus._components:
            if (getattr(c, "getFlags", None) != None):
                flags = c.getFlags()
                return flags
        return 0

    def sendOutControlWords(self):
        flags = self.getFlags()
        print("FLAGS: " + bin(flags))
        opcode = self.instructionRegister._currentValue
        address = opcode << 10
        flgs = flags << 8
        ts = self.timeSequence << 4
        address = address | flgs | ts
        print("Address: " + hex(address))
        for i in range(len(self._bus._components)):
            ctrlWord = self._memory[address + i]
            if (self._bus._components[i] != None):
                self._bus._components[i].setControlWord(ctrlWord)
                print(str(i) + ": " + hex(ctrlWord))
                if isKthBitSet(self.controlWord, 0) and (i == (len(self._bus._components)-1)): #this line is the death of me
                    self._resetSequenceCountOnNextClockCycle = True
        self._bus.scan()

    def reset(self):
        self.loadMicrocode(self.filename)
        self.timeSequence = 0
        self._currentValue = 0
        self._resetSequenceCountOnNextClockCycle = False
        if(mode == 0):
            self.sendOutControlWords()

    def busScan(self):
        if(isKthBitSet(self.controlWord, 1)):
            self.halt = True
        else:
            self.halt = False


    def clockFallingEdge(self):
        if self._resetSequenceCountOnNextClockCycle:
            self.timeSequence = -1
            self._resetSequenceCountOnNextClockCycle = False

    def clockRisingEdge(self):
        if(mode == 0):
            self.timeSequence = self.timeSequence + 1
        self._currentValue = self.timeSequence
        if(mode == 0):
            self.sendOutControlWords() 

    def loadMicrocode(self, fileName):
        with open(fileName, 'rb') as f:
            bytes = f.read(2)
            msb = bytes[0]
            msb = msb * 256
            lsb = bytes[1]
            size = msb + lsb
            count = 0
            byte = f.read(1)
            componentCount = byte[0]
            count = count + 1

            while count < size:
                byte = f.read(1)
                opcode = byte[0]
                count = count + 1
                for flag in range(4):
                    byte = f.read(1)
                    count = count + 1
                    flags = byte[0]
                    byte = f.read(1)
                    count = count + 1
                    timeslotsForOpcode = byte[0]
                    for timeSlot in range(timeslotsForOpcode):
                        for component in range(componentCount):
                            byte = f.read(1)
                            count = count + 1
                            ctrlWord = byte[0]
                            # build address
                            address = opcode << 10
                            flgs = flags << 8
                            address = address | flgs
                            ts = timeSlot << 4
                            address = address | ts
                            address = address | component
                            self._memory[address] = ctrlWord
            f.close()
        #logger.debug(self._memory)

class MemoryAddressRegister(Register):
    def __init__(self, ctrlWordActivePolarity, name, busPosition, ctrlLines):
        super().__init__(ctrlWordActivePolarity, name, busPosition, ctrlLines)
        self._msb = 0
        self._lsb = 0
        self._LSB_CTRL = ctrlLines.index("LOAD_LSB")
        self._MSB_CTRL = ctrlLines.index("LOAD_MSB")
        self._LOAD16_CTRL = ctrlLines.index("LOAD_16")
        self._RST_CTRL = ctrlLines.index("RST")
        self._byteSelect = 0
        self._resetEnable = 0
        self.type = "MAR"
    
    def busScan(self):
        if self._resetEnable:
            self._currentValue = 0

    def doAssertion(self, assertionIndex, asserted):
        if assertionIndex == self._LSB_CTRL:
            if asserted: #LSB LOAD
                self._readingBus = True
                self._byteSelect = 0
            else:
                self._readingBus = False
        if assertionIndex == self._MSB_CTRL:
            if asserted: #MSB LOAD
                self._readingBus = True
                self._byteSelect = 1
        if assertionIndex == self._LOAD16_CTRL:
            if asserted: #LOAD_16
                return
        if assertionIndex == self._RST_CTRL:
            if asserted: #RESET
                self._currentValue = 0

    def clockFallingEdge(self):
        if(self._readingBus):
            self._currentValue = self.busValue
            #elif (self._byteSelect):
             #   self._currentValue = self._currentValue & 0x00FF
              #  self._currentValue = self._currentValue | (bus.currentValue << 8)
        if(self._resetEnable):
            self._currentValue = 0

class ALU(Component):
    def __init__(self, ctrlWordActivePolarity, name, busPosition, ctrlLines):
        super().__init__(ctrlWordActivePolarity, name, busPosition, ctrlLines)
        self._CF_OUT_CTRL = ctrlLines.index("CF_OUT")
        self._ZF_OUT_CTRL = ctrlLines.index("ZF_OUT")
        self._FLG_OE_CTRL = ctrlLines.index("FLG_OE")
        self._CLR_CTRL = ctrlLines.index("CLR")
        self._OE_CTRL = ctrlLines.index("OE")
        self._SUB_CTRL = ctrlLines.index("SUB")
        self._FLAGS_LOAD = ctrlLines.index("FLAGS_LOAD")
        self._clearEnable = 0
        self._outputEnable = 0
        self._subtractEnable = 0
        self._component1 = None
        self._component2 = None
        self._loadFlags = False
        self.zeroFlag = False
        self.carryFlag = False
        self.type = "ALU"

    def getFlags(self):
        result = 0
        if self.zeroFlag:
            result = setKthBit(result, self._ZF_OUT_CTRL)
        if self.carryFlag:
            result = setKthBit(result, self._CF_OUT_CTRL)
        return result

    def reset(self):
        self.zeroFlag = False
        self.carryFlag = False
        self.controlWord = clearKthBit(self.controlWord, self._ZF_OUT_CTRL)
        self.controlWord = clearKthBit(self.controlWord, self._CF_OUT_CTRL)

    def setControlWord(self, value):
        if value == None:
            logger.warn(self.name + " setControlWord is None")
        else:
            for i in range(8):
                if(i >= 2):
                    if(isKthBitSet(value, i)):
                        self.controlWord = setKthBit(self.controlWord, i)
                    else:
                        self.controlWord = clearKthBit(self.controlWord, i)
            self._assertions = 0xff - (self.controlWord ^ self._polarity)
            self.handleAssertions()

    def clockFallingEdge(self):
        if(self._loadFlags):
            if self.zeroFlag:
                self.controlWord = setKthBit(self.controlWord, self._ZF_OUT_CTRL)
            else:
                self.controlWord = clearKthBit(self.controlWord, self._ZF_OUT_CTRL)
            if self.carryFlag:
                self.controlWord = setKthBit(self.controlWord, self._CF_OUT_CTRL)
            else:
                self.controlWord = clearKthBit(self.controlWord, self._CF_OUT_CTRL)

    def attachComponents(self, component1, component2):
        self._component1 = component1[0]
        self._component2 = component2[0]
        
    def busScan(self):
        #add component1 and 2 values together or sub if SUB line is asserted
        if(self._subtractEnable):
            self._currentValue = self._component1._currentValue - self._component2._currentValue
            if(self._currentValue == 0):
                self.zeroFlag = True
            else:
                self.zeroFlag = False

            if(self._currentValue > 255 or self._currentValue < -256):
                self.carryFlag = True
            else:
                self.carryFlag = False
        else:
            self._currentValue = self._component1._currentValue + self._component2._currentValue
            if(self._currentValue == 0):
                self.zeroFlag = True
            else:
                self.zeroFlag = False
            
            if(self._currentValue > 255):
                self.carryFlag = True
            else:
                self.carryFlag = False

    def doAssertion(self, assertionIndex, asserted):
        if assertionIndex == self._SUB_CTRL:
            if asserted: 
                self._subtractEnable = True
            else:
                self._subtractEnable = False
        if assertionIndex == self._FLAGS_LOAD:
            if asserted: 
                self._loadFlags = True
            else:
                self._loadFlags = False
        if assertionIndex == self._OE_CTRL:
            if asserted: 
                self._drivingBus = True
            else:
                self._drivingBus = False
        if assertionIndex == self._CLR_CTRL:
            if asserted: 
                self.reset()

if __name__ == "__main__":
    bus = Bus()
    bus.constructSystem('./controlmap.json', './opcodes.json')
    bus.scan()
    bus.exportBusdata()
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
    bus.exportBusdata()
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
    bus.exportBusdata()
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
    bus.exportBusdata()
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
    bus.exportBusdata()
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
    bus.exportBusdata()
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
    bus.exportBusdata()
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
    bus.exportBusdata()
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
    bus.exportBusdata()
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