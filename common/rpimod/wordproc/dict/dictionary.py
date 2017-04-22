#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : dictionary.py
# Description : Dictionary lookup functions sourcing from multiple dictionaries
# Author      : Dito Manavalan
# Date        : 2016/03/14
#--------------------------------------------------------------------------------------------------

import sys
import re

#sys.path.insert(0, "/home/pi/projects/raspi")
sys.path.insert(0, "../../../..")

import common.rpimod.stdio.output as coutput
import common.rpimod.stdio.fileio as cfile

import common.rpimod.wordproc.dict.merriamwebster as webster
import common.rpimod.wordproc.dict.oxford as oxford
import common.rpimod.wordproc.dict.cambridge as cambridge
import common.rpimod.wordproc.dict.google as google
import common.rpimod.wordproc.dict.collins as collins
import common.rpimod.wordproc.dict.randomhouse as randomhouse
import common.rpimod.wordproc.dict.freedictionary as freedictionary
import common.rpimod.wordproc.dict.youtube as youtube

'''
# Reference Priority for Dictionary Sources
PRIORITIZED_DICT_SOURCES = [
webster,
oxford,
cambridge,
collins,
randomhouse,
google,
freedictionary,
youtube
]
'''

PRIORITIZED_DICT_SOURCES = [
cambridge,
collins,
randomhouse,
google,
freedictionary,
youtube,
oxford,
webster
]

DICT_SOURCES = {
'webster': webster,
'oxford': oxford,
'cambridge': cambridge,
'google': google,
'collins': collins,
'randomhouse': randomhouse,
'freedictionary': freedictionary,
'youtube': youtube
}

DICT_LIST_BULLET = u'• '

HEADER_TEXT_COLOR = 'cyan'
SECTION_TEXT_COLOR = 'cyan'
WARNING_TEXT_COLOR = 'yellow'
ERROR_TEXT_COLOR = 'red'

# Set to True to turn debug messages on
ERR_DEBUG = False

################################################################
# Dictionary Configuration Variables
################################################################

def fetch_dictionary_entry(connectionPool, word):
    _FUNC_NAME_ = "fetch_dictionary_entry"

    wordDefinitionSource = ""
    wordDefinitions = []
    wordDefinitionFound = False

    pronunciationSource = ""
    pronunciationWord = ""
    pronunciationURL = ""
    wordPronunciationFound = False

    for dictSource in PRIORITIZED_DICT_SOURCES:
        dictEntryText = dictSource.get_dictionary_entry(connectionPool, word)

        if wordDefinitionFound == False:
            currentDefinitions = dictSource.parse_word_definition(word, dictEntryText)
            if len(currentDefinitions) > 0:
                wordDefinitionSource = dictSource.get_dictionary_source()
                wordDefinitions = currentDefinitions
                wordDefinitionFound = True

                DEBUG_VAR="wordDefinitionSource"
                coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(wordDefinitionSource)))
                coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))


        if wordPronunciationFound == False:
            [currentClipWord, currentClipURL] = dictSource.parse_word_clip(word, dictEntryText)
            if currentClipWord != "":
                pronunciationSource = dictSource.get_dictionary_source()
                [pronunciationWord, pronunciationURL] = [currentClipWord, currentClipURL]
                wordPronunciationFound = True

                DEBUG_VAR="pronunciationSource"
                coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(pronunciationSource)))
                coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        if wordDefinitionFound == True and wordPronunciationFound == True:
            break

    return [word, wordDefinitions, wordDefinitionSource, pronunciationWord, pronunciationURL, pronunciationSource]


def display_dictionary_entry(connectionPool, pronAudioOutput, pronLoopCount, pronLoopDelaySec, word, currentDefinitions, source, currentClipWord, currentClipURL, pronSource):
    print ""

    if len(currentDefinitions) == 0:
        displayMessage = "No definitions available for {WORD}".format(WORD=word)
        coutput.print_color(WARNING_TEXT_COLOR, displayMessage)
    else:
        displayMessage = "Definition of {WORD} from {SOURCE}:".format(WORD=word, SOURCE=source)
        coutput.print_color(HEADER_TEXT_COLOR, displayMessage)
        for definition in currentDefinitions:
            print u"{BULLET}{ITEM}".format(BULLET=DICT_LIST_BULLET, ITEM=definition)

    if currentClipWord == "":
        displayMessage = "No pronunciation available for {WORD}".format(WORD=word)
        coutput.print_color(WARNING_TEXT_COLOR, displayMessage)
    else:
        displayMessage = "Pronunciation of {WORD} from {SOURCE}:".format(WORD=currentClipWord, SOURCE=pronSource)
        coutput.print_color(SECTION_TEXT_COLOR, displayMessage)
        print u"{BULLET}{ITEM}".format(BULLET=DICT_LIST_BULLET, ITEM=currentClipURL)
        cfile.play_url(connectionPool, currentClipURL, pronAudioOutput, pronLoopCount, pronLoopDelaySec)


def lookup_word(connectionPool, pronAudioOutput, pronLoopCount, pronLoopDelaySec, word, *lookupSource):
    _FUNC_NAME_ = "lookup_word"

    isError = False

    dictSources = []
    if len(lookupSource) == 0:
        dictEntry = fetch_dictionary_entry(connectionPool, word)

        currentDefinitions = dictEntry[1]
        source = dictEntry[2]
        currentClipWord = dictEntry[3]
        currentClipURL = dictEntry[4]
        pronSource = dictEntry[5]

        display_dictionary_entry(connectionPool, pronAudioOutput, pronLoopCount, pronLoopDelaySec, word, currentDefinitions, source, currentClipWord, currentClipURL, pronSource)

    elif lookupSource[0].lower() == 'all' or lookupSource[0].lower() in DICT_SOURCES.keys():
        
        if lookupSource[0].lower() == 'all':
            dictSources = dictSources + PRIORITIZED_DICT_SOURCES

        else:                
            dictSources.append(DICT_SOURCES[lookupSource[0].lower()])

        DEBUG_VAR="dictSources"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(dictSources)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))     
        
        for dictSource in dictSources:
            source = dictSource.get_dictionary_source()
            pronSource = dictSource.get_dictionary_source()

            DEBUG_VAR="source"
            coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(source)))
            coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

            dictEntryText = dictSource.get_dictionary_entry(connectionPool, word)
            currentDefinitions = dictSource.parse_word_definition(word, dictEntryText)
            [currentClipWord, currentClipURL] = dictSource.parse_word_clip(word, dictEntryText)

            display_dictionary_entry(connectionPool, pronAudioOutput, pronLoopCount, pronLoopDelaySec, word, currentDefinitions, source, currentClipWord, currentClipURL, pronSource)

    else:
        print ""
        displayMessage = "ERROR: Unable to lookup {WORD}. Dictionary source {SOURCE} not supported".format(WORD=word, SOURCE=lookupSource[0])
        coutput.print_color(ERROR_TEXT_COLOR, displayMessage)

    print ""

########################################################################
# Sample application to test the python module
########################################################################
'''
import urllib3

DICT_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}
connectionPool = urllib3.PoolManager(10, headers=DICT_USER_AGENT)

for word in []:
#for word in ['cloud']:
    lookup_word(connectionPool, word)

for word in ['sakura', 'wagnerian']:
    lookup_word(connectionPool, 'Speaker', 1, 1.5, word, 'youtube')

for word in []:
#for word in ['horrible']:
    lookup_word(connectionPool, word, 'all')

for word in []:
#for word in ['horse']:
    lookup_word(connectionPool, word, 'blah')

for word in []:
#for word in ['cloud', 'klompen', 'fiery', 'incorruptible', 'sakura']:
    entry = fetch_dictionary_entry(connectionPool, word)
    print entry[0]
    #print entry[1]
    for definition in entry[1]:
        print definition
    print entry[2]
    print entry[3]
    print entry[4]
    print entry[5]
    print ""

connectionPool.clear()
'''

########################################################################
# Debugging Commands
########################################################################

'''
cd ~/projects/raspi/common/rpimod/wordproc/dict
sudo python dictionary.py
'''