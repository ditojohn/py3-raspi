#!/usr/bin/env python

#--------------------------------------------------------------------------------------------------
# File name   : 002_active_buzzer_controller.py
# Description : Multi-threaded I/O program to read commands from stdin to control an active buzzer
# Author      : Dito Manavalan
# Date        : 2015/12/02
#--------------------------------------------------------------------------------------------------

#==================================================================
# Circuit Diagram
#==================================================================
# Active Buzzer
#     Anode > GPIO Pin 1 (3.3V)
#     Cathode > S8050 NPN Transistor - Collector
#                   Emitter > GPIO Pin 6 (GND)
#                   Base > 1k Resistor > GPIO Pin 11 (GPIO17)
#
# Apply LOW to turn OFF, HIGH to turn ON
#==================================================================
# Formulae and Notes
#==================================================================
# Active Buzzer Pin Identification:
# Anode: Positive, Longer pin, (+) Polarity marking
# Cathode: Negative, Shorter pin
#
# NPN Transistor Pin Identification:
# Facing the flat side with pins pointing downwards,
# Emitter: Left
# Base: Middle
# Collector: Right
#==================================================================

import threading
import time
import rpimod.gpio.devicecontrol as GDC

# Configuration block - START

cntlrDeviceName = "Active Buzzer"
cntlrDeviceType = "Active Buzzer"
cntlrIOMode = GDC.OUTPUT_DEVICE
cntlrLogicState = GDC.ACTIVE_HIGH
cntlrPin = 11                                                         # set pin # 11

cntlrOnCommand = "ON"
cntlrOffCommand = "OFF"
cntlrAltCommand = "BEEP"
cntlrExitCommand = "EXIT"

cntlrCommand = "OFF"
cntlrPrevCommand = ""
cntlrOutputCommandScanDelay = 0.5
cntlrBlinkDelay = 0.5

# Configuration block - END

cntlrName = "RPi2 " + cntlrDeviceType + " Controller"
cntlrInputCommandReadFlag = True

class inputThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        #print "Starting " + self.name + "\n"
        capture_input(self.name)
        #print "Exiting " + self.name + "\n"

def capture_input(threadName):
    global cntlrInputCommandReadFlag
    global cntlrCommand

    global cntlrOnCommand
    global cntlrOffCommand
    global cntlrAltCommand
    global cntlrExitCommand

    while True:
        if cntlrInputCommandReadFlag == False:
            break
        rawCommand = raw_input(cntlrDeviceName + ":" + cntlrCommand.ljust(6) + " > ").upper()
        if rawCommand in [cntlrOnCommand, cntlrOffCommand, cntlrAltCommand, cntlrExitCommand]:
            cntlrCommand = rawCommand
        else:
            print "! Unknown command", rawCommand
        if cntlrCommand == cntlrExitCommand:
            cntlrInputCommandReadFlag = False

class outputThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        #print "Starting " + self.name + "\n"
        display_output(self.name)
        #print "Exiting " + self.name + "\n"

def display_output(threadName):
    global cntlrName
    global cntlrDeviceName
    global cntlrDeviceType
    global cntlrIOMode
    global cntlrLogicState
    global cntlrPin

    global cntlrInputCommandReadFlag
    global cntlrOutputCommandScanDelay
    global cntlrCommand
    global cntlrPrevCommand    
    global cntlrBlinkDelay

    global cntlrOnCommand
    global cntlrOffCommand
    global cntlrAltCommand
    global cntlrExitCommand

    devCntlr = GDC.DeviceController(cntlrName)
    dev = GDC.Device(cntlrDeviceName, cntlrDeviceType, cntlrIOMode, cntlrLogicState, devCntlr, cntlrPin)

    while True:
        if cntlrInputCommandReadFlag == False:
            break
        elif cntlrCommand == cntlrOnCommand or cntlrCommand == cntlrOffCommand:
            if cntlrCommand != cntlrPrevCommand:
                dev.switch(cntlrCommand)
                cntlrPrevCommand = cntlrCommand
        elif cntlrCommand == cntlrAltCommand:
            while cntlrCommand == cntlrAltCommand:
                dev.switch("TOGGLE")
                cntlrPrevCommand = cntlrCommand
                time.sleep(cntlrBlinkDelay)
        else:
            dev.switch("OFF")
            cntlrPrevCommand = cntlrCommand
        time.sleep(cntlrOutputCommandScanDelay)
        cntlrPrevCommand = cntlrCommand

    dev.close()
    devCntlr.close()

# Main program
print "[" + cntlrName + ": " + cntlrOnCommand + "/" + cntlrOffCommand + "/" + cntlrAltCommand + "/" + cntlrExitCommand + "]"

# Create new threads
threadRead = inputThread(1, "Reader")
threadWrite = outputThread(2, "Writer")

# Start new Threads
threadRead.start()
threadWrite.start()
