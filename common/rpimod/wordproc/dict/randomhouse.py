#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : randomhouse.py
# Description : Dictionary lookup functions sourcing from Cambridge
# Author      : Dito Manavalan
# Date        : 2016/03/15
#--------------------------------------------------------------------------------------------------

################################################################
# Source: Dictionary.com based on the Random House Unabridged Dictionary
#         supplemented with sources including American Heritage and Harper Collins
# Sample Search URL: http://dictionary.reference.com/browse/test?s=t
# Sample Pronunciation URL: http://static.sfdict.com/staticrep/dictaudio/T01/T0170800.mp3
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
    cdict.DICT_SOURCE_NAME = unicode("Dictionary.com (Random House Unabridged Dictionary)", 'utf-8')
    cdict.DICT_ENTRY_URL = unicode("http://www.dictionary.com/browse/{WORD}?s=t", 'utf-8')
    cdict.DICT_AUDIO_URL = unicode("{PATH}", 'utf-8')

    cdict.DICT_CLEAN_TEXT_PATTERNS = [
    r':\s*<div class="def-block def-inline-example">.*?</div>',
    r'[:]*\s*<span class="dbox-ex">.*?</span>',
    ]
    cdict.DICT_CLEAN_INNER_TEXT_PATTERNS = []
    cdict.DICT_CLEAN_OUTER_TEXT_PATTERNS = [
    [r'<span.*?>', r'</span>'],
    [r'<a.*?>', r'</a>']
    ]

    # The dictionary definition line is identified by the HTML tag '<div class="def-content">....</div>'
    # The pronunciation audio line is identified by the HTML tag '<audio> <source src="http://static.sfdict.com/staticrep/dictaudio/lunawav/C05/C0576000.ogg" type="audio/ogg"> <source src="http://static.sfdict.com/staticrep/dictaudio/C05/C0576000.mp3" type="audio/mpeg"> </audio>'
    # The pronunciation audio header word is identified by the HTML tag '<h1 class="head-entry"><span class="me" data-syllable="cloud">cloud</span></h1>'
    # The span tag is removed as part of the cleansing
    cdict.DICT_MARKER_DEFINITION = [
    [r'<div class="def-content">\s*', r'\s*</div>']
    ]
    cdict.DICT_MARKER_PRONUNCIATION_URL = [r'type="audio/ogg"> <source src="', r'" type="audio/mpeg"> </audio>']
    cdict.DICT_MARKER_PRONUNCIATION_WORD = [r'<h1 class="head-entry">', r'</h1>']


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

