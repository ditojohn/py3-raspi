#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : output.py
# Description : Generic output handling library
# Author      : Dito Manavalan
# Date        : 2016/01/28
#--------------------------------------------------------------------------------------------------

import unicodedata
import math
import logging

# Set to True to turn debug messages on
ERR_DEBUG = False

# Display a list as evenly spaced columns
OUT_MARGIN_WIDTH = 4                                    # set margin width to 4 characters

def visual_len(word):
    visual_word = unicodedata.normalize('NFKD', word).encode('ASCII', 'ignore')
    # Add back special characters to determine final visual length
    rlen = len(visual_word)
    rlen = rlen + word.count(u'ˈ') + word.count(u'ˌ')
    rlen = rlen + word.count(u'ə') + word.count(u'ᵊ')
    rlen = rlen + word.count(u'œ') + word.count(u'ᵫ')
    rlen = rlen + word.count(u'ŋ')
    rlen = rlen + word.count(u'•') + word.count(u'√')
    
    return rlen

def columnize(elementList, numCols):
    _FUNC_NAME_ = "columnize"
    elementCount = len(elementList)
    colCount = numCols
    rowCount = int(math.ceil(float(elementCount)/float(colCount)))

    elementMargin = OUT_MARGIN_WIDTH                               
    columnizedList = []

    if elementCount > 0:
        elementMaxLength = max([visual_len(element) for element in elementList])
        DEBUG_VAR="elementMaxLength"
        print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, eval(DEBUG_VAR)))

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
            print col,
        print ""

def print_columnized_slice(elementList, sliceIndexList, numCols):
    slicedList = []
    for index in sliceIndexList:
        slicedList.append(elementList[index])

    print_columnized_list(slicedList, numCols)

def multiline_text(elementList):
    textList = u""

    for index, item in enumerate(elementList):
        if index == 0:
            textList = item
        else:
            textList = textList + u"\n" + item

    return textList

def coalesce(*args):
    for arg in args:
        if arg != u"":
            return arg

    return None

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
        msgText = unicode(msg, 'utf-8')
    else:
        msgText = msg

    print unicode("{colorOn}{text}{colorOff}", 'utf-8').format(colorOn=get_term_color(color, 'normal', 'normal'), text=msgText, colorOff=get_term_color('normal', 'normal', 'normal'))

def print_err (msg):
    print_color ('red', 'ERROR: ' + msg)

def print_warn (msg):
    print_color ('yellow', 'WARNING: ' + msg)

def print_tip (msg):
    print_color ('magenta', 'TIP: ' + msg)

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

