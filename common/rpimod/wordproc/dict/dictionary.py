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
import common.rpimod.wordproc.dict.merriamwebster as webster
import common.rpimod.wordproc.dict.oxford as oxford
import common.rpimod.wordproc.dict.cambridge as cambridge
import common.rpimod.wordproc.dict.google as google
import common.rpimod.wordproc.dict.collins as collins
import common.rpimod.wordproc.dict.randomhouse as randomhouse
import common.rpimod.wordproc.dict.freedictionary as freedictionary

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

    for dictSource in [freedictionary, collins, randomhouse, cambridge, oxford, google, webster]:
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


def fetch_dictionary_audio(connectionPool, pronunciationURL):
    _FUNC_NAME_ = "fetch_dictionary_audio"

    # Download audio clip
    audioClipResponse = connectionPool.request('GET', pronunciationURL)
    return audioClipResponse.data


def lookup_all_sources(connectionPool, word):
    _FUNC_NAME_ = "lookup_all_sources"

    print "\nWord: " + word

    for dictSource in [freedictionary, randomhouse, collins, google, cambridge, oxford, webster]:
        source = dictSource.get_dictionary_source()
        
        DEBUG_VAR="source"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(source)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        dictEntryText = dictSource.get_dictionary_entry(connectionPool, word)
        currentDefinitions = dictSource.parse_word_definition(word, dictEntryText)
        [currentClipWord, currentClipURL] = dictSource.parse_word_clip(word, dictEntryText)

        print "\nSource: " + source
        print "Definition:"
        for definition in currentDefinitions:
            print definition
        print "Pronunciation URL: " + currentClipURL
        print "Pronunciation Word: " + currentClipWord


########################################################################
# Sample application to test the python module
########################################################################

import urllib3

DICT_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}
connectionPool = urllib3.PoolManager(10, headers=DICT_USER_AGENT)

for word in ['cloud']:
    lookup_all_sources(connectionPool, word)

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

########################################################################
# Debugging Commands
########################################################################

