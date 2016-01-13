#!/usr/bin/env python

#--------------------------------------------------------------------------------------------------
# File name   : 009_rgb_led_controller.py
# Description : Multi-threaded I/O program to read commands from stdin to control an RGB LED
# Author      : Dito Manavalan
# Date        : 2016/01/08
#--------------------------------------------------------------------------------------------------

#==================================================================
# Circuit Diagram
#==================================================================
# LED
#     Anode > 220 Resistor > GPIO Pin 1 (3.3V)
#     Cathode > GPIO Pin 11 (GPIO17)
#
# Apply HIGH to turn OFF, LOW to turn ON
#==================================================================
# Formulae and Notes
#==================================================================
# R = U / I = 3.3V / (5~20mA) = 165~660 = 220
#
# LED Pin Identification:
# Anode: Positive, Longer pin
# Cathode: Negative, Shorter pin, Pin near the flat edge
#==================================================================

import threading
import time
import rpimod.gpio.devicecontrol as GDC

# Configuration block - START

cntlrDeviceName = "RGB LED"
cntlrDeviceType = "RGB LED"
cntlrIOMode = GDC.OUTPUT_DEVICE
cntlrLogicState = GDC.ACTIVE_LOW
cntlrPWMFrequency = 100

#cntlrPin = 11                                                         # set pin # 11
cntlrPins = {'RED':11, 'GREEN':12, 'BLUE':13}

cntlrOnCommand = "ON"
cntlrOffCommand = "OFF"
cntlrAltCommand = "BLINK"
cntlrExitCommand = "EXIT"

cntlrCommand = "OFF"
cntlrPrevCommand = ""
cntlrColorCommand = ""
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
        #logger.debug('Starting %s', self.name)
        capture_input(self.name)
        #logger.debug('Exiting %s', self.name)

def capture_input(threadName):
    global cntlrInputCommandReadFlag
    global cntlrCommand
    global cntlrColorCommand

    global cntlrOnCommand
    global cntlrOffCommand
    global cntlrAltCommand
    global cntlrExitCommand

    while True:
        if cntlrInputCommandReadFlag == False:
            break
        rawCommand = raw_input(cntlrDeviceName + ":" + cntlrCommand.ljust(6) + " > ")
        if rawCommand.upper() in [cntlrOnCommand, cntlrOffCommand, cntlrAltCommand, cntlrExitCommand]:
            cntlrCommand = rawCommand.upper()
        elif rawCommand.upper() in GDC.RGB_COLOR_DICT:
            cntlrColorCommand = rawCommand.upper()
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
        #logger.debug('Starting %s', self.name)
        display_output(self.name)
        #logger.debug('Exiting %s', self.name)

def display_output(threadName):
    global cntlrName
    global cntlrDeviceName
    global cntlrLogicState
    global cntlrPin

    global cntlrInputCommandReadFlag
    global cntlrOutputCommandScanDelay
    global cntlrCommand
    global cntlrPrevCommand
    global cntlrColorCommand
    global cntlrBlinkDelay

    global cntlrOnCommand
    global cntlrOffCommand
    global cntlrAltCommand
    global cntlrExitCommand

    devCntlr = GDC.DeviceController(cntlrName)
    #dev = GDC.Device(cntlrDeviceName, cntlrDeviceType, cntlrIOMode, cntlrLogicState, devCntlr, cntlrPin)
    dev = GDC.RGBLedDevice(cntlrDeviceName, cntlrLogicState, devCntlr, cntlrPins, cntlrPWMFrequency)

    while True:
        #print "Current Command: " + cntlrCommand + "; Previous Command: " + cntlrPrevCommand + "\n"
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

        # apply color updates
        if cntlrColorCommand != "":
            #print "! Setting color to", cntlrColorCommand
            dev.set_color(GDC.RGB_COLOR_DICT[cntlrColorCommand])
            cntlrColorCommand = ""

        time.sleep(cntlrOutputCommandScanDelay)

    dev.close()
    devCntlr.close()

# Main program
print "[" + cntlrName + ": " + cntlrOnCommand + "/" + cntlrOffCommand + "/" + cntlrAltCommand + "/[COLOR]/" + cntlrExitCommand + "]"

# Create new threads
threadRead = inputThread(1, "Reader")
threadWrite = outputThread(2, "Writer")

# Start new Threads
threadRead.start()
threadWrite.start()
