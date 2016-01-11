#!/usr/bin/env python

#--------------------------------------------------------------------------------------------------
# File name   : devicecontrol.py
# Description : Generic GPIO device controller library
# Author      : Dito Manavalan
# Date        : 2015/12/03
#--------------------------------------------------------------------------------------------------

import logging
import RPi.GPIO as GPIO
import rpimod.math.functions as MATH

# Debugging block - START
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
# Debugging block - END

# Device type constants
INPUT_DEVICE = 1
OUTPUT_DEVICE = 2

# Circuit logic state constants
ACTIVE_HIGH = 1                                 # ACTIVE_HIGH circuit logic state indicates a GPIO.HIGH turns the device on
ACTIVE_LOW = 2                                  # ACTIVE_LOW circuit logic state indicates a GPIO.LOW turns the device on

# Default constants
DEFAULT_PWM_FREQ = 50
DEFAULT_CHANNEL = 11

# RGB LED constants
RGB_COLOR_LIST = ["Red", "Green", "Blue"]
RGB_COLOR_DICT = {
'Black'  :{'Red':000, 'Green':000, 'Blue':000},
'Gray'  :{'Red':128, 'Green':128, 'Blue':128},
'Red'    :{'Red':255, 'Green':000, 'Blue':000},
'Pink'   :{'Red':255, 'Green':192, 'Blue':203},
'Violet' :{'Red':238, 'Green':130, 'Blue':238},
'Purple' :{'Red':128, 'Green':000, 'Blue':128},
'Green'  :{'Red':000, 'Green':255, 'Blue':000},
'Yellow'  :{'Red':255, 'Green':255, 'Blue':000},
'Gold'  :{'Red':255, 'Green':215, 'Blue':000},
'Orange'  :{'Red':255, 'Green':165, 'Blue':000},
'Blue'   :{'Red':000, 'Green':000, 'Blue':255},
'Indigo' :{'Red':075, 'Green':000, 'Blue':130},
'Lavender' :{'Red':230, 'Green':230, 'Blue':250},
'Sky Blue' :{'Red':135, 'Green':206, 'Blue':235},
'Turquoise' :{'Red':064, 'Green':224, 'Blue':208},
'White'  :{'Red':255, 'Green':255, 'Blue':255}
}

class DeviceController(object):
    """
    A device controller that uses the GPIO module to control any electronic device 
    like an LED or Active Buzzer.
    It has the following attributes:
        name: A string representing the device controller's name
    """
    def __init__(self, name):
        self.name = name
        GPIO.setmode(GPIO.BOARD)                                          # Numbers pins by physical location            

    def setup(self, channel, channel_mode, initial_level):
        GPIO.setup(channel, channel_mode, initial=initial_level)          # Set pin, I/O mode and initial state as default

    def switch(self, channel, logic_level):
        GPIO.output(channel, logic_level)

    def PWM(self, channel, frequency):
        return GPIO.PWM(channel, frequency)

    def close(self):
        self.name = "Unknown"

    def __del__(self):
        self.close()
        GPIO.cleanup()                                                    # Release resource

class Device(object):
    """
    Any electronic device like an LED or Active Buzzer that can be controlled by the GPIO module.
    It has the following attributes:
        name: A string representing the device's name
        device_type: An string representing the device's type e.g. LED, Active Buzzer, etc.
        io_mode: An integer representing the device's input/output mode
        logic_state: An integer representing the device's circuit logic state
        controller: A DeviceController object used to control the device
        channel: An integer representing the GPIO channel or pin used by the device
        channel_mode: An integer representing the GPIO mode (GPIO.OUT/GPIO.IN) used by the device
        default_level: An integer representing the device's default state, determined by the logic_state
        level: An integer representing the device's current state
    """
    def __init__(self, name, device_type, io_mode, logic_state, controller, channel):
        self.name = name
        self.device_type = device_type
        self.io_mode = io_mode
        self.logic_state = logic_state
        self.controller = controller
        self.channel = channel

        if io_mode == INPUT_DEVICE:
            self.channel_mode = GPIO.IN
        elif io_mode == OUTPUT_DEVICE:
            self.channel_mode = GPIO.OUT
        else:
            self.channel_mode = -1
            raise RuntimeError('Invalid I/O mode specified.')
        if logic_state == ACTIVE_HIGH:
            self.default_level = GPIO.LOW
        elif logic_state == ACTIVE_LOW:
            self.default_level = GPIO.HIGH
        else:
            self.default_level = -1
            raise RuntimeError('Invalid circuit logic state specified.')
        self.controller.setup(self.channel, self.channel_mode, self.default_level)      # Set pin, I/O mode and initial state as default
        self.level = self.default_level

    def switch(self, switch_mode):
        if switch_mode == "ON":
            self.level = not self.default_level                           # device on
        elif switch_mode == "OFF":
            self.level = self.default_level                               # device off
        elif switch_mode == "TOGGLE":
            self.level = not self.level                                   # device toggle
        else:
            self.level = self.default_level                               # device off
        self.controller.switch(self.channel, self.level)

    def close(self):
        self.switch("OFF")
        self.name = "Unknown"
        self.device_type = "Unknown"

    def __del__(self):
        self.close()


class LedDevice(Device):
    """
    An LED electronic device that can be controlled by the GPIO module,
    derived from the Device base class.
    """
    def __init__(self, name, logic_state, controller, channel):
        super(LedDevice, self).__init__(name, "LED", OUTPUT_DEVICE, logic_state, controller, channel)

class ActiveBuzzerDevice(Device):
    """
    An Active Buzzer electronic device that can be controlled by the GPIO module,
    derived from the Device base class.
    """
    def __init__(self, name, logic_state, controller, channel):
        super(ActiveBuzzerDevice, self).__init__(name, "Active Buzzer", OUTPUT_DEVICE, logic_state, controller, channel)

class ColorChannel(object):
    """
    A color channel in an electronic device such as an RGB LED device.
    It has the following attributes:
        color: A string representing the channel's color
        value: An integer between 0 and 255 representing the color value
        channel: An integer representing the GPIO channel or pin used by the device
        frequency: An integer representing the PWM frequency of the GPIO channel in Hz
        PWM:
        duty_cycle(): A number between 0 and 100 representing the PWM duty cycle equivalent of the color value
    """
    def __init__(self, color, value, channel, frequency, PWM):
        logger.debug('ColorChannel.__init__: Executing for %s', color)
        self.color = color
        self.value = value
        self.channel = channel
        self.frequency = frequency
        self.PWM = PWM

    def duty_cycle(self, logic_state):
        logger.debug('ColorChannel.duty_cycle: Executing')
        if logic_state == ACTIVE_HIGH:
            return MATH.map(self.value, 0, 255, 0, 100)
        elif logic_state == ACTIVE_LOW:
            return 100 - MATH.map(self.value, 0, 255, 0, 100)
        else:
            raise RuntimeError('Invalid circuit logic state specified.')

class RGBLedDevice(Device):
    """
    An RGB LED electronic device that can be controlled by the GPIO module,
    derived from the Device base class.
    It has the following additional attributes:
    color_channels: A dictionary of ColorChannel objects representing the RGB channels
    """
    def __init__(self, name, logic_state, controller, channels, frequency=DEFAULT_PWM_FREQ):
        logger.debug('RGBLedDevice.__init__: Executing')
        super(RGBLedDevice, self).__init__(name, "RGB LED", OUTPUT_DEVICE, logic_state, controller, DEFAULT_CHANNEL)
        
        # Initialize and setup color channels
        self.color_channels = {}
        for color in RGB_COLOR_LIST:
            logger.debug('RGBLedDevice.__init__: Initializing %s color channel', color)
            self.controller.setup(channels[color], self.channel_mode, self.level)
            self.controller.switch(channels[color], self.level)
            current_PWM = self.controller.PWM(channels[color], frequency)
            self.color_channels[color] = ColorChannel(color, 0, channels[color], frequency, current_PWM)

    def switch(self, switch_mode):
        print "Switch mode: " + switch_mode
        print "Current level: " + str(self.level)
        print "GPIO.HIGH is " + str(GPIO.HIGH)
        self.display_color()
        if switch_mode == "ON":
            self.level = 1 - self.default_level                           # device on
            # Start PWM channels
            for color in RGB_COLOR_LIST:
                current_channel = self.color_channels[color]
                current_channel.PWM.start(current_channel.duty_cycle(self.logic_state))
                print color + ":" + str(current_channel.duty_cycle(self.logic_state))
        elif switch_mode == "OFF":
            self.level = self.default_level                               # device off
            # Stop PWM channels
            for color in RGB_COLOR_LIST:
                current_channel = self.color_channels[color]
                current_channel.PWM.stop()
                self.controller.switch(current_channel.channel, self.level)
        elif switch_mode == "TOGGLE":
            self.level = 1 - self.level                                  # device toggle
            if self.level == self.default_level:
                #print "Toggle: turning off\n"
                # Stop PWM channels
                for color in RGB_COLOR_LIST:
                    current_channel = self.color_channels[color]
                    current_channel.PWM.stop()
                    self.controller.switch(current_channel.channel, self.level)
            else:
                #print "Toggle: turning on\n"
                # Start PWM channels
                for color in RGB_COLOR_LIST:
                    current_channel = self.color_channels[color]
                    current_channel.PWM.start(current_channel.duty_cycle(self.logic_state))
        print "Switch mode: " + switch_mode
        print "Switched level: " + str(self.level)

    def set_color(self, values):
        # Set PWM channels
        for color in RGB_COLOR_LIST:
            self.color_channels[color].value = values[color]
            current_channel = self.color_channels[color]
            current_channel.PWM.ChangeDutyCycle(current_channel.duty_cycle(self.logic_state))

    def change_color(self, color, increment):
        # Retrieve current RGB values
        newColorValues = {}
        for colorIndex in RGB_COLOR_LIST:
            newColorValues[colorIndex] = self.color_channels[colorIndex].value

        # Set new RGB value
        newColorValue = newColorValues[color] + increment
        if newColorValue < 0:
            newColorValue = 0
        elif newColorValue > 255:
            newColorValue = 255
        newColorValues[color] = newColorValue

        self.set_color(newColorValues)

    def display_color(self):
        index=1
        print "[",
        for colorIndex in RGB_COLOR_LIST:
            if index != 1:
                print ",",
            print str(self.color_channels[colorIndex].value),
            index+=1
        print "]",