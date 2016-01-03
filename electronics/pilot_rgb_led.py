#!/usr/bin/env python

import rpi2lib.gpio.devicecontrol as GDC
import time

# Configuration block - START

cntlrDeviceName = "RGB LED"
cntlrDeviceType = "RGB LED"
cntlrIOMode = GDC.OUTPUT_DEVICE
cntlrLogicState = GDC.ACTIVE_LOW
cntlrPin = 11                                                         # set pin # 11

cntlrOnCommand = "ON"
cntlrOffCommand = "OFF"
cntlrAltCommand = "BLINK"
cntlrExitCommand = "EXIT"

cntlrCommand = "OFF"
cntlrOutputCommandScanDelay = 0.5
cntlrBlinkDelay = 0.5

rgbChannels = {'Red':11, 'Green':12, 'Blue':13}
rgbFrequency = 50

# Configuration block - END

cntlrName = "RPi2 " + cntlrDeviceType + " Controller"
cntlrInputCommandReadFlag = True

devCntlr = GDC.DeviceController(cntlrName)
dev = GDC.RGBLedDevice(cntlrDeviceName, cntlrLogicState, devCntlr, rgbChannels, rgbFrequency)
dev.switch("ON")

colors = list(GDC.RGB_COLOR_DICT.keys())
colors.sort()
for name in colors:
    print name
    dev.set_color(GDC.RGB_COLOR_DICT[name])
    time.sleep(3)

dev.switch("OFF")
dev.close()
devCntlr.close()
