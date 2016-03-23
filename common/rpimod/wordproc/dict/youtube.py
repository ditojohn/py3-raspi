#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : youtube.py
# Description : Dictionary lookup functions sourcing from Youtube
# Author      : Dito Manavalan
# Date        : 2016/03/22
#--------------------------------------------------------------------------------------------------

################################################################
# Source: YouTube
# Sample Search URL: https://www.youtube.com/results?search_query=Pronunciation+Guide+How+to+Pronounce+Wagnerian
# Sample Pronunciation URL: https://www.youtube.com/watch?v=VvnT8q7EY5U
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
    cdict.DICT_SOURCE_NAME = unicode("YouTube", 'utf-8')
    cdict.DICT_ENTRY_URL = unicode("http://www.google.com/search?hl=en&q=YouTube+Pronunciation+Guide+How+to+Pronounce+{WORD}", 'utf-8')
    cdict.DICT_AUDIO_URL = unicode("{PATH}", 'utf-8')

    cdict.DICT_CLEAN_TEXT_PATTERNS = [
    r'<script.*?>.*?</script>',
    r'<style.*?>.*?</style>'
    ]
    cdict.DICT_CLEAN_INNER_TEXT_PATTERNS = []
    cdict.DICT_CLEAN_OUTER_TEXT_PATTERNS = []

    # The dictionary definition line is identified by the HTML tag '<div class="sds-list"><b>a. </b>....</div>'
    # The pronunciation audio line is identified by the HTML tag '<div class="wy" id="wy1"></div><h1>cloud</h1><span class=snd2 data-snd="en/US/dg/dgdgd3sjstdthr">'
    # The pronunciation audio header word is identified by the HTML tag '<div class="wy" id="wy1"></div><h1>cloud</h1><span class=snd2 data-snd="en/US/dg/dgdgd3sjstdthr">'
    cdict.DICT_MARKER_DEFINITION = [
    [r'<unknown>', r'</unknown>']
    ]
    cdict.DICT_MARKER_PRONUNCIATION_URL = [r'<div class="rc" data-hveid=.*?<h3 class="r"><a href="', r'" onmousedown.*?>How to Pronounce.*? - YouTube</a></h3>.*?<div class="f slp">.*?Uploaded by Pronunciation Guide</div>']
    cdict.DICT_MARKER_PRONUNCIATION_WORD = [r'<div class="rc" data-hveid=.*?<h3 class="r"><a href=".*?" onmousedown.*?>How to Pronounce\s*', r'\s*- YouTube</a></h3>.*?<div class="f slp">.*?Uploaded by Pronunciation Guide</div>']


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
    #return cdict.parse_word_definition(word, entryText)
    return []


def parse_word_clip(word, entryText):
    _FUNC_NAME_ = "parse_word_clip"
    initialize_source()
    return cdict.parse_word_clip(word, entryText)

