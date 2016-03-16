#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : textparser.py
# Description : Generic module to perform text parsing functions
# Author      : Dito Manavalan
# Date        : 2016/03/15
#--------------------------------------------------------------------------------------------------

import sys
import re

sys.path.insert(0, "../../..")
import common.rpimod.stdio.output as coutput

################################################################
# Internal variables
################################################################

# Set to True to turn debug messages on
ERR_DEBUG = False

UNICODE_EMPTY_STR = unicode("", 'utf-8')
UNICODE_NEWLINE_STR = unicode("\n", 'utf-8')


def find_enclosed_text(rawStartPattern, rawEndPattern, text):
    _FUNC_NAME_ = "find_enclosed_text"

    regexNonGreedyJoiner = r'(.*?)'
    rawSearchPattern = rawStartPattern + regexNonGreedyJoiner + rawEndPattern

    enclosedTextMatches = []
    matches = re.finditer(rawSearchPattern, text)
    for match in matches:
        enclosedTextMatches.append(match.group(1))

    return enclosedTextMatches


def cleanse_text(rawText, rawTextPatterns, rawInnerTextPatterns, rawOuterTextPatterns ):
    _FUNC_NAME_ = "cleanse_text"

    DEBUG_VAR="rawText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(rawText)))

    cleansedText = rawText

    DEBUG_VAR="cleansedText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(cleansedText)))

    cleanseTextPatterns = rawTextPatterns
    cleanseInnerTextPatterns = rawInnerTextPatterns
    cleanseOuterTextPatterns = rawOuterTextPatterns

    # Cleanse text patterns
    for pattern in cleanseTextPatterns:
        cleansedText = re.sub(pattern, UNICODE_EMPTY_STR, cleansedText)

    # Cleanse inner text surrounded by text patterns
    for enclosure in cleanseInnerTextPatterns:
        DEBUG_VAR="enclosure"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(enclosure)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        pattern = r'(' + enclosure[0] + r').*?(' + enclosure[1] + r')'
        cleansedText = re.sub(pattern, r'\g<1>\g<2>', cleansedText)

    # Cleanse outer text patterns preserving enclosed contents
    for enclosure in cleanseOuterTextPatterns:
        DEBUG_VAR="enclosure"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(enclosure)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        pattern = enclosure[0] + r'(.*?)' + enclosure[1]
        cleansedText = re.sub(pattern, r'\g<1>', cleansedText)

    outputText = cleansedText
    return outputText


########################################################################
# Debugging Commands
########################################################################

#rawText = "<tag1>apple</tag1><tag2>orange</tag2><tag3>banana</tag3>"
#print rawText
#
#cleanText = cleanse_text(rawText, [r'tag1'], [[r'<tag2>', r'</tag2>']], [[r'<tag3>', r'</tag3>']])
#print cleanText

