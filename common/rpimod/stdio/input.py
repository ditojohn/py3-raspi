#!/usr/bin/env python

#--------------------------------------------------------------------------------------------------
# File name   : input.py
# Description : Generic input handling library
# Author      : Dito Manavalan
# Date        : 2015/12/03
#--------------------------------------------------------------------------------------------------

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
