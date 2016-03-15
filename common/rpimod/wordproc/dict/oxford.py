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

# Set to True to turn debug messages on
ERR_DEBUG = False

################################################################
# Dictionary Configuration Variables
################################################################

DICT_SOURCE_NAME = unicode("Oxford Dictionaries", 'utf-8')
DICT_ENTRY_URL = unicode("http://www.oxforddictionaries.com/us/definition/american_english/{WORD}?searchDictCode=all", 'utf-8')
DICT_AUDIO_URL = unicode("{PATH}", 'utf-8')

DICT_UNICODE_EMPTY_STR = unicode("", 'utf-8')
DICT_UNICODE_NEWLINE_STR = unicode("\n", 'utf-8')


def get_dictionary_source():
    _FUNC_NAME_ = "get_dictionary_source"

    return DICT_SOURCE_NAME


def find_enclosed_text(rawStartPattern, rawEndPattern, text):
    _FUNC_NAME_ = "find_enclosed_text"

    regexNonGreedyJoiner = r'(.*?)'
    rawSearchPattern = rawStartPattern + regexNonGreedyJoiner + rawEndPattern

    enclosedTextMatches = []
    matches = re.finditer(rawSearchPattern, text)
    for match in matches:
        enclosedTextMatches.append(match.group(1))

    return enclosedTextMatches


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


def cleanse_dictionary_entry(entryText):
    _FUNC_NAME_ = "cleanse_dictionary_entry"

    DEBUG_VAR="entryText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(entryText)))

    cleansedText = entryText

    DEBUG_VAR="cleansedText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(cleansedText)))

    cleanseTextList = []
    cleansePatternList = []
    cleanseTagList = []
    cleanseElementList = []
    splitElementList = []

    cleanseTextList = [u'\xb7', u'<span class="punctuation">']
    #cleanseTagList = [u'b', u'i', u'u']
    #cleanseElementList = [u'script', u'style']
    #splitElementList = ['<div class="lr_dct_ent"', '<div class="xpdxpnd _xk vkc_np"']

    # todo: enable cleansing
    # Clean unwanted text
    for searchText in cleanseTextList:
        cleansedText = cleansedText.replace(searchText, DICT_UNICODE_EMPTY_STR)

    # Clean unwanted patterns
    for searchPattern in cleansePatternList:
        cleansedText = re.sub(searchPattern, DICT_UNICODE_EMPTY_STR, cleansedText)

    # Clean tags preserving contents
    for tag in cleanseTagList:
        DEBUG_VAR="tag"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(tag)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        cleansedText = cleansedText.replace(u"<{0}>".format(tag), DICT_UNICODE_EMPTY_STR).replace("</{0}>".format(tag), DICT_UNICODE_EMPTY_STR)

    # Clean tags and contents
    for tag in cleanseElementList:
        DEBUG_VAR="tag"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(tag)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        cleansedText = re.sub(r"<{0}.*?>.*?</{0}>".format(tag), DICT_UNICODE_EMPTY_STR, cleansedText)

    # Split key tags into separate lines for easier identification
    for tag in splitElementList:
        DEBUG_VAR="tag"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(tag)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        cleansedText = cleansedText.replace("{0}".format(tag), DICT_UNICODE_NEWLINE_STR + "{0}".format(tag))

    outputText = cleansedText
    return outputText


def parse_word_definition(word, entryText):
    _FUNC_NAME_ = "parse_word_definition"

    searchWord = word
    wordDefinitions = []

    DEBUG_VAR="entryText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(entryText)))

    sourceText = cleanse_dictionary_entry(entryText)

    DEBUG_VAR="sourceText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(sourceText)))
    
    # The dictionary definition line is identified by the HTML tag '<span class="definition">...</span>'
    startMarker = r'<span class="definition">'
    endMarker = r'[:]*</span>'
    wordDefinitions = wordDefinitions + find_enclosed_text(startMarker, endMarker, sourceText)

    DEBUG_VAR="wordDefinitions"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(wordDefinitions)))
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

    return wordDefinitions


def parse_word_clip(word, entryText):
    _FUNC_NAME_ = "parse_word_clip"

    searchWord = word
    
    audioClipURLs = []
    audioClipURL =  DICT_UNICODE_EMPTY_STR

    audioClipWords = []
    audioClipWord = DICT_UNICODE_EMPTY_STR

    DEBUG_VAR="entryText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(entryText)))

    sourceText = cleanse_dictionary_entry(entryText)

    DEBUG_VAR="sourceText"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(sourceText)))

    # The pronunciation audio line is identified by the HTML tag '<div class="sound audio_play_button icon-audio" data-src-mp3="http://www.oxforddictionaries.com/us/media/american_english/us_pron/c/clo/cloud/cloud__us_1.mp3"'
    startMarker = r'data-src-mp3="'
    endMarker = r'"'
    audioClipURLs = audioClipURLs + find_enclosed_text(startMarker, endMarker, sourceText)

    DEBUG_VAR="audioClipURLs"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

    if len(audioClipURLs) > 0:
        audioClipURL = DICT_AUDIO_URL.format(PATH=audioClipURLs[0])

        # The pronunciation audio header word is identified by the HTML tag '<span data-dobid="hdw">'
        startMarker = r'<h2 class="pageTitle">'
        endMarker = r'\n</h2>'
        audioClipWords = audioClipWords + find_enclosed_text(startMarker, endMarker, sourceText)

        if len(audioClipWords) > 0:
            audioClipWord = audioClipWords[0]

    return [audioClipWord, audioClipURL]


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
