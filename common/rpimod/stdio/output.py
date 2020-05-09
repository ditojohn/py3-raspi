#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : output.py
# Description : Generic output handling library
# Author      : Dito Manavalan
# Date        : 2016/01/28
#--------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------
# Reference:
# sys._getframe: https://docs.python.org/2/library/sys.html?highlight=_getframe#sys._getframe
#--------------------------------------------------------------------------------------------------

import os
import sys
import unicodedata
import math
import re
import logging

# Set to True to turn debug messages on
#APP_DEBUG_MODE_ENABLED = True
APP_DEBUG_MODE_ENABLED = False

# Environment variable name for identifying debug mode
DEBUG_MODE_VARNAME = "APP_DEBUG_MODE_ENABLED"

# Display a list as evenly spaced columns
OUT_MARGIN_WIDTH = 4                                    # set margin width to 4 characters

CHR_NEWLINE = "\n"
CHR_EMPTY_STRING = ""
CHR_WORD_DELIMITER = ";"


def visual_len(word):
    visual_word = unicodedata.normalize('NFKD', word).encode('ASCII', 'ignore')
    # Add back special characters to determine final visual length
    rlen = len(visual_word)
    rlen = rlen + word.count('ˈ') + word.count('ˌ')
    rlen = rlen + word.count('ə') + word.count('ᵊ')
    rlen = rlen + word.count('œ') + word.count('ᵫ')
    rlen = rlen + word.count('ŋ')
    rlen = rlen + word.count('•') + word.count('√')
    
    return rlen

def columnize(elementList, numCols):
    elementCount = len(elementList)
    colCount = numCols
    rowCount = int(math.ceil(float(elementCount)/float(colCount)))

    elementMargin = OUT_MARGIN_WIDTH                               
    columnizedList = []

    if elementCount > 0:
        elementMaxLength = max([visual_len(element) for element in elementList])

        for rowIndex in range(0, rowCount):
            row = []
            elementIndex = rowIndex
            for colIndex in range(0, colCount):
                if elementIndex < elementCount:
                    elementLength = visual_len(elementList[elementIndex])
                    elementPadLength = elementMaxLength + elementMargin - elementLength
                    row.append(elementList[elementIndex] + ' ' * elementPadLength)
                    elementIndex += rowCount
            columnizedList.append(row)

    return columnizedList

def print_columnized_list(elementList, numCols):
    columnizedList = columnize(elementList, numCols)

    for row in columnizedList:
        for col in row:
            print(col, end=' ')
        print("")

def print_columnized_slice(elementList, sliceIndexList, numCols):
    slicedList = []
    for index in sliceIndexList:
        slicedList.append(elementList[index])

    print_columnized_list(slicedList, numCols)

def multiline_text(elementList):
    textList = ""

    for index, item in enumerate(elementList):
        if index == 0:
            textList = item
        else:
            textList = textList + "\n" + item

    return textList

def coalesce(*args):
    for arg in args:
        if arg != "":
            return arg

    return None

def normalize(word):

    wordToken = word
    wordToken = unicodedata.normalize('NFKD', wordToken)
   
    return wordToken

def tokenize(word):

    wordToken = word
    wordToken = unicodedata.normalize('NFKD', wordToken.lower())
    wordToken = re.sub('[- ]', CHR_EMPTY_STRING, wordToken)
   
    return wordToken

# Print to the terminal in color. References:
# https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_codes
# http://kishorelive.com/2011/12/05/printing-colors-in-the-terminal/

termColors = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
termEffects = ['bold', 'underline', 'blink', 'inverse', 'conceal']

termSGRCodes = {

    'prefix':    "\033[",
    'suffix':    "m",

    'normal':    "0",
    'bold':      "1",
    'underline': "4",
    'blink':     "5",
    'inverse':   "7",
    'conceal':   "8",

    'foreground': {

        'black':     "30",
        'red':       "31",
        'green':     "32",
        'yellow':    "33",
        'blue':      "34",
        'magenta':   "35",
        'cyan':      "36",
        'white':     "37"
    },

    'background': {

        'black':     "40",
        'red':       "41",
        'green':     "42",
        'yellow':    "43",
        'blue':      "44",
        'magenta':   "45",
        'cyan':      "46",
        'white':     "47"
    }   
}

def get_term_color (textColor, backgroundColor, effect):
    colorCode = termSGRCodes['prefix']
    
    if effect in termEffects:
        colorCode = colorCode + termSGRCodes[effect]
    else:
        colorCode = colorCode + termSGRCodes['normal']

    if textColor in termColors:
        colorCode = colorCode + ";" + termSGRCodes['foreground'][textColor]
    else:
        colorCode = colorCode + ";" + termSGRCodes['normal']

    if backgroundColor in termColors:
        colorCode = colorCode + ";" + termSGRCodes['background'][backgroundColor]

    colorCode = colorCode + termSGRCodes['suffix']

    return colorCode

def print_color (color, msg):

    if isinstance(msg, str):
        msgText = msg
    else:
        msgText = msg

    print("{colorOn}{text}{colorOff}".format(colorOn=get_term_color(color, 'normal', 'normal'), text=msgText, colorOff=get_term_color('normal', 'normal', 'normal')))

def print_err (msg):
    print_color ('red', 'ERROR: ' + msg)

def print_warn (msg):
    print_color ('yellow', 'WARNING: ' + msg)

def print_tip (msg):
    print_color ('magenta', 'TIP: ' + msg)

#################################################################################
# Logging and debugging
# Usage:
# import common.rpimod.stdio.output as coutput
# APP_DEBUG_MODE_ENABLED = True
# To print debug statements:
# coutput.print_debug("Executing step #1")
# coutput.print_watcher('variable_1')
#################################################################################

def addLoggingLevel(levelName, levelNum, methodName=None):
    # Reference: https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present 

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
       raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
       raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
       raise AttributeError('{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)


logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.CRITICAL)

# START: "TRACE" debug level
TRACE_DEBUG_LEVEL_NUM = logging.DEBUG - 5
TRACE_DEBUG_LEVEL_NAME = "TRACE"
addLoggingLevel(TRACE_DEBUG_LEVEL_NAME, TRACE_DEBUG_LEVEL_NUM)
# END: "TRACE" debug level

def print_debug (msg):
    # Set frame as previous code frame (calling function)
    frame = sys._getframe(1)    
    # Set context as name of calling function
    module = os.path.splitext(os.path.basename(frame.f_code.co_filename))[0]
    function = frame.f_code.co_name
    context = "{0}.{1}".format(module, function)
            
    try:
        debugEnabled = eval(DEBUG_MODE_VARNAME, frame.f_globals, frame.f_locals)
        if debugEnabled:
            logger.setLevel(logging.DEBUG)
            logger.debug('[%s] %s', context, msg)
            logger.setLevel(logging.CRITICAL)
    except:
        print_err("Debug mode [{1}] not set for {0}".format(context, DEBUG_MODE_VARNAME))

def print_watcher (expr):
    # Set frame as previous code frame (calling function)
    frame = sys._getframe(1)    
    # Set context as name of calling function
    module = os.path.splitext(os.path.basename(frame.f_code.co_filename))[0]
    function = frame.f_code.co_name
    context = "{0}.{1}".format(module, function)
            
    try:
        debugEnabled = eval(DEBUG_MODE_VARNAME, frame.f_globals, frame.f_locals)
        if debugEnabled:
            logger.setLevel(logging.TRACE)
            logger.trace('[%s] %s :: %s :: %s', context, expr, type(eval(expr, frame.f_globals, frame.f_locals)), repr(eval(expr, frame.f_globals, frame.f_locals)))
            logger.setLevel(logging.CRITICAL)
    except:
        print_err("Debug mode [{1}] not set for {0}".format(context, DEBUG_MODE_VARNAME))
