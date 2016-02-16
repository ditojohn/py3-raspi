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

ERR_DEBUG = False                                             # Set to True to turn debug messages on

################################################################
# Dictionary Configuration Variables
################################################################

# Sample dictionary API URL - http://www.dictionaryapi.com/api/v1/references/collegiate/xml/test?key=cbbd4001-c94d-493a-ac94-7268a7e41f6f
DICT_ENTRY_URL="http://www.dictionaryapi.com/api/v1/references/collegiate/xml/{WORD}?key={KEY}"
DICT_AUDIO_URL="http://media.merriam-webster.com/soundc11/{FOLDER}/{CLIP}"
DICT_KEY="cbbd4001-c94d-493a-ac94-7268a7e41f6f"


def get_dictionary_entry(connectionPool, word):
    _FUNC_NAME_ = "get_dictionary_entry"

    # Download dictionary entry
    dictEntryURL = DICT_ENTRY_URL.format(WORD=word, KEY=DICT_KEY).replace(" ", "%20")
    dictEntryResponse = connectionPool.request('GET', dictEntryURL)
    # todo: check return for str/unicode
    return dictEntryResponse.data


def get_dictionary_audio(connectionPool, audioClipURL):
    _FUNC_NAME_ = "get_dictionary_audio"

    # Download audio clip
    audioClipResponse = connectionPool.request('GET', audioClipURL)
    return audioClipResponse.data


def cleanse_dictionary_entry(entryXML):
    _FUNC_NAME_ = "cleanse_dictionary_entry"
    # todo: Cleanse XML of formatting tags
    cleansedXML = entryXML

    cleanseTagList = ['d_link', 'fw', 'it', 'un']
    cleanseElementList = []

    for tag in cleanseTagList:
        cleansedXML = cleansedXML.replace("<{0}>".format(tag), "").replace("</{0}>".format(tag), "")

    return cleansedXML


def parse_word_definition(word, entryXML):
    _FUNC_NAME_ = "parse_word_definition"
    searchWord = unicode(word, 'utf-8')
    
    sourceXML = entryXML
    sourceXML = cleanse_dictionary_entry(sourceXML)
    dictEntryXML = minidom.parseString(sourceXML)
    wordDefinition = []

    # Process <entry> elements to locate match
    entryElements = dictEntryXML.getElementsByTagName('entry')
    for entryElement in entryElements:
        wordFound = False

        # Pass #1: Process <hw> tags to locate match
        hwElements = entryElement.getElementsByTagName('hw')
        for hwElement in hwElements:
            if hwElement.firstChild.nodeType == hwElements[0].firstChild.TEXT_NODE:
                hwText = hwElement.firstChild.data.replace("*", "")
                if hwText.lower() == searchWord.lower():
                    wordFound = True
                    break

        # Pass #2: Process <ure> tags to locate match
        ureElements = entryElement.getElementsByTagName('ure')
        for ureElement in ureElements:
            if ureElement.firstChild.nodeType == ureElements[0].firstChild.TEXT_NODE:
                ureText = ureElement.firstChild.data.replace("*", "")
                if ureText.lower() == searchWord.lower():
                    wordFound = True
                    break

        # Pass #3: Process <if> tags to locate match
        ifElements = entryElement.getElementsByTagName('if')
        for ifElement in ifElements:
            if ifElement.firstChild.nodeType == ifElements[0].firstChild.TEXT_NODE:
                ifText = ifElement.firstChild.data.replace("*", "")
                if ifText.lower() == searchWord.lower():
                    wordFound = True
                    break

        # Process <dt> elements to retrieve definition, if matched
        if wordFound:
            dtElements = entryElement.getElementsByTagName('dt')
            for dtIndex, dtElement in enumerate(dtElements, start=0):
                if dtElement.firstChild.nodeType == dtElement.firstChild.TEXT_NODE:
                    dtText = re.sub("^[^:]*:", "", dtElement.firstChild.data)
                    dtText = re.sub(":[^:]*$", "", dtText)
                    if dtText != "":
                        wordDefinition.append(dtText)
                
                # Process <sx> elements
                sxElements = dtElement.getElementsByTagName('sx')
                sxCombinedText = ""
                for sxIndex, sxElement in enumerate(sxElements, start=0):
                    if sxElement.firstChild.nodeType == dtElement.firstChild.TEXT_NODE:
                        sxText = re.sub("^[^:]*:", "", sxElement.firstChild.data)
                        sxText = re.sub(":[^:]*$", "", sxText)
                        if sxText != "":
                            if sxIndex < len(sxElements) - 1:
                                sxCombinedText = sxCombinedText + sxText + ", "
                            else:
                                sxCombinedText = sxCombinedText + sxText
                if sxCombinedText != "":
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
                    dtText = re.sub("^[^:]*:", "", dtElement.firstChild.data)
                    dtText = re.sub(":[^:]*$", "", dtText)
                    if dtText != "":
                        wordDefinition.append(dtText)
                
                # Process <sx> elements
                sxElements = dtElement.getElementsByTagName('sx')
                sxCombinedText = ""
                for sxIndex, sxElement in enumerate(sxElements, start=0):
                    if sxElement.firstChild.nodeType == dtElement.firstChild.TEXT_NODE:
                        sxText = re.sub("^[^:]*:", "", sxElement.firstChild.data)
                        sxText = re.sub(":[^:]*$", "", sxText)
                        if sxText != "":
                            if sxIndex < len(sxElements) - 1:
                                sxCombinedText = sxCombinedText + sxText + ", "
                            else:
                                sxCombinedText = sxCombinedText + sxText
                if sxCombinedText != "":
                    wordDefinition.append(sxCombinedText)
    
    return wordDefinition


# todo: Improve lookup/pronunciation with root word match e.g. idiosyncratic <uor>
def parse_word_clip(word, entryXML):
    _FUNC_NAME_ = "parse_word_clip"
    searchWord = unicode(word, 'utf-8')

    sourceXML = entryXML
    sourceXML = cleanse_dictionary_entry(sourceXML)
    dictEntryXML = minidom.parseString(sourceXML)

    # Pass #1: Process <uro> tag to locate matching entry
    wordFound = False
    audioClipFound = False
    audioClip = ""
    audioClipWord = ""

    # Process <entry> elements
    entryElements = dictEntryXML.getElementsByTagName('entry')
    for entryElement in entryElements:
        uroElements = entryElement.getElementsByTagName('uro')
        for uroElement in uroElements:

            # Process first populated <ure> element to get root word
            ureElements = uroElement.getElementsByTagName('ure')
            for ureElement in ureElements:
                if ureElement.firstChild.nodeType == ureElement.firstChild.TEXT_NODE:
                    audioClipWord = ureElement.firstChild.data.replace("*", "").strip()
                    if audioClipWord != "":
                        break

            # Process first populated <wav> element to get audio clip
            wavElements = uroElement.getElementsByTagName('wav')
            for wavElement in wavElements:
                if wavElement.firstChild.nodeType == wavElement.firstChild.TEXT_NODE:
                    audioClip = wavElement.firstChild.data.strip()
                    if audioClip != "":
                        break

            if audioClipWord == searchWord:
                wordFound = True
                if audioClip != "":
                    audioClipFound = True

            if wordFound:
                break

        if wordFound:
            break

    # Pass #2: Process <in> tag to locate matching entry
    if audioClipFound == False:
        wordFound = False
        audioClipFound = False
        audioClip = ""
        audioClipWord = ""

        # Process <entry> elements
        entryElements = dictEntryXML.getElementsByTagName('entry')
        for entryIndex, entryElement in enumerate(entryElements, start=0):

            inElements = entryElement.getElementsByTagName('in')
            for inElement in inElements:

                # Process first populated <if> element to get root word
                ifElements = inElement.getElementsByTagName('if')
                for ifElement in ifElements:
                    if ifElement.firstChild.nodeType == ifElement.firstChild.TEXT_NODE:
                        audioClipWord = ifElement.firstChild.data.replace("*", "").strip()
                        if audioClipWord != "":
                            break

                # Process first populated <wav> element to get audio clip
                wavElements = inElement.getElementsByTagName('wav')
                for wavElement in wavElements:
                    if wavElement.firstChild.nodeType == wavElement.firstChild.TEXT_NODE:
                        audioClip = wavElement.firstChild.data.strip()
                        if audioClip != "":
                            break

                if audioClipWord == searchWord:
                    wordFound = True
                    if audioClip != "":
                        audioClipFound = True

                if wordFound:
                    break

            if wordFound:
                break

    # Pass #3: Process <hw> tag to locate matching entry, if no match found
    if audioClipFound == False:

        wordFound = False
        audioClipFound = False
        audioClip = ""
        audioClipWord = ""

        # Process <entry> elements
        entryElements = dictEntryXML.getElementsByTagName('entry')
        for entryElement in entryElements:
            hwElements = entryElement.getElementsByTagName('hw')
            for hwElement in hwElements:

                if hwElement.firstChild.nodeType == hwElement.firstChild.TEXT_NODE:
                    audioClipWord = hwElement.firstChild.data.replace("*", "").strip()

                    if audioClipWord == searchWord:
                        wordFound = True

                        # Process <wav> elements to get audio clip
                        wavElements = entryElement.getElementsByTagName('wav')
                        for wavElement in wavElements:
                            if wavElement.firstChild.nodeType == wavElement.firstChild.TEXT_NODE:
                                audioClip = wavElement.firstChild.data.strip()

                                if audioClip != "":
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
        audioClip = ""
        audioClipWord = ""

        # Process <entry> elements
        entryElements = dictEntryXML.getElementsByTagName('entry')
        for entryElement in entryElements:
            wavElements = entryElement.getElementsByTagName('wav')
            for wavElement in wavElements:

                if wavElement.firstChild.nodeType == wavElement.firstChild.TEXT_NODE:
                    audioClip = wavElement.firstChild.data.strip()

                if audioClip != "":
                    audioClipFound = True

                    # Process <hw> elements to get root word
                    hwElements = entryElement.getElementsByTagName('hw')
                    for hwElement in hwElements:

                        if hwElement.firstChild.nodeType == hwElement.firstChild.TEXT_NODE:
                            audioClipWord = hwElement.firstChild.data.replace("*", "").strip()

                            if audioClipWord != "":
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
        return ["", ""]
