#!/usr/bin/env python

#-----------------------------------------------------------
# File name   : pilot_thread_io.py
# Description : Input/Output program to read input and
#               display output using different threads
# Author      : Dito
# Date        : 2015/11/24
#-----------------------------------------------------------

import rpi2lib.stdio.input as INPUT

inputStr = ''

print "Press any keys (x to exit): "

userInput = INPUT.getch.impl()
while userInput != 'x':
    inputStr += userInput
    userInput = INPUT.getch.impl()

print "You entered: " + inputStr