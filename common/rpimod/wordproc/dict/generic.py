#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : generic.py
# Description : Generic module to perform dictionary lookup functions
# Author      : Dito Manavalan
# Date        : 2016/03/15
#--------------------------------------------------------------------------------------------------

import sys
import re

#sys.path.insert(0, "/home/pi/projects/raspi")
sys.path.insert(0, "../../../..")
import common.rpimod.stdio.output as coutput
import common.rpimod.wordproc.textparser as cparser

################################################################
# Dictionary Configuration Variables
################################################################

DICT_SOURCE_NAME = unicode("", 'utf-8')
DICT_ENTRY_URL = unicode("{WORD}", 'utf-8')
DICT_AUDIO_URL = unicode("{PATH}", 'utf-8')

DICT_CLEAN_TEXT_PATTERNS = []
DICT_CLEAN_INNER_TEXT_PATTERNS = []
DICT_CLEAN_OUTER_TEXT_PATTERNS = []

DICT_MARKER_DEFINITION = []
DICT_MARKER_PRONUNCIATION_URL = []
DICT_MARKER_PRONUNCIATION_WORD = []

################################################################
# Internal variables
################################################################

# Set to True to turn debug messages on
ERR_DEBUG = False

DICT_UNICODE_EMPTY_STR = unicode("", 'utf-8')
DICT_UNICODE_NEWLINE_STR = unicode("\n", 'utf-8')


def get_dictionary_source():
    _FUNC_NAME_ = "get_dictionary_source"

    return DICT_SOURCE_NAME


def get_dictionary_entry(connectionPool, word):
    _FUNC_NAME_ = "get_dictionary_entry"

    # Download dictionary entry
    dictEntryURL = DICT_ENTRY_URL.format(WORD=word).replace(" ", "%20")
    dictEntryURL = dictEntryURL.encode('utf-8')             # Handle URL strings in ascii

    DEBUG_VAR="dictEntryURL"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(dictEntryURL)))
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

    dictEntryResponse = connectionPool.urlopen('GET', dictEntryURL)

    DEBUG_VAR="dictEntryResponse.data"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(dictEntryResponse.data)))
    #coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

    responseText = dictEntryResponse.data

    DEBUG_VAR="responseText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(responseText)))

    # Convert entry text to unicode
    if isinstance(dictEntryResponse.data, str):
        responseText = unicode(dictEntryResponse.data, 'utf-8')
    else:
        responseText = dictEntryResponse.data

    DEBUG_VAR="responseText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(responseText)))

    return responseText


def parse_word_definition(word, entryText):
    _FUNC_NAME_ = "parse_word_definition"

    searchWord = word
    wordDefinitions = []

    DEBUG_VAR="entryText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(entryText)))

    sourceText = cparser.cleanse_text(entryText, DICT_CLEAN_TEXT_PATTERNS, DICT_CLEAN_INNER_TEXT_PATTERNS, DICT_CLEAN_OUTER_TEXT_PATTERNS)

    DEBUG_VAR="sourceText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(sourceText)))
    
    for marker in DICT_MARKER_DEFINITION:
        wordDefinitions = wordDefinitions + cparser.find_enclosed_text(marker[0], marker[1], sourceText)

    DEBUG_VAR="wordDefinitions"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(wordDefinitions)))
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

    return wordDefinitions


def parse_word_clip(word, entryText):
    _FUNC_NAME_ = "parse_word_clip"

    searchWord = word
    
    pronunciationURLs = []
    pronunciationURL =  DICT_UNICODE_EMPTY_STR

    pronunciationWords = []
    pronunciationWord = DICT_UNICODE_EMPTY_STR

    DEBUG_VAR="entryText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(entryText)))

    sourceText = cparser.cleanse_text(entryText, DICT_CLEAN_TEXT_PATTERNS, DICT_CLEAN_INNER_TEXT_PATTERNS, DICT_CLEAN_OUTER_TEXT_PATTERNS)

    DEBUG_VAR="sourceText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(sourceText)))

    pronunciationURLs = pronunciationURLs + cparser.find_enclosed_text(DICT_MARKER_PRONUNCIATION_URL[0], DICT_MARKER_PRONUNCIATION_URL[1], sourceText)

    if len(pronunciationURLs) > 0:
        pronunciationURL = DICT_AUDIO_URL.format(PATH=pronunciationURLs[0])
        pronunciationWords = pronunciationWords + cparser.find_enclosed_text(DICT_MARKER_PRONUNCIATION_WORD[0], DICT_MARKER_PRONUNCIATION_WORD[1], sourceText)

        if len(pronunciationWords) > 0:
            pronunciationWord = pronunciationWords[0]

    return [pronunciationWord, pronunciationURL]


########################################################################
# Sample application to test the python module
########################################################################

#import urllib3
#
#DICT_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}
#connectionPool = urllib3.PoolManager(10, headers=DICT_USER_AGENT)
#
#for word in [u'cloud', u'klompen', u'fiery', u'incorruptible', u'sakura', u'buckwagon']:
#
#    print word
#    htmlResponse = get_dictionary_entry(connectionPool, word)
#
#    definitions = parse_word_definition(word, htmlResponse)
#    print definitions
#
#    audio = parse_word_clip(word, htmlResponse)
#    print audio
#
#connectionPool.clear()

########################################################################
# Debugging Commands
########################################################################

#Print user-agent for urlopen
#urlopenResponse = connectionPool.urlopen('GET', 'http://httpbin.org/headers')
#print(urlopenResponse.data)

#Print user-agent for request
#requestResponse = connectionPool.request('GET', 'http://httpbin.org/headers')
#print(requestResponse.data)

#vText="blah <script> bad text bad text </script> blah blah blah blah <script> bad text bad text </script> blah blah blah blah blah blah blah <script> bad text bad text </script>"
#vCleansedText = re.sub("<{0}>.*?</{0}>".format("script"), DICT_UNICODE_EMPTY_STR, vText
#print vText
#print vCleansedText
#print re.search(r'<script>(.*?)</script>', vText).group()
#print re.search(r'<script>(.*?)</script>', vText).group(1)
