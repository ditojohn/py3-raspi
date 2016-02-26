#!/usr/bin/env python

import time
import rpimod.gpio.devicecontrol as GDC

# Configuration block - START

cntlrDeviceName = "RGB LED"
cntlrDeviceType = "RGB LED"
cntlrIOMode = GDC.OUTPUT_DEVICE
cntlrLogicState = GDC.ACTIVE_LOW
cntlrPWMFrequency = 100

#cntlrPin = 11                                                         # set pin # 11
cntlrPins = {'Red':11, 'Green':12, 'Blue':13}

# Configuration block - END

cntlrName = "RPi2 " + cntlrDeviceType + " Controller"

devCntlr = GDC.DeviceController(cntlrName)
dev = GDC.RGBLedDevice(cntlrDeviceName, cntlrLogicState, devCntlr, cntlrPins, cntlrPWMFrequency)
rawCommand = raw_input(" > ")
dev.switch("OFF")
rawCommand = raw_input(" > ")
dev.switch("ON")
rawCommand = raw_input(" > ")
dev.switch("ON")
rawCommand = raw_input(" > ")
dev.switch("OFF")
rawCommand = raw_input(" > ")
dev.switch("TOGGLE")
rawCommand = raw_input(" > ")
dev.switch("TOGGLE")

dev.close()
devCntlr.close()
