#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : google.py
# Description : Dictionary lookup functions sourcing from Google
# Author      : Dito Manavalan
# Date        : 2016/02/20
#--------------------------------------------------------------------------------------------------

################################################################
# Source: Google
# Sample Search URL: http://www.google.com/search?q=define+test
# Sample Pronunciation URL: http://ssl.gstatic.com/dictionary/static/sounds/de/0/test.mp3
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
    cdict.DICT_SOURCE_NAME = unicode("Google", 'utf-8')
    cdict.DICT_ENTRY_URL = unicode("http://www.google.com/search?hl=en&q=define+{WORD}", 'utf-8')
    cdict.DICT_AUDIO_URL = unicode("http:{PATH}", 'utf-8')

    cdict.DICT_CLEAN_TEXT_PATTERNS = [
    u'\xb7',
    u'&quot;',
    r'<script.*?>.*?</script>',
    r'<style.*?>.*?</style>'
    ]
    cdict.DICT_CLEAN_INNER_TEXT_PATTERNS = []
    cdict.DICT_CLEAN_OUTER_TEXT_PATTERNS = [
    [r'<b>', r'</b>'],
    [r'<i>', r'</i>'],
    [r'<u>', r'</u>']
    ]

    # The Google define dictionary entry is identified by the HTML tag '<div class="lr_dct_ent"'
    # The subsequent sections can be separated by the HTML tag '<div class="vk_'
    # The dictionary definition line is identified by the HTML tag '<div style="display:inline" data-dobid="dfn">'
    # The encyclopedia definition line is identified by the HTML tag '<div class="_oDd" data-hveid=".*?"><span class="_Tgc">'
    # The pronunciation audio line is identified by the HTML tag '<audio src='
    # The pronunciation audio header word is identified by the HTML tag '<span data-dobid="hdw">'
    cdict.DICT_MARKER_DEFINITION = [
    [r'<div style="display:inline" data-dobid="dfn"><span>', r'</span>'],
    [r'<div class="_oDd" data-hveid=".*?"><span class="_Tgc">', r'</span></div>']
    ]
    cdict.DICT_MARKER_PRONUNCIATION_URL = [r'<audio src="', r'" data-dobid="aud"']
    cdict.DICT_MARKER_PRONUNCIATION_WORD = [r'<span data-dobid="hdw">', r'</span>']


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

