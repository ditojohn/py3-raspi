#!/usr/bin/env python

#--------------------------------------------------------------------------------------------------
# File name   : input.py
# Description : Generic input handling library
# Author      : Dito Manavalan
# Date        : 2015/12/03
#--------------------------------------------------------------------------------------------------

import sys, termios, time, getch

def set_term_echo(fd, enabled):
    # Save current terminal attributes
    [iflag, oflag, cflag, lflag, ispeed, ospeed, cc] = termios.tcgetattr(fd)
    if enabled:
        lflag |= termios.ECHO               # Turn echo on
    else:
        lflag &= ~termios.ECHO              # Turn echo off
    # Set new terminal attributes
    termios.tcsetattr(fd, termios.TCSANOW, [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])

def set_term_input(enabled):
    if enabled:
        set_term_echo(sys.stdin, True)                   # Turn echo on
        termios.tcflow(sys.stdin, termios.TCION)         # Resume input
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)    # Flush queued data
    else:
        set_term_echo(sys.stdin, False)                  # Turn echo off
        termios.tcflow(sys.stdin, termios.TCIOFF)        # Suspend input

def get_keypress(prompt):
    time.sleep(0.05)                                     # Sleep to allow pending I/O operations to complete
    print(prompt, end='', flush=True)
    set_term_input(True)
    userKeypress = getch.getch()
    set_term_input(False)
    print("")
    return userKeypress

def get_input(prompt):
    time.sleep(0.05)                                     # Sleep to allow pending I/O operations to complete    
    set_term_input(True)
    userInput = input(prompt).strip()
    set_term_input(False)
    return userInput
