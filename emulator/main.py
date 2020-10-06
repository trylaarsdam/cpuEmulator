import sys
import Emulator
from subprocess import call
import threading
import time
import platform

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QPixmap

leftMargin = 75
topMargin = 25

verticalSpacing = 100
horizontalSeparation = 400
numberOfControlBits = 8
labelWidth = horizontalSeparation / 4
labelHeight = 50
lcdWidth = horizontalSeparation / 4
lcdHeight = 30
editButtonWidth = 40

class Ui_MainWindow(QMainWindow):

    def clockTriggered(self):
        for i in range(len(self.bus._components)):
            c = self.bus._components[i]
            if c != None:
                c.clockFallingEdge()
        for i in range(len(self.bus._components)):
            c = self.bus._components[i]
            if c != None:
                c.clockRisingEdge()
        self.refresh()

    def resetTriggered(self):
        for c in range(len(self.bus._components)):
            comp = self.bus._components[c]
            if(comp != None):
                comp.reset()
        self.refresh()

    def refresh(self):
        self.bus.scan()
        ui.updateControlWords(bus)
        for i in range(len(self.bus._components)):
            comp = self.bus._components[i]
            if (comp != None):
                if (hasattr(comp,"_loadFlags")):
                    self.flagButtons[0].setChecked(comp.zeroFlag)
                    self.flagButtons[1].setChecked(comp.carryFlag)
                if comp._drivingBus:
                    self.labels[i].setStyleSheet("QLabel { background-color : blue; }")
                else:
                    if comp._readingBus:
                        self.labels[i].setStyleSheet("QLabel { background-color : green; }")
                    else:
                        self.labels[i].setStyleSheet("QLabel { }")
                self.lcds[i].setProperty("value", self.bus._components[i]._currentValue)
        self.busLCD.setProperty("value", self.bus.currentValue)
        
        if bus.isFloating:
            ui.busLabel.setText("FLOATING")
            ui.busLabel.setStyleSheet("QLabel { }")
        else: 
            if bus.hasConflict:
                ui.busLabel.setText("BUS CONFLICT!")
                ui.busLabel.setStyleSheet("QLabel { background-color : red; }")
            else:
                ui.busLabel.setText("NORMAL")
                ui.busLabel.setStyleSheet("QLabel { background-color : blue; }")
            
        

    def mousePressEvent(self, QMouseEvent):
        print (QMouseEvent.pos())

    def flagClicked(self, state):
        pass

    def editButtonTapped(self):
        sendingCheckBox = self.sender()
        items = sendingCheckBox.objectName().split('_')
        component = int(items[1])
        bus._components[component]._currentValue = bus._components[component]._currentValue + 1
        self.refresh()
        

    def checkBoxClicked(self, state):
        sendingCheckBox = self.sender()
        items = sendingCheckBox.objectName().split('_')
        component = int(items[1])
        bit = 7 - int(items[2])
        cw = self.bus._components[component].controlWord
        if state:
            self.bus._components[component].setControlWord(Emulator.setKthBit(cw,bit))
        else:
            self.bus._components[component].setControlWord(Emulator.clearKthBit(cw,bit))
        self.refresh()

    def buildFlagButton(self, componentNumber, flagNumber):
        verticalIncrement = int(componentNumber / 2)
        flagsize = 20
        yPos = 200 + verticalSpacing * verticalIncrement + flagNumber + topMargin

        flagButton = QtWidgets.QCheckBox(self.centralwidget)
        if (componentNumber % 2):
            flagButton.setGeometry(QtCore.QRect(horizontalSeparation + leftMargin + flagNumber*flagsize, yPos, flagsize, flagsize))
        else:
            flagButton.setGeometry(QtCore.QRect(leftMargin + labelWidth * 2 + flagNumber*flagsize, yPos, flagsize, flagsize))
        flagButton.setObjectName("flag_" + str(flagNumber) )
        flagButton.clicked.connect(self.flagClicked)
        return flagButton

    def buildRadioButton(self, componentNumber, bitNumber, startOffset):
        verticalIncrement = int(componentNumber / 2)
        yPos = 120 + verticalSpacing * verticalIncrement + startOffset + topMargin

        radioButton = QtWidgets.QCheckBox(self.centralwidget)
        if (componentNumber % 2):
            radioButton.setGeometry(QtCore.QRect(horizontalSeparation + leftMargin + bitNumber*20, yPos, 20, 20))
        else:
            radioButton.setGeometry(QtCore.QRect(leftMargin + labelWidth * 2 - (numberOfControlBits*20) + bitNumber*20, yPos, 20, 20))
        radioButton.setObjectName("radioButton_" + str(componentNumber) + "_" + str(bitNumber))
        radioButton.clicked.connect(self.checkBoxClicked)
        return radioButton

    def addClockButton(self):
        _translate = QtCore.QCoreApplication.translate
        font = QtGui.QFont()
        font.setFamily("Victor Mono")
        font.setPointSize(24)

        rowCount = int((len(self.bus._components)+1) / 2) + 1
        self.clkButton = QtWidgets.QPushButton(self.centralwidget)
        self.clkButton.setGeometry(QtCore.QRect(leftMargin + horizontalSeparation / 2 - 150, rowCount * verticalSpacing + 40, 200, 60))
        self.clkButton.setObjectName("clkButton")
        self.clkButton.setFont(font)
        self.clkButton.setText(_translate("MainWindow", "CLOCK"))
        self.clkButton.clicked.connect(self.clockTriggered)

    def runAssembler(self):
        if(platform.system() == 'Windows'):
            call("./python ./assembler/main.py ./assembler/code.asm")
        elif(platform.system() != 'Windows'):
            call("./python3 ./assembler/main.py ./assembler/code.asm")
#        call("pwd")

    def addAssembleButton(self):
        _translate = QtCore.QCoreApplication.translate
        font = QtGui.QFont()
        font.setFamily("Victor Mono")
        font.setPointSize(14)

        rowCount = int((len(self.bus._components)+1) / 2) + 1
        self.assembleButton = QtWidgets.QPushButton(self.centralwidget)
        self.assembleButton.setGeometry(QtCore.QRect(leftMargin + horizontalSeparation / 2 + 150 + 200, rowCount * verticalSpacing + 40, 200, 30))
        self.assembleButton.setObjectName("assembleButton")
        self.assembleButton.setFont(font)
        self.assembleButton.setText(_translate("MainWindow", "Run Assembler"))
        self.assembleButton.clicked.connect(self.runAssembler)

    def addResetButton(self):
        _translate = QtCore.QCoreApplication.translate
        font = QtGui.QFont()
        font.setFamily("Victor Mono")
        font.setPointSize(24)

        rowCount = int((len(self.bus._components)+1) / 2) + 1
        self.clkButton = QtWidgets.QPushButton(self.centralwidget)
        self.clkButton.setGeometry(QtCore.QRect(leftMargin + horizontalSeparation / 2 + 150, rowCount * verticalSpacing + 40, 200, 60))
        self.clkButton.setObjectName("rstButton")
        self.clkButton.setFont(font)
        self.clkButton.setText(_translate("MainWindow", "RESET"))
        self.clkButton.clicked.connect(self.resetTriggered)

    def buildBus(self):
        font = QtGui.QFont()
        font.setFamily("Victor Mono")
        font.setPointSize(24)
        label = QtWidgets.QLabel(self.centralwidget)
        label.setFont(font)
        label.setAutoFillBackground(True)
        label.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignVCenter)
        label.setObjectName("busLabel")
        label.setText("NORMAL")
      #  label.setStyleSheet("QLabel { background-color : red; }")
        label.setGeometry(QtCore.QRect(leftMargin + horizontalSeparation/2, topMargin, horizontalSeparation/2, 49))
        self.busLabel=label

        lcd = QtWidgets.QLCDNumber(self.centralwidget)
        lcd.setGeometry(QtCore.QRect(leftMargin + 35 + horizontalSeparation/2, 50 + topMargin, 91, 49))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(lcd.sizePolicy().hasHeightForWidth())
        lcd.setSizePolicy(sizePolicy)
        lcd.setFrameShape(QtWidgets.QFrame.NoFrame)
        lcd.setDigitCount(4)
        lcd.setMode(QtWidgets.QLCDNumber.Hex)
        lcd.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        lcd.setObjectName("bus")
        self.busLCD = lcd

    def buildComponent(self, componentIndex, startOffset):
        if (self.bus._components[componentIndex] == None):
            return
        verticalIncrement = int(componentIndex / 2)
        yPos = 120 + verticalSpacing * verticalIncrement + startOffset + topMargin

        label = QtWidgets.QLabel(self.centralwidget)
        if (componentIndex % 2):
            label.setGeometry(QtCore.QRect(leftMargin + horizontalSeparation, yPos, labelWidth, labelHeight))
            label.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        else:
            label.setGeometry(QtCore.QRect(leftMargin + lcdWidth, yPos, labelWidth, labelHeight))
            label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        font = QtGui.QFont()
        font.setFamily("Victor Mono")
        font.setPointSize(18)
        label.setFont(font)
        label.setAutoFillBackground(True)
        label.setObjectName("label_" + str(componentIndex))
        label.setText(self.bus._components[componentIndex].name)  
        if (hasattr(self.bus._components[componentIndex],"_loadFlags")):
            self.flagButtons.append(self.buildFlagButton(componentIndex, 0))
            self.flagButtons.append(self.buildFlagButton(componentIndex, 1))
        self.labels[componentIndex] = label
        lcd = QtWidgets.QLCDNumber(self.centralwidget)
        if (componentIndex % 2):
            lcd.setGeometry(QtCore.QRect(leftMargin + horizontalSeparation + labelWidth, yPos, lcdWidth, lcdHeight))
        else:
            lcd.setGeometry(QtCore.QRect(leftMargin, yPos, lcdWidth, lcdHeight))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(lcd.sizePolicy().hasHeightForWidth())
        lcd.setSizePolicy(sizePolicy)
        lcd.setFrameShape(QtWidgets.QFrame.NoFrame)
        lcd.setDigitCount(2)
        lcd.setMode(QtWidgets.QLCDNumber.Hex)
        lcd.setSegmentStyle(QtWidgets.QLCDNumber.Filled)
        lcd.setProperty("value", 42.0 + componentIndex*2)
        lcd.setObjectName("lcdNumber_" + str(componentIndex))
        self.lcds[componentIndex] = lcd
        pushButton = QtWidgets.QPushButton(self.centralwidget)
        if (componentIndex % 2):
            pushButton.setGeometry(QtCore.QRect(leftMargin + labelWidth + lcdWidth + horizontalSeparation, yPos + 10, editButtonWidth, 32))
        else:
            pushButton.setGeometry(QtCore.QRect(leftMargin - editButtonWidth, yPos + 10, editButtonWidth, 32))
        pushButton.setObjectName("pushButton_" + str(componentIndex))
        pushButton.clicked.connect(self.editButtonTapped)
        self.pushButtons[componentIndex] = pushButton


    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(831, 950)
        font = QtGui.QFont()
        font.setFamily("Victor Mono")
        font.setPointSize(14)
        MainWindow.setFont(font)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.labels = [None] * len(self.bus._components)
        self.busDriver = []
        self.lcds = [None] * len(self.bus._components)
        self.controlWords = [None] * len(self.bus._components) * 8
        self.pushButtons = [None] * len(self.bus._components)
        self.flagButtons = []
        self.buildBus()
        self.addClockButton()
        self.addResetButton()
        self.addAssembleButton()
        for i in range(len(self.bus._components)):
            if (self.bus._components[i] != None):
                for j in range(numberOfControlBits):  # number of control bits
                    rb = self.buildRadioButton(i,j,60)
                    self.controlWords[i * 8 + j] = self.buildRadioButton(i,j,60)
                self.buildComponent(i, 0)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 831, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionLoad_Microcode = QtWidgets.QAction(MainWindow)
        self.actionLoad_Microcode.setObjectName("actionLoad_Microcode")

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        # self.labels[0].setText(_translate("MainWindow", "REG_A"))
        # label_2.setText(_translate("MainWindow", "REG_B"))
        self.actionLoad_Microcode.setText(_translate("MainWindow", "Load Microcode"))

    def updateControlWords(self, bus):
        for c in range(len(bus._components)):
            if (bus._components[c] == None):
                return
            value = bus._components[c].controlWord
            for i in range(numberOfControlBits):
                index = c * numberOfControlBits + i
                radioButton = self.controlWords[index]
                radioButton.setChecked(Emulator.isKthBitSet(value, 7-i))

#testing
if __name__ == "__main__":
    bus = Emulator.Bus()
    bus.constructSystem()
    
    bus.componentReference['CTRL'].sendOutControlWords()
    
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.bus = bus
    ui.setupUi(MainWindow)
    MainWindow.show()
    ui.refresh()
    sys.exit(app.exec_())