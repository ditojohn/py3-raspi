#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : freedictionary.py
# Description : Dictionary lookup functions sourcing from The Free Dictionary
# Author      : Dito Manavalan
# Date        : 2016/03/15
#--------------------------------------------------------------------------------------------------

################################################################
# Source: The Free Dictionary by Farlex
# Sample Search URL: http://www.thefreedictionary.com/test
# Sample Pronunciation URL: http://img2.tfd.com/pron/mp3/en/US/dg/dgdgd3sjstdthr.mp3
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
    cdict.DICT_SOURCE_NAME = unicode("The Free Dictionary by Farlex", 'utf-8')
    cdict.DICT_ENTRY_URL = unicode("http://www.thefreedictionary.com/{WORD}", 'utf-8')
    cdict.DICT_AUDIO_URL = unicode("http://img2.tfd.com/pron/mp3/{PATH}.mp3", 'utf-8')

    cdict.DICT_CLEAN_TEXT_PATTERNS = [
    r'<div class="sds-list">.*?<span lang=.*?</div>',
    r'<span class="illustration">.*?</span>',
    r'<script.*?>.*?</script>',
    r'<style.*?>.*?</style>'
    ]
    cdict.DICT_CLEAN_INNER_TEXT_PATTERNS = []
    cdict.DICT_CLEAN_OUTER_TEXT_PATTERNS = []

    # The dictionary definition line is identified by the HTML tag '<div class="sds-list"><b>a. </b>....</div>'
    # The pronunciation audio line is identified by the HTML tag '<div class="wy" id="wy1"></div><h1>cloud</h1><span class=snd2 data-snd="en/US/dg/dgdgd3sjstdthr">'
    # The pronunciation audio header word is identified by the HTML tag '<div class="wy" id="wy1"></div><h1>cloud</h1><span class=snd2 data-snd="en/US/dg/dgdgd3sjstdthr">'
    cdict.DICT_MARKER_DEFINITION = [
    [r'<div class="sds-list"><b>.*?</b>\s*', r'\s*</div>']
    ]
    cdict.DICT_MARKER_PRONUNCIATION_URL = [r'data-snd="', r'"']
    cdict.DICT_MARKER_PRONUNCIATION_WORD = [r'<h1>', r'</h1>']


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

