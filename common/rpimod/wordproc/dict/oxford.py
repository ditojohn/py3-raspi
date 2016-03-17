#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : oxford.py
# Description : Dictionary lookup functions sourcing from Oxford
# Author      : Dito Manavalan
# Date        : 2016/03/15
#--------------------------------------------------------------------------------------------------

################################################################
# Source: Oxford Dictionaries
# Sample Search URL: http://www.oxforddictionaries.com/us/definition/american_english/test?searchDictCode=all
# Sample Pronunciation URL: http://www.oxforddictionaries.com/us/media/american_english/us_pron/t/tes/test_/test__us_1.mp3
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
    cdict.DICT_SOURCE_NAME = unicode("Oxford Dictionaries", 'utf-8')
    cdict.DICT_ENTRY_URL = unicode("http://www.oxforddictionaries.com/us/definition/american_english/{WORD}?searchDictCode=all", 'utf-8')
    cdict.DICT_AUDIO_URL = unicode("{PATH}", 'utf-8')

    cdict.DICT_CLEAN_TEXT_PATTERNS = [
    u'\xb7',
    r'<span class="punctuation">'
    ]
    cdict.DICT_CLEAN_INNER_TEXT_PATTERNS = []
    cdict.DICT_CLEAN_OUTER_TEXT_PATTERNS = [
    [r'<em>', r'</em>']
    ]

    # The dictionary definition line is identified by the HTML tag '<span class="definition">...</span>'
    # The pronunciation audio line is identified by the HTML tag '<div class="sound audio_play_button icon-audio" data-src-mp3="http://www.oxforddictionaries.com/us/media/american_english/us_pron/c/clo/cloud/cloud__us_1.mp3"'
    # The pronunciation audio header word is identified by the HTML tag '<span data-dobid="hdw">'
    cdict.DICT_MARKER_DEFINITION = [
    [r'<span class="definition">\s*', r'[:]*</span>']
    ]
    cdict.DICT_MARKER_PRONUNCIATION_URL = [r'data-src-mp3="', r'"']
    cdict.DICT_MARKER_PRONUNCIATION_WORD = [r'<h2 class="pageTitle">', r'\n</h2>']


def get_dictionary_source():
    _FUNC_NAME_ = "get_dictionary_source"
    initialize_source()
    return cdict.get_dictionary_source()


def get_dictionary_entry(connectionPool, word):
    _FUNC_NAME_ = "get_dictionary_entry"
    initialize_source()
    return cdict.get_dictionary_entry(connectionPool, word)


def parse_word_definition(word, entryText):
    _FUNC_NAME_ = "parse_word_definition"
    initialize_source()
    return cdict.parse_word_definition(word, entryText)


def parse_word_clip(word, entryText):
    _FUNC_NAME_ = "parse_word_clip"
    initialize_source()
    return cdict.parse_word_clip(word, entryText)

