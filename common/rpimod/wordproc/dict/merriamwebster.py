#!/usr/bin/env python
# -*- encoding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : merriamwebsterv2.py
# Description : Dictionary lookup functions sourcing from Merriam Webster Collegiate Dictionary
# Author      : Dito Manavalan
# Date        : 2017/06/07
#--------------------------------------------------------------------------------------------------

################################################################
# Source: Merriam-Webster's Collegiate Dictionary
# Sample Search URL: http://www.merriam-webster.com/dictionary/test
# Sample API URL: http://www.dictionaryapi.com/api/v1/references/collegiate/xml/test?key=cbbd4001-c94d-493a-ac94-7268a7e41f6f
# Sample Pronunciation URL: http://media.merriam-webster.com/soundc11/t/test0001.wav
################################################################

import sys
#import re
import merriamwebsterapi as api

sys.path.insert(0, "../../../..")
import common.rpimod.stdio.output as coutput

# Set to True to turn debug messages on
ERR_DEBUG = False

################################################################
# Dictionary Configuration Variables
################################################################

DICT_SOURCE_NAME = unicode("Merriam-Webster's Collegiate Dictionary", 'utf-8')
DICT_ENTRY_URL = unicode("http://www.dictionaryapi.com/api/v1/references/collegiate/xml/{WORD}?key={KEY}", 'utf-8')
DICT_AUDIO_URL = unicode("http://media.merriam-webster.com/soundc11/{FOLDER}/{CLIP}", 'utf-8')
DICT_KEY = unicode("cbbd4001-c94d-493a-ac94-7268a7e41f6f", 'utf-8')

DICT_ASCII_EMPTY_STR = ""
DICT_UNICODE_EMPTY_STR = unicode("", 'utf-8')


def get_dictionary_source():
    _FUNC_NAME_ = "get_dictionary_source"

    return DICT_SOURCE_NAME


def get_dictionary_entry(connectionPool, word):
    _FUNC_NAME_ = "get_dictionary_entry"

    # Download dictionary entry
    dictEntryURL = DICT_ENTRY_URL.format(WORD=word, KEY=DICT_KEY).replace(" ", "%20")
    dictEntryURL = dictEntryURL.encode('utf-8')             # Handle URL strings in ascii

    DEBUG_VAR="dictEntryURL"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(dictEntryURL)))
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

    dictEntryResponse = connectionPool.request('GET', dictEntryURL)

    DEBUG_VAR="dictEntryResponse.data"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(dictEntryResponse.data)))
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

    # Convert XML to unicode
    if isinstance(dictEntryResponse.data, str):
        outputXML = unicode(dictEntryResponse.data, 'utf-8')
    else:
        outputXML = dictEntryResponse.data

    return outputXML


def parse_word_definition(word, entryXML):
    _FUNC_NAME_ = "parse_word_definition"
    searchWord = word

    DEBUG_VAR="entryXML"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(entryXML)))

    sourceXML = entryXML
    if isinstance(sourceXML, unicode):
        sourceXML = sourceXML.encode('utf-8')

    DEBUG_VAR="sourceXML"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(sourceXML)))

    wordDefinition = []
    dictionary = api.CollegiateDictionary(DICT_KEY)
    
    try:
        entries = dictionary.lookup(searchWord, sourceXML)
        for entry in entries:
            for sense in entry.senses:

                DEBUG_VAR="sense.definition"
                coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(sense.definition)))
                coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

                strDefinition = unicode("({0}) {1}", 'utf-8').format(entry.function, sense.definition)
                if isinstance(strDefinition, str):
                    wordDefinition.append(unicode(strDefinition, 'utf-8'))
                else:
                    wordDefinition.append(strDefinition)

    except api.WordNotFoundException:
        wordDefinition = []

    return wordDefinition


# todo: Improve lookup/pronunciation with root word match e.g. idiosyncratic <uor>
def parse_word_clip(word, entryXML):
    _FUNC_NAME_ = "parse_word_clip"
    searchWord = word

    DEBUG_VAR="entryXML"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(entryXML)))

    sourceXML = entryXML
    if isinstance(sourceXML, unicode):
        sourceXML = sourceXML.encode('utf-8')

    DEBUG_VAR="sourceXML"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(sourceXML)))

    dictionary = api.CollegiateDictionary(DICT_KEY)

    wordFound = False
    audioClipFound = False
    audioClip = DICT_UNICODE_EMPTY_STR
    audioClipWord = DICT_UNICODE_EMPTY_STR

    try:
        # Pass #1: Find matching headword spelling
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "Start of Pass #1")

        entries = dictionary.lookup(searchWord, sourceXML)
        for entry in entries:

            DEBUG_VAR="entry.spelling"
            coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(entry.spelling)))
            coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

            if searchWord == entry.spelling:
                for audio in entry.audio:
                    audioClipWord = entry.spelling
                    wordFound = True
                    audioClip = audio
                    audioClipFound = True
                    if wordFound:
                        break
            if wordFound:
                break

        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "End of Pass #1")
        DEBUG_VAR="audioClipFound"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(audioClipFound)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))
        DEBUG_VAR="wordFound"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(wordFound)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        # Pass #2: Find matching inflection
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "Start of Pass #2")
        if audioClipFound == False:
            wordFound = False
            audioClip = DICT_UNICODE_EMPTY_STR
            audioClipWord = DICT_UNICODE_EMPTY_STR

            entries = dictionary.lookup(searchWord, sourceXML)
            for entry in entries:

                DEBUG_VAR="entry.spelling"
                coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(entry.spelling)))
                coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

                for inflection in entry.inflections:

                    DEBUG_VAR="inflection.spellings"
                    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(inflection.spellings)))
                    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

                    for spelling in inflection.spellings:

                        DEBUG_VAR="searchWord"
                        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(searchWord)))
                        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

                        DEBUG_VAR="spelling"
                        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(spelling)))
                        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

                        if searchWord == spelling:
                            audioClipWord = spelling
                            wordFound = True

                            DEBUG_VAR="inflection.sound_urls"
                            coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(inflection.sound_urls)))
                            coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

                            for sound_url in inflection.sound_urls:

                                DEBUG_VAR="sound_url"
                                coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(sound_url)))
                                coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

                                audioClip = sound_url
                                audioClipFound = True
                                break

                        if wordFound:
                            break

                if wordFound:
                    break

        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "End of Pass #2")
        DEBUG_VAR="audioClipFound"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(audioClipFound)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))
        DEBUG_VAR="wordFound"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(wordFound)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        # Pass #3: Find pronunciation for first entry, if no match found
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "Start of Pass #3")
        if audioClipFound == False:
            wordFound = False
            audioClip = DICT_UNICODE_EMPTY_STR
            audioClipWord = DICT_UNICODE_EMPTY_STR

            entries = dictionary.lookup(searchWord, sourceXML)
            for entry in entries:
                for audio in entry.audio:
                    audioClipWord = entry.spelling
                    wordFound = True
                    audioClip = audio
                    audioClipFound = True
                    if wordFound:
                        break
                if wordFound:
                    break
        
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "End of Pass #3")
        DEBUG_VAR="audioClipFound"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(audioClipFound)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))
        DEBUG_VAR="wordFound"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(wordFound)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

    except api.WordNotFoundException:
        audioClip = DICT_UNICODE_EMPTY_STR
        audioClipWord = DICT_UNICODE_EMPTY_STR

    if not audioClipFound:
        audioClip = DICT_UNICODE_EMPTY_STR
        audioClipWord = DICT_UNICODE_EMPTY_STR

    DEBUG_VAR="searchWord"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(searchWord)))
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))
    DEBUG_VAR="audioClipWord"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(audioClipWord)))
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))
    DEBUG_VAR="audioClip"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(audioClip)))
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

    # Return audioClipWord and audioClip, if found
    if isinstance(audioClipWord, str):
        audioClipWord = unicode(audioClipWord, 'utf-8')
    else:
        audioClipWord = audioClipWord

    if isinstance(audioClip, str):
        audioClip = unicode(audioClip, 'utf-8')
    else:
        audioClip = audioClip

    return [audioClipWord, audioClip]