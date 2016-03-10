#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : merriamwebster.py
# Description : Dictionary lookup functions sourcing from Merriam Webster Collegiate Dictionary
# Author      : Dito Manavalan
# Date        : 2016/02/09
#--------------------------------------------------------------------------------------------------

import sys
import re
from xml.dom import minidom

sys.path.insert(0, "/home/pi/projects/raspi")
import common.rpimod.stdio.output as coutput

# Set to True to turn debug messages on
ERR_DEBUG = False

################################################################
# Dictionary Configuration Variables
################################################################

# Sample dictionary API URL - http://www.dictionaryapi.com/api/v1/references/collegiate/xml/test?key=cbbd4001-c94d-493a-ac94-7268a7e41f6f
DICT_ENTRY_URL = unicode("http://www.dictionaryapi.com/api/v1/references/collegiate/xml/{WORD}?key={KEY}", 'utf-8')
DICT_AUDIO_URL = unicode("http://media.merriam-webster.com/soundc11/{FOLDER}/{CLIP}", 'utf-8')
DICT_KEY = unicode("cbbd4001-c94d-493a-ac94-7268a7e41f6f", 'utf-8')

DICT_ASCII_EMPTY_STR = ""
DICT_UNICODE_EMPTY_STR = unicode("", 'utf-8')


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


def get_dictionary_audio(connectionPool, audioClipURL):
    _FUNC_NAME_ = "get_dictionary_audio"

    # Download audio clip
    audioClipResponse = connectionPool.request('GET', audioClipURL)
    return audioClipResponse.data


def cleanse_dictionary_entry(entryXML):
    _FUNC_NAME_ = "cleanse_dictionary_entry"

    DEBUG_VAR="entryXML"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(entryXML)))
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, entryXML))

    # Handle XML cleansing in ascii
    if isinstance(entryXML, str):
        cleansedXML = entryXML
    else:
        cleansedXML = entryXML.encode('utf-8')

    DEBUG_VAR="cleansedXML"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(cleansedXML)))

    cleanseTagList = []
    for tag in ['d_link', 'fw', 'it', 'un']:
        cleanseTagList.append(tag)
    
    cleanseElementList = []

    for tag in cleanseTagList:

        DEBUG_VAR="tag"
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(tag)))
        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        cleansedXML = cleansedXML.replace("<{0}>".format(tag), DICT_ASCII_EMPTY_STR).replace("</{0}>".format(tag), DICT_ASCII_EMPTY_STR)

    # Convert XML to unicode
    if isinstance(cleansedXML, str):
        outputXML = unicode(cleansedXML, 'utf-8')
    else:
        outputXML = cleansedXML

    DEBUG_VAR="outputXML"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(outputXML)))
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, outputXML))

    return outputXML


def parse_word_definition(word, entryXML):
    _FUNC_NAME_ = "parse_word_definition"
    searchWord = word

    DEBUG_VAR="entryXML"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(entryXML)))

    sourceXML = cleanse_dictionary_entry(entryXML)

    # Handle XML cleansing in ascii
    if isinstance(sourceXML, unicode):
        sourceXML = sourceXML.encode('utf-8')

    DEBUG_VAR="sourceXML"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(sourceXML)))

    dictEntryXML = minidom.parseString(sourceXML)
    wordDefinition = []

    DEBUG_VAR="dictEntryXML"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(dictEntryXML)))

    # Process <entry> elements to locate match
    entryElements = dictEntryXML.getElementsByTagName('entry')
    for entryElement in entryElements:
        wordFound = False

        # Pass #1: Process <hw> tags to locate match
        hwElements = entryElement.getElementsByTagName('hw')
        for hwElement in hwElements:
            if hwElement.firstChild.nodeType == hwElements[0].firstChild.TEXT_NODE:
                hwText = hwElement.firstChild.data.replace("*", DICT_ASCII_EMPTY_STR)
                if hwText.lower() == searchWord.lower():
                    wordFound = True
                    break

        # Pass #2: Process <ure> tags to locate match
        ureElements = entryElement.getElementsByTagName('ure')
        for ureElement in ureElements:
            if ureElement.firstChild.nodeType == ureElements[0].firstChild.TEXT_NODE:
                ureText = ureElement.firstChild.data.replace("*", DICT_ASCII_EMPTY_STR)
                if ureText.lower() == searchWord.lower():
                    wordFound = True
                    break

        # Pass #3: Process <if> tags to locate match
        ifElements = entryElement.getElementsByTagName('if')
        for ifElement in ifElements:
            if ifElement.firstChild.nodeType == ifElements[0].firstChild.TEXT_NODE:
                ifText = ifElement.firstChild.data.replace("*", DICT_ASCII_EMPTY_STR)
                if ifText.lower() == searchWord.lower():
                    wordFound = True
                    break

        # Process <dt> elements to retrieve definition, if matched
        if wordFound:
            dtElements = entryElement.getElementsByTagName('dt')
            for dtIndex, dtElement in enumerate(dtElements, start=0):
                if dtElement.firstChild.nodeType == dtElement.firstChild.TEXT_NODE:
                    dtText = re.sub("^[^:]*:", DICT_ASCII_EMPTY_STR, dtElement.firstChild.data)
                    dtText = re.sub(":[^:]*$", DICT_ASCII_EMPTY_STR, dtText)
                    if dtText != DICT_ASCII_EMPTY_STR:

                        DEBUG_VAR="dtText"
                        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(dtText)))
                        coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

                        if isinstance(dtText, str):
                            wordDefinition.append(unicode(dtText, 'utf-8'))
                        else:
                            wordDefinition.append(dtText)
                        
                
                # Process <sx> elements
                sxElements = dtElement.getElementsByTagName('sx')
                sxCombinedText = DICT_ASCII_EMPTY_STR
                for sxIndex, sxElement in enumerate(sxElements, start=0):
                    if sxElement.firstChild.nodeType == dtElement.firstChild.TEXT_NODE:
                        sxText = re.sub("^[^:]*:", DICT_ASCII_EMPTY_STR, sxElement.firstChild.data)
                        sxText = re.sub(":[^:]*$", DICT_ASCII_EMPTY_STR, sxText)
                        if sxText != DICT_ASCII_EMPTY_STR:
                            if sxIndex < len(sxElements) - 1:
                                sxCombinedText = sxCombinedText + sxText + ", "
                            else:
                                sxCombinedText = sxCombinedText + sxText
                if sxCombinedText != DICT_ASCII_EMPTY_STR:
                    if isinstance(sxCombinedText, str):
                        wordDefinition.append(unicode(sxCombinedText, 'utf-8'))
                    else:
                        wordDefinition.append(sxCombinedText)


    # Scan all entries without matching, if no definitions were retrieved
    if len(wordDefinition) == 0:
        # Process <entry> elements to locate match
        entryElements = dictEntryXML.getElementsByTagName('entry')
        for entryElement in entryElements:
            # Process <dt> elements to retrieve definition
            dtElements = entryElement.getElementsByTagName('dt')
            for dtIndex, dtElement in enumerate(dtElements, start=0):
                if dtElement.firstChild.nodeType == dtElement.firstChild.TEXT_NODE:
                    dtText = re.sub("^[^:]*:", DICT_ASCII_EMPTY_STR, dtElement.firstChild.data)
                    dtText = re.sub(":[^:]*$", DICT_ASCII_EMPTY_STR, dtText)
                    if dtText != DICT_ASCII_EMPTY_STR:
                        if isinstance(dtText, str):
                            wordDefinition.append(unicode(dtText, 'utf-8'))
                        else:
                            wordDefinition.append(dtText)
                
                # Process <sx> elements
                sxElements = dtElement.getElementsByTagName('sx')
                sxCombinedText = DICT_ASCII_EMPTY_STR
                for sxIndex, sxElement in enumerate(sxElements, start=0):
                    if sxElement.firstChild.nodeType == dtElement.firstChild.TEXT_NODE:
                        sxText = re.sub("^[^:]*:", DICT_ASCII_EMPTY_STR, sxElement.firstChild.data)
                        sxText = re.sub(":[^:]*$", DICT_ASCII_EMPTY_STR, sxText)
                        if sxText != DICT_ASCII_EMPTY_STR:
                            if sxIndex < len(sxElements) - 1:
                                sxCombinedText = sxCombinedText + sxText + ", "
                            else:
                                sxCombinedText = sxCombinedText + sxText
                if sxCombinedText != DICT_ASCII_EMPTY_STR:
                    if isinstance(sxCombinedText, str):
                        wordDefinition.append(unicode(sxCombinedText, 'utf-8'))
                    else:
                        wordDefinition.append(sxCombinedText)
    
    # Handle word definitions in unicode
    return wordDefinition


# todo: Improve lookup/pronunciation with root word match e.g. idiosyncratic <uor>
def parse_word_clip(word, entryXML):
    _FUNC_NAME_ = "parse_word_clip"
    searchWord = word

    DEBUG_VAR="entryXML"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(entryXML)))

    sourceXML = cleanse_dictionary_entry(entryXML)

    # Handle XML cleansing in ascii
    if isinstance(sourceXML, unicode):
        sourceXML = sourceXML.encode('utf-8')

    DEBUG_VAR="sourceXML"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(sourceXML)))

    dictEntryXML = minidom.parseString(sourceXML)

    DEBUG_VAR="dictEntryXML"
    coutput.print_debug(ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(dictEntryXML)))

    # Pass #1: Process <uro> tag to locate matching entry
    wordFound = False
    audioClipFound = False
    audioClip = DICT_UNICODE_EMPTY_STR
    audioClipWord = DICT_UNICODE_EMPTY_STR

    # Process <entry> elements
    entryElements = dictEntryXML.getElementsByTagName('entry')
    for entryElement in entryElements:
        uroElements = entryElement.getElementsByTagName('uro')
        for uroElement in uroElements:

            # Process first populated <ure> element to get root word
            ureElements = uroElement.getElementsByTagName('ure')
            for ureElement in ureElements:
                if ureElement.firstChild.nodeType == ureElement.firstChild.TEXT_NODE:
                    audioClipWord = ureElement.firstChild.data.replace("*", DICT_UNICODE_EMPTY_STR).strip()
                    if audioClipWord != DICT_UNICODE_EMPTY_STR:
                        break

            # Process first populated <wav> element to get audio clip
            wavElements = uroElement.getElementsByTagName('wav')
            for wavElement in wavElements:
                if wavElement.firstChild.nodeType == wavElement.firstChild.TEXT_NODE:
                    audioClip = wavElement.firstChild.data.strip()
                    if audioClip != DICT_UNICODE_EMPTY_STR:
                        break

            if audioClipWord == searchWord:
                wordFound = True
                if audioClip != DICT_UNICODE_EMPTY_STR:
                    audioClipFound = True

            if wordFound:
                break

        if wordFound:
            break

    # Pass #2: Process <in> tag to locate matching entry
    if audioClipFound == False:
        wordFound = False
        audioClipFound = False
        audioClip = DICT_UNICODE_EMPTY_STR
        audioClipWord = DICT_UNICODE_EMPTY_STR

        # Process <entry> elements
        entryElements = dictEntryXML.getElementsByTagName('entry')
        for entryIndex, entryElement in enumerate(entryElements, start=0):

            inElements = entryElement.getElementsByTagName('in')
            for inElement in inElements:

                # Process first populated <if> element to get root word
                ifElements = inElement.getElementsByTagName('if')
                for ifElement in ifElements:
                    if ifElement.firstChild.nodeType == ifElement.firstChild.TEXT_NODE:
                        audioClipWord = ifElement.firstChild.data.replace("*", DICT_UNICODE_EMPTY_STR).strip()
                        if audioClipWord != DICT_UNICODE_EMPTY_STR:
                            break

                # Process first populated <wav> element to get audio clip
                wavElements = inElement.getElementsByTagName('wav')
                for wavElement in wavElements:
                    if wavElement.firstChild.nodeType == wavElement.firstChild.TEXT_NODE:
                        audioClip = wavElement.firstChild.data.strip()
                        if audioClip != DICT_UNICODE_EMPTY_STR:
                            break

                if audioClipWord == searchWord:
                    wordFound = True
                    if audioClip != DICT_UNICODE_EMPTY_STR:
                        audioClipFound = True

                if wordFound:
                    break

            if wordFound:
                break

    # Pass #3: Process <hw> tag to locate matching entry, if no match found
    if audioClipFound == False:

        wordFound = False
        audioClipFound = False
        audioClip = DICT_UNICODE_EMPTY_STR
        audioClipWord = DICT_UNICODE_EMPTY_STR

        # Process <entry> elements
        entryElements = dictEntryXML.getElementsByTagName('entry')
        for entryElement in entryElements:
            hwElements = entryElement.getElementsByTagName('hw')
            for hwElement in hwElements:

                if hwElement.firstChild.nodeType == hwElement.firstChild.TEXT_NODE:
                    audioClipWord = hwElement.firstChild.data.replace("*", DICT_UNICODE_EMPTY_STR).strip()

                    if audioClipWord == searchWord:
                        wordFound = True

                        # Process <wav> elements to get audio clip
                        wavElements = entryElement.getElementsByTagName('wav')
                        for wavElement in wavElements:
                            if wavElement.firstChild.nodeType == wavElement.firstChild.TEXT_NODE:
                                audioClip = wavElement.firstChild.data.strip()

                                if audioClip != DICT_UNICODE_EMPTY_STR:
                                    audioClipFound = True
                                    break

                if wordFound == True:
                    break

            if wordFound == True:
                break

    # Pass #4: Process <wav> tag to locate first entry, if no match found
    if audioClipFound == False:

        wordFound = False
        audioClipFound = False
        audioClip = DICT_UNICODE_EMPTY_STR
        audioClipWord = DICT_UNICODE_EMPTY_STR

        # Process <entry> elements
        entryElements = dictEntryXML.getElementsByTagName('entry')
        for entryElement in entryElements:
            wavElements = entryElement.getElementsByTagName('wav')
            for wavElement in wavElements:

                if wavElement.firstChild.nodeType == wavElement.firstChild.TEXT_NODE:
                    audioClip = wavElement.firstChild.data.strip()

                if audioClip != DICT_UNICODE_EMPTY_STR:
                    audioClipFound = True

                    # Process <hw> elements to get root word
                    hwElements = entryElement.getElementsByTagName('hw')
                    for hwElement in hwElements:

                        if hwElement.firstChild.nodeType == hwElement.firstChild.TEXT_NODE:
                            audioClipWord = hwElement.firstChild.data.replace("*", DICT_UNICODE_EMPTY_STR).strip()

                            if audioClipWord != DICT_UNICODE_EMPTY_STR:
                                wordFound == True
                                break

                if audioClipFound == True:
                    break

            if audioClipFound == True:
                break

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
    if audioClipFound:
        # Determine audio clip folder
        # Reference: http://www.dictionaryapi.com/info/faq-audio-image.htm
        if re.match('^bix.*', audioClip):
            audioClipFolder = "bix"
        elif re.match('^gg.*', audioClip):
            audioClipFolder = "gg"
        elif re.match('^[0-9].*', audioClip):
            audioClipFolder = "number"
        else:
            audioClipFolder = audioClip[0:1]

        # Determine audio clip URL
        audioClipURL = DICT_AUDIO_URL.format(FOLDER=audioClipFolder, CLIP=audioClip)

        return [audioClipWord, audioClipURL]
    else:
        return [DICT_UNICODE_EMPTY_STR, DICT_UNICODE_EMPTY_STR]
