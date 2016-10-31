#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : output.py
# Description : Generic output handling library
# Author      : Dito Manavalan
# Date        : 2016/01/28
#--------------------------------------------------------------------------------------------------

import math
import logging

# Display a list as evenly spaced columns
OUT_MARGIN_WIDTH = 4                                    # set margin width to 4 characters

def columnize(list, numCols):
    elementCount = len(list)
    colCount = numCols
    rowCount = int(math.ceil(float(elementCount)/float(colCount)))

    elementMargin = OUT_MARGIN_WIDTH                               
    columnizedList = []

    if len(list) > 0:
        elementMaxLength = max([len(element) for element in list])

        for rowIndex in range(0, rowCount):
            row = []
            elementIndex = rowIndex
            for colIndex in range(0, colCount):
                if elementIndex < elementCount:
                    row.append(list[elementIndex].ljust(elementMaxLength + elementMargin, ' '))
                    elementIndex += rowCount
            columnizedList.append(row)

    return columnizedList

def print_columnized_list(list, numCols):
    columnizedList = columnize(list, numCols)

    for row in columnizedList:
        for col in row:
            print col,
        print ""

def print_columnized_slice(list, sliceIndexList, numCols):
    slicedList = []
    for index in sliceIndexList:
        slicedList.append(list[index])

    print_columnized_list(slicedList, numCols)

def multiline_text(list):
    textList = u""

    for index, item in enumerate(list):
        if index == 0:
            textList = item
        else:
            textList = textList + u"\n" + item

    return textList


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

def print_err (msg):
    print "{colorOn}{header}{text}{colorOff}".format(colorOn=get_term_color('red', 'normal', 'normal'), header="ERROR: ", text=msg, colorOff=get_term_color('normal', 'normal', 'normal'))

def print_warn (msg):
    print "{colorOn}{header}{text}{colorOff}".format(colorOn=get_term_color('yellow', 'normal', 'normal'), header="WARNING: ", text=msg, colorOff=get_term_color('normal', 'normal', 'normal'))

def print_tip (msg):
    print "{colorOn}{header}{text}{colorOff}".format(colorOn=get_term_color('yellow', 'normal', 'inverse'), header="TIP: ", text=msg, colorOff=get_term_color('normal', 'normal', 'normal'))

def print_color (color, msg):
    print "{colorOn}{text}{colorOff}".format(colorOn=get_term_color(color, 'normal', 'normal'), text=msg, colorOff=get_term_color('normal', 'normal', 'normal'))

# Logging and debugging
# Usage:
# import common.rpimod.stdio.output as coutput
# SB_ERR_DEBUG = True
# To print debug statements:
# _FUNC_NAME_ = "function_name"
# DEBUG_VAR="searchWord"
# coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "WATCH: {0} :: {1}".format(DEBUG_VAR, eval(DEBUG_VAR)))

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.CRITICAL)

def print_debug (debugEnabled, context, msg):
    if debugEnabled:
        logger.setLevel(logging.DEBUG)
        logger.debug('[%s] %s', context, msg)
        logger.setLevel(logging.CRITICAL)

