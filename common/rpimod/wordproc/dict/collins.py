#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : collins.py
# Description : Dictionary lookup functions sourcing from Collins
# Author      : Dito Manavalan
# Date        : 2016/03/15
#--------------------------------------------------------------------------------------------------

################################################################
# Source: Collins Dictionary
# Sample Search URL: http://www.collinsdictionary.com/dictionary/american/test
# Sample Pronunciation URL: http://www.collinsdictionary.com/sounds/e/en_/en_us/en_us_test.mp3
################################################################

import sys
import re

#sys.path.insert(0, "/home/pi/projects/raspi")
sys.path.insert(0, "../../../..")
import common.rpimod.stdio.output as coutput
import common.rpimod.wordproc.dict.generic as cdict

################################################################
# Internal variables
################################################################

# Set to True to turn debug messages on
ERR_DEBUG = False


def initialize_source():
    cdict.DICT_SOURCE_NAME = unicode("Collins American English Dictionary", 'utf-8')
    cdict.DICT_ENTRY_URL = unicode("http://www.collinsdictionary.com/dictionary/american/{WORD}", 'utf-8')
    cdict.DICT_AUDIO_URL = unicode("http://www.collinsdictionary.com{PATH}", 'utf-8')

    cdict.DICT_CLEAN_TEXT_PATTERNS = []
    cdict.DICT_CLEAN_INNER_TEXT_PATTERNS = []
    cdict.DICT_CLEAN_OUTER_TEXT_PATTERNS = []

    # The dictionary definition line is identified by the HTML tag '<span class="def">....</span>'
    # The pronunciation audio line is identified by the HTML tag 'data-src-mp3="/sounds/e/en_/en_us/en_us_cloud.mp3"'
    # The pronunciation audio header word is identified by the HTML tag '<h1 class="orth h1_entry">cloud<'
    cdict.DICT_MARKER_DEFINITION = [
    [r'<span class="def">\s*', r'\s*</span>']
    ]
    cdict.DICT_MARKER_PRONUNCIATION_URL = [r'data-src-mp3="', r'"']
    cdict.DICT_MARKER_PRONUNCIATION_WORD = [r'<h1 class="orth h1_entry">', r'<']


def get_dictionary_source():
    _FUNC_NAME_ = "get_dictionary_source"

    initialize_source()
    DEBUG_VAR="cdict.DICT_SOURCE_NAME"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(cdict.DICT_SOURCE_NAME)))
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

    return cdict.get_dictionary_source()


def get_dictionary_entry(connectionPool, word):
    _FUNC_NAME_ = "get_dictionary_entry"
    return cdict.get_dictionary_entry(connectionPool, word)


def parse_word_definition(word, entryText):
    _FUNC_NAME_ = "parse_word_definition"
    return cdict.parse_word_definition(word, entryText)


def parse_word_clip(word, entryText):
    _FUNC_NAME_ = "parse_word_clip"
    return cdict.parse_word_clip(word, entryText)

