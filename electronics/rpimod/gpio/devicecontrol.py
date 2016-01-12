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
logger.setLevel(logging.INFO)
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
'OFF'  :{'Red':000, 'Green':000, 'Blue':000},
'ON'  :{'Red':255, 'Green':255, 'Blue':255},
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
        logger.debug('DeviceController.setup: Executing for channel %s', str(channel))
        GPIO.setup(channel, channel_mode, initial=initial_level)          # Set pin, I/O mode and initial state as default

    def switch(self, channel, logic_level):
        logger.debug('DeviceController.switch: Switching channel %s to %s', str(channel), str(logic_level))
        GPIO.output(channel, logic_level)

    def PWM(self, channel, frequency):
        logger.debug('DeviceController.PWM: Executing for channel %s', str(channel))
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
        logger.debug('RGBLedDevice.__init__: Executing [GPIO.HIGH is %s; GPIO.LOW is %s]', str(GPIO.HIGH), str(GPIO.LOW))
        super(RGBLedDevice, self).__init__(name, "RGB LED", OUTPUT_DEVICE, logic_state, controller, DEFAULT_CHANNEL)
        
        # Initialize and setup color channels
        logger.debug('RGBLedDevice.__init__: Current level is %s', str(self.level))
        self.color_channels = {}
        for color in RGB_COLOR_LIST:
            logger.debug('RGBLedDevice.__init__: Initializing %s color channel', color)
            # Set channel to output mode
            self.controller.setup(channels[color], self.channel_mode, self.level)
            # Switch channel off
            self.controller.switch(channels[color], self.level)
            # Set PWM for channel
            current_PWM = self.controller.PWM(channels[color], frequency)
            # Set color channel
            self.color_channels[color] = ColorChannel(color, 0, channels[color], frequency, current_PWM)
            # The following section is to be used when the color of the RGB LED needs to be adjusted via PWM
            #logger.debug('RGBLedDevice.__init__: Starting PWM with duty cycle %s', self.color_channels[color].duty_cycle(self.logic_state))
            #self.color_channels[color].PWM.start(self.color_channels[color].duty_cycle(self.logic_state))


    def switch_off(self):
        logger.debug('RGBLedDevice.switch_off: Current RGB value is (%s,%s,%s)', str(self.color_channels['Red'].value), str(self.color_channels['Green'].value), str(self.color_channels['Blue'].value))
        logger.debug('RGBLedDevice.switch_off: Current RGB duty cycle is (%s,%s,%s)', str(self.color_channels['Red'].duty_cycle(self.logic_state)), str(self.color_channels['Green'].duty_cycle(self.logic_state)), str(self.color_channels['Blue'].duty_cycle(self.logic_state)))

        self.level = self.default_level                               # device off
        logger.debug('RGBLedDevice.switch_off: Switched level is %s', str(self.level))

        for color in RGB_COLOR_LIST:
            current_channel = self.color_channels[color]
            # The following section is to be used when the color of the RGB LED needs to be adjusted via PWM
            #logger.debug('RGBLedDevice.switch: Stopping PWM for %s channel', color)
            #current_channel.PWM.stop() # Not required to stop PWM
            #self.set_color(RGB_COLOR_DICT['OFF'])
            # The following section is to be used when the RGB LED has to be operated in ON/OFF mode
            self.controller.switch(current_channel.channel, self.level)

    def switch_on(self):
        logger.debug('RGBLedDevice.switch_on: Current RGB value is (%s,%s,%s)', str(self.color_channels['Red'].value), str(self.color_channels['Green'].value), str(self.color_channels['Blue'].value))
        logger.debug('RGBLedDevice.switch_on: Current RGB duty cycle is (%s,%s,%s)', str(self.color_channels['Red'].duty_cycle(self.logic_state)), str(self.color_channels['Green'].duty_cycle(self.logic_state)), str(self.color_channels['Blue'].duty_cycle(self.logic_state)))

        self.level = 1 - self.default_level                           # device on
        logger.debug('RGBLedDevice.switch_on: Switched level is %s', str(self.level))
        
        for color in RGB_COLOR_LIST:
            current_channel = self.color_channels[color]
            # The following section is to be used when the color of the RGB LED needs to be adjusted via PWM
            #logger.debug('RGBLedDevice.switch_on: Starting PWM for %s channel', color)
            #current_channel.PWM.start(current_channel.duty_cycle(self.logic_state))
            #self.set_color(RGB_COLOR_DICT['ON'])
            # The following section is to be used when the RGB LED has to be operated in ON/OFF mode
            self.controller.switch(current_channel.channel, self.level)

    def switch(self, switch_mode):
        logger.debug('RGBLedDevice.switch: Executing in %s mode', switch_mode)
        logger.debug('RGBLedDevice.switch: Current level is %s', str(self.level))
        logger.debug('RGBLedDevice.switch: Current RGB value is (%s,%s,%s)', str(self.color_channels['Red'].value), str(self.color_channels['Green'].value), str(self.color_channels['Blue'].value))

        if switch_mode == "ON":
            self.switch_on()
        elif switch_mode == "OFF":
            self.switch_off()
        elif switch_mode == "TOGGLE":
            if self.level == self.default_level:
                self.switch_on()
            else:
                self.switch_off()
    
    def set_color(self, values):
        # Set PWM channels
        for color in RGB_COLOR_LIST:
            self.color_channels[color].value = values[color]
            self.color_channels[color].PWM.ChangeDutyCycle(self.color_channels[color].duty_cycle(self.logic_state))

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
        print "RGB (",
        for colorIndex in RGB_COLOR_LIST:
            if index != 1:
                print ",",
            print str(self.color_channels[colorIndex].value),
            index+=1
        print ")",