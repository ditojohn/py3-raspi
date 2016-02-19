#!/usr/bin/env python

#--------------------------------------------------------------------------------------------------
# File name   : input.py
# Description : Generic input handling library
# Author      : Dito Manavalan
# Date        : 2015/12/03
#--------------------------------------------------------------------------------------------------

import sys, termios, time
#--------------------------------------------------------------------------------------------------
# Class       : _Getch
# Function    : Gets a single character from standard input.  Does not echo to the screen.
# Reference   : http://code.activestate.com/recipes/134892-getch-like-unbuffered-character-reading-from-stdin/
# Usage       : import rpi2lib.stdio.input as INPUT
#               userInput = INPUT.getch.impl()
#--------------------------------------------------------------------------------------------------

class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

getch = _Getch()

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
    set_term_input(True)
    print prompt ,
    userKeypress = getch()
    set_term_input(False)
    print ""
    return userKeypress

def get_input(prompt):
    time.sleep(0.05)                                     # Sleep to allow pending I/O operations to complete    
    set_term_input(True)
    userInput = raw_input(prompt).strip()
    set_term_input(False)
    return userInput
