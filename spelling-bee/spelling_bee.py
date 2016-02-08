#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################
# Syntax :   sudo python spelling_bee.py runMode contestList mode selection
# where      runMode is study, practice, scan or test.
#            contestList is the word list identifier for the contest in YYYY[-language][-challenge] format
#            mode is chapter, count or word.
#                In chapter mode, the next argument is the chapter number
#                    selection is the chapter number of the word list to be practiced.
#                    Default chapter size is 50 words.
#                In count mode, the next argument is the word range
#                    selection is the index range of words in the word list to be practiced.
#                In word mode, the next argument is the word range
#                    selection is the range of words in the word list to be practiced.
# Example:    sudo python spelling_bee.py study 2016 chapter 7
#             sudo python spelling_bee.py practice 2016-asian-languages count 1
#             sudo python spelling_bee.py test 2016 count 10-15
#             sudo python spelling_bee.py practice 2016 word lary-frees
#             sudo python spelling_bee.py scan 2016 count 10-15
################################################################

# todo: Reduce import execution time
# todo: convert all data handling to unicode

import sys
import os
import time
import argparse
import math
import re
import urllib3
import codecs
import unicodedata
from xml.dom import minidom
import pygame

sys.path.insert(0, "/home/pi/projects/raspi")
import common.rpimod.stdio.input as cinput
import common.rpimod.stdio.output as coutput

################################################################
# Spelling Bee Configuration variables
################################################################

SB_CHAPTER_SIZE = 50
SB_DEFINITION_COUNT = 3
SB_DEFINITION_HIDE_EXPLICIT = True                              # Set to True if definitions containing the word are to be hidden
SB_REPEAT_COUNT = 1
SB_REPEAT_DELAY = 1.5
SB_TEST_MODE = "easy"                                           # Available test modes are: easy, medium and difficult
SB_DATA_DIR = "/home/pi/projects/raspi/spelling-bee/data"

# Spelling Bee Word Lists: Processing Tips
# Obtain word lists from http://myspellit.com/
# Copy lists from the print section and paste into excel
# Apply the foll. regex replacements to cleanse words
#    "^[0-9]*\. "  
#    " [\[][0-9]*]$"

################################################################
# Internal variables
################################################################

SB_ERR_DEBUG = False                                             # Set to True to turn debug messages on

SB_ERR_LOG = "spelling_bee_errors.log"
SB_TEST_LOG = "spelling_bee_tests.log"

SB_DICT_OFFLINE_DIR = SB_DATA_DIR + '/dict'
SB_DICT_WORD_FILE = "spelling_bee_{LISTID}.txt"
SB_DICT_OFFLINE_ENTR = "sb_{WORD}.xml"
SB_DICT_OFFLINE_CLIP = "sb_{WORD}.wav"

#Sample dictionary API URL - http://www.dictionaryapi.com/api/v1/references/collegiate/xml/test?key=cbbd4001-c94d-493a-ac94-7268a7e41f6f
SB_DICT_MW_KEY="cbbd4001-c94d-493a-ac94-7268a7e41f6f"
SB_DICT_MW_ENTRY_URL="http://www.dictionaryapi.com/api/v1/references/collegiate/xml/{WORD}?key={KEY}"
SB_DICT_MW_CLIP_URL="http://media.merriam-webster.com/soundc11/{FOLDER}/{CLIP}"

SB_LIST_BULLET = '•'
SB_PROMPT_SYMBOL = "> "
SB_RIGHT_SYMBOL = '√'
SB_WRONG_SYMBOL = 'X'
SB_PRACTICE_KEYBOARD_MENU = "[N]ext [P]revious [R]epeat Re[v]iew [S]how [L]ookup [H]elp E[x]it"
SB_TEST_KEYBOARD_MENU = "[R]epeat E[x]it"

SB_STUDY_WORD_DEFN_TITLE="\nDefinition of word #{INDEX} ({WORD}):"
SB_PRACTICE_WORD_DEFN_TITLE="\nDefinition of word #{INDEX}:"
SB_LOOKUP_WORD_DEFN_TITLE="\nDefinition of {WORD}:"


class SpellingBee(object):
    """
    A Spelling Bee assistant to help with word list navigation and dictionary lookup.
    It has the following attributes:
        contestList: A string representing the word list identifier for the contest in YYYY[-language][-challenge] format
        wordList: A list containing words loaded from wordFile
        activeChapter: 
        activeRangeStart: 
        activeRangeEnd: 

        activeWord:
        activeEntry:
        activeDefinition:
        activePronunciation:
        activePronunciationWord:
        activeTestValuations:

        word_count():
        chapter_count():
        active_word_count():
    """
    def __init__(self, listID, mode, selection):
        self.contestList = listID

        wordFileName = SB_DATA_DIR + "/" + SB_DICT_WORD_FILE
        wordFileName = wordFileName.format(LISTID=listID)
        wordFile = codecs.open(wordFileName, mode='r', encoding='utf-8')
        self.wordList = wordFile.read().encode('utf-8').splitlines()                # Use of splitlines() avoids the newline character from being stored in the word list
        wordFile.close()

        rangeSelection = selection.split("-")
        self.activeChapter = "-"

        if mode.lower() == "chapter":
            self.activeChapter = int(rangeSelection[0])
            self.activeRangeStart = (self.activeChapter - 1) * SB_CHAPTER_SIZE
            self.activeRangeEnd = self.activeRangeStart + SB_CHAPTER_SIZE - 1
        elif mode.lower() == "count":
            self.activeRangeStart = int(rangeSelection[0]) - 1
            if len(rangeSelection) > 1:
                self.activeRangeEnd = int(rangeSelection[1]) - 1
            else:
                self.activeRangeEnd = len(self.wordList) - 1
        else:
            self.activeRangeStart = self.get_word_index(rangeSelection[0])
            if self.activeRangeStart < 0:
                print "ERROR: Unable to locate '{0}' in word list".format(rangeSelection[0])
                exit(1)

            if len(rangeSelection) > 1:
                self.activeRangeEnd = self.get_word_index(rangeSelection[1])
                if self.activeRangeEnd < 0:
                    print "ERROR: Unable to locate '{0}' in word list".format(rangeSelection[1])
                    exit(1)
            else:
                self.activeRangeEnd = len(self.wordList) - 1

        if self.activeRangeEnd >= len(self.wordList):
            self.activeRangeEnd = len(self.wordList) - 1

        self.activeWord = ""
        self.activeEntry = ""
        self.activeDefinition = []
        self.activePronunciation = ""
        self.activePronunciationWord = ""
        
        self.activeTestDate = ""
        self.activeTestScore = ""
        self.activeTestValuations = []
        self.activePracticeWords = []

    def word_count(self):
        return len(self.wordList)

    def chapter_count(self):
        return int(math.ceil(float(len(self.wordList))/float(SB_CHAPTER_SIZE)))

    def active_word_count(self):
        return (self.activeRangeEnd - self.activeRangeStart + 1)

    def display_about(self):
        print "Spelling Bee {0}".format(self.contestList)
        print "Word Count [{0}] Chapter [{1}/{2}] Words [{3}-{4}]".format(self.word_count(), self.activeChapter, self.chapter_count(), self.activeRangeStart + 1, self.activeRangeEnd + 1)

    def print_active_word_list(self):
        self.display_about()
        print ""
        coutput.columnize(self.wordList[self.activeRangeStart : self.activeRangeEnd + 1], 5)

    def get_word_index(self, searchWord):
        resultIndex = -1
        for wordIndex, word in enumerate(self.wordList, start=0):
            if re.match('^' + searchWord.lower() + '.*', word.lower()):
                resultIndex = wordIndex
                break
        return resultIndex

    def cleanse_formatting(self, entryXML):
        # todo: Cleanse XML of formatting tags
        cleansedXML = entryXML

        cleanseTagList = ['d_link', 'fw', 'it', 'un']
        cleanseElementList = []

        for tag in cleanseTagList:
            cleansedXML = cleansedXML.replace("<{0}>".format(tag), "").replace("</{0}>".format(tag), "")

        return cleansedXML

    # todo: Improve lookup/pronunciation with root word match e.g. idiosyncratic <uor>
    # todo: Implement dictionary XML parsing as a library
    def parse_word_clip(self, word, entryXML):
        _FUNC_NAME_ = "parse_word_clip"
        searchWord = unicode(word, 'utf-8')

        sourceXML = entryXML
        sourceXML = self.cleanse_formatting(sourceXML)
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
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(searchWord)))
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))
        DEBUG_VAR="audioClipWord"
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(audioClipWord)))
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))
        DEBUG_VAR="audioClip"
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(audioClip)))
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        # Return audioClipWord and audioClip, if found
        if audioClipFound:
            return [audioClipWord, audioClip]
        else:
            return ["", ""]


    def parse_word_definition(self, word, entryXML):
        _FUNC_NAME_ = "parse_word_definition"
        searchWord = unicode(word, 'utf-8')
        
        sourceXML = entryXML
        sourceXML = self.cleanse_formatting(sourceXML)
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


    def lookup_dictionary_by_word(self, word):
        _FUNC_NAME_ = "lookup_dictionary_by_word"
        self.activeWord = word.strip()
        
        # Setup connection and error logging
        connectionPool = urllib3.PoolManager()
        errorFileName = SB_DATA_DIR + "/" + SB_ERR_LOG
        errorFile = codecs.open(errorFileName, mode='a', encoding='utf-8')

        # Check offline for dictionary entry
        self.activeEntry = ""
        self.activeDefinition = []
        offlineEntryFileName = SB_DICT_OFFLINE_DIR + "/" + SB_DICT_OFFLINE_ENTR.format(WORD=self.activeWord).replace(" ", "_")

        if os.path.isfile(offlineEntryFileName) and os.path.getsize(offlineEntryFileName) > 100:
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "offlineEntryFile size :: {0}".format(os.path.getsize(offlineEntryFileName)))

            offlineEntryFile = codecs.open(offlineEntryFileName, mode='r', encoding='utf-8')
            # Encode as utf-8 while reading XML file
            self.activeEntry = offlineEntryFile.read().encode('utf-8')
            offlineEntryFile.close()

            self.activeDefinition = self.parse_word_definition(self.activeWord, self.activeEntry)
        else:
            # Download dictionary entry
            dictEntryURL = SB_DICT_MW_ENTRY_URL.format(WORD=self.activeWord, KEY=SB_DICT_MW_KEY).replace(" ", "%20")
            dictEntryResponse = connectionPool.request('GET', dictEntryURL)
            self.activeEntry = dictEntryResponse.data

            # Save dictionary entry offline
            offlineEntryFile = codecs.open(offlineEntryFileName, mode='w', encoding='utf-8')
            # Decode as utf-8 while writing XML file
            # todo: Implement file read/write operations as a library
            offlineEntryFile.write(self.activeEntry.decode('utf-8'))
            offlineEntryFile.close()

            # Verify active word with root word entry
            #wordEntry = self.parse_word_root(self.activeEntry)
            #if self.activeWord.lower() != str(wordEntry).lower():
            #    errorFile.write("ERROR:Entry Mismatch:{0}\n".format(self.activeWord).decode('utf-8'))

            # Retrieve word definition
            self.activeDefinition = self.parse_word_definition(self.activeWord, dictEntryResponse.data)
            if len(self.activeDefinition) == 0:
                errorFile.write("ERROR:Missing Definition:{0}\n".format(self.activeWord).decode('utf-8'))


        # Check offline for word pronunciation
        self.activePronunciation = ""
        self.activePronunciationWord = ""
        offlineProncnFileName = SB_DICT_OFFLINE_DIR + "/" + SB_DICT_OFFLINE_CLIP.format(WORD=self.activeWord).replace(" ", "_")

        # Retrieve pronunciation audio clip word form and filename
        [wordClipForm, wordClip] = self.parse_word_clip(self.activeWord, self.activeEntry)

        if os.path.isfile(offlineProncnFileName) and os.path.getsize(offlineProncnFileName) > 1000:
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "offlineProncnFile size :: {0}".format(os.path.getsize(offlineProncnFileName)))
            self.activePronunciation = offlineProncnFileName
            self.activePronunciationWord = wordClipForm
        else:
            # Save pronunciation offline
            if wordClip == "":
                errorFile.write("ERROR:Missing Audio:{0}\n".format(self.activeWord).decode('utf-8'))
            else:
                # Determine audio clip folder.
                # Reference: http://www.dictionaryapi.com/info/faq-audio-image.htm
                if re.match('^bix.*', wordClip):
                    wordClipFolder = "bix"
                elif re.match('^gg.*', wordClip):
                    wordClipFolder = "gg"
                elif re.match('^[0-9].*', wordClip):
                    wordClipFolder = "number"
                else:
                    wordClipFolder = wordClip[0:1]
                wordClipURL = SB_DICT_MW_CLIP_URL.format(FOLDER=wordClipFolder, CLIP=wordClip)

                # Download audio clip
                wordClipResponse = connectionPool.request('GET', wordClipURL)
                offlineProncnFile = open(offlineProncnFileName, "wb")
                offlineProncnFile.write(wordClipResponse.data)
                offlineProncnFile.close()

                self.activePronunciation = offlineProncnFileName
                self.activePronunciationWord = wordClipForm

        # Close connection and error logging
        errorFile.close()
        connectionPool.clear()

    def lookup_dictionary_by_index(self, index):
        self.lookup_dictionary_by_word(self.wordList[index])
       
    def print_word_definition(self):
        if len(self.activeDefinition) == 0:
            #print "ERROR: Unable to lookup dictionary definition"
            coutput.print_err("Unable to lookup dictionary definition")
        else:
            definitionIndex = 0
            for definition in self.activeDefinition:
                if definitionIndex >= SB_DEFINITION_COUNT:
                    break
                formattedDefinition = unicode(SB_LIST_BULLET + " ", 'utf-8') + definition

                # Check for definitions that contain the word itself
                if SB_DEFINITION_HIDE_EXPLICIT:
                    if re.match('.*' + self.activeWord.lower() + '[ .$].*', definition.lower()) is None:
                        print formattedDefinition
                        definitionIndex += 1
                else:
                    print formattedDefinition
                    definitionIndex += 1

    def pronounce_word(self):
        if self.activePronunciation == "":
            coutput.print_err("Unable to lookup audio pronunciation")
        else:
            wordToken = re.sub('[^a-zA-Z]', "", unicode(self.activeWord, 'utf-8').lower())
            pronunciationToken = re.sub('[^a-zA-Z]', "", self.activePronunciationWord.lower())
            if wordToken != pronunciationToken:
                coutput.print_warn("A different form of the word is being pronounced")
                    
            pygame.mixer.init()
            pygame.mixer.music.load(self.activePronunciation)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() == True:
                continue
            pygame.mixer.stop()
            pygame.mixer.quit()

    def display_word_cue(self, title):
        print title
        self.print_word_definition()
        for i in range (0, SB_REPEAT_COUNT):
            self.pronounce_word()
            time.sleep(SB_REPEAT_DELAY)

    def reset_test_result(self):
        self.activeTestDate = ""
        self.activeTestScore = ""
        self.activeTestValuations = []
        self.activePracticeWords = []

    def valuate_test_response(self, testResponse, testWord, testMode):
        valuationMode = testMode.lower()
        valuationResponse = unicode(testResponse, 'utf-8').strip()
        valuationWord = unicode(testWord, 'utf-8').strip()

        if testMode == "easy":
            testDifficultyLevel = 0
        elif testMode == "medium":
            testDifficultyLevel = 1
        elif testMode == "difficult":
            testDifficultyLevel = 2

        # Rule difficulty goes from high to low
        # Most difficult rule would be relaxed in most number of levels
        if testDifficultyLevel < 2:
            # Relax foreign character restriction
            valuationResponse = unicodedata.normalize('NFKD', valuationResponse).encode('ASCII', 'ignore')
            valuationResponse = unicode(valuationResponse, 'utf-8')
            valuationWord = unicodedata.normalize('NFKD', valuationWord).encode('ASCII', 'ignore')
            valuationWord = unicode(valuationWord, 'utf-8')

        if testDifficultyLevel < 1:
            # Relax letter case restriction
            valuationResponse = valuationResponse.lower()
            valuationWord = valuationWord.lower()

        if valuationResponse == valuationWord:
            valuationResult = True
        else:
            valuationResult = False

        return valuationResult

    def log_test_result(self, testDate, testScore):
        self.activeTestDate = testDate
        self.activeTestScore = testScore

    def log_practice_word(self, testWord):
        self.activePracticeWords.append(testWord)

    def log_test_valuation(self, testValuation):
        self.activeTestValuations.append(testValuation)

    def display_test_result(self):
        print "Test Date [{0}] Score [{1}]".format(self.activeTestDate, self.activeTestScore)
        
        # Color code valuations
        coloredTestValuations = self.activeTestValuations
        for index, valuation in enumerate(coloredTestValuations, start=0):
            if re.match('^' + SB_RIGHT_SYMBOL + '.*', valuation):
                textColor = coutput.get_term_color('green', 'normal', 'normal')
            else:
                textColor = coutput.get_term_color('red', 'normal', 'normal')
            coloredTestValuations[index] = textColor + valuation + coutput.get_term_color('normal', 'normal', 'normal')
        
        #coutput.columnize(self.activeTestValuations, 5)
        coutput.columnize(coloredTestValuations, 5)

        if len(self.activePracticeWords) > 0:
            print "\nPractice Words:"
            coutput.columnize(self.activePracticeWords, 5)

def init_app():
    # Clear screen
    os.system("clear")

    # Switch audio output to 3.5 mm jack
    os.system("amixer -q cset numid=3 1")

    # Suspend input from stdin
    cinput.set_term_input(False)

def exit_app():
    # Switch audio output back to auto
    os.system("amixer -q cset numid=3 0")

    # Resume input from stdin
    cinput.set_term_input(True)

    print "\n\nThank you for practicing for Spelling Bee.\n"
    exit()

def display_help(runMode):
    if runMode == "test":
        print "{0} Keyboard Menu: {1}".format(runMode.title(), SB_TEST_KEYBOARD_MENU)
    else:
        print "{0} Keyboard Menu: {1}".format(runMode.title(), SB_PRACTICE_KEYBOARD_MENU)


# todo: Implement goto feature to specify new start/stop words
def run_practice(spellBee, practiceMode):

    userPracticeMode = practiceMode.strip().lower()
    spellBee.display_about()
    display_help(userPracticeMode)
    userInput = cinput.get_keypress("\nReady to {0}? Press any key when ready ... ".format(userPracticeMode))

    wordIndex = spellBee.activeRangeStart

    while True:
        if (wordIndex < spellBee.activeRangeStart) or (wordIndex > spellBee.activeRangeEnd):
            break

        # Lookup word definition
        spellBee.lookup_dictionary_by_index(wordIndex)
        if userPracticeMode == "study":
            spellBee.display_word_cue(SB_STUDY_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1, WORD=spellBee.wordList[wordIndex]))
        else:
            spellBee.display_word_cue(SB_PRACTICE_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1))
        userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
        
        while True:
            # Move to [n]ext word
            if userInput.lower() == "n":
                wordIndex += 1
                break
            # Move to [p]revious word
            elif userInput.lower() == "p":
                wordIndex -= 1
                break
            # [R]epeat current word
            elif userInput.lower() == "r":
                if userPracticeMode == "study":
                    spellBee.display_word_cue(SB_STUDY_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1, WORD=spellBee.wordList[wordIndex]))
                else:
                    spellBee.display_word_cue(SB_PRACTICE_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1))
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # Re[v]iew active word list
            elif userInput.lower() == "v":
                print ""
                spellBee.print_active_word_list()
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # [S]how current word spelling
            elif userInput.lower() == "s":
                spellBee.display_word_cue(SB_STUDY_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1, WORD=spellBee.wordList[wordIndex]))
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # [L]ookup word definition and pronunciation
            elif userInput.lower() == "l":
                userLookupWord = cinput.get_input("\nEnter word to be looked up: ")
                spellBee.lookup_dictionary_by_word(userLookupWord)
                spellBee.display_word_cue(SB_LOOKUP_WORD_DEFN_TITLE.format(WORD=userLookupWord))
                # Reset lookup to current word
                spellBee.lookup_dictionary_by_index(wordIndex)
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # Display [h]elp and statistics
            elif userInput.lower() == "h":
                print ""
                spellBee.display_about()
                display_help(userPracticeMode)
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # E[x]it application
            elif userInput.lower() == "x":
                exit_app()
            else:
                print "\nInvalid response."
                display_help(userPracticeMode)
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)


# todo: Implement random test feature
def run_test(spellBee):

    spellBee.display_about()
    display_help("test")
    userInput = cinput.get_keypress("\nReady for the test? Press any key when ready ... ")

    testDate = time.strftime('%a %d-%b-%Y %H:%M:%S')
    testTotalCount = spellBee.active_word_count()
    testCorrectCount = 0

    userResponse = ""
    testValuation = ""

    spellBee.reset_test_result()

    wordIndex = spellBee.activeRangeStart
    while True:
        if (wordIndex < spellBee.activeRangeStart) or (wordIndex > spellBee.activeRangeEnd):
            break

        # Lookup word definition
        spellBee.lookup_dictionary_by_index(wordIndex)
        spellBee.display_word_cue(SB_PRACTICE_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1))
        userResponse = cinput.get_input("Enter spelling: ")

        # E[x]it test
        if userResponse.lower() == "x":
            break
        # [R]epeat question
        elif userResponse.lower() == "r":
            continue
        else:

            correctResponse = False
            # Process correct response
            if spellBee.valuate_test_response(userResponse, spellBee.activeWord, SB_TEST_MODE):
                correctResponse = True
                testValuation = SB_RIGHT_SYMBOL + " " + userResponse
                testCorrectCount += 1
            # Process incorrect response
            else:
                testValuation = SB_WRONG_SYMBOL + " " + userResponse
                spellBee.log_practice_word(spellBee.activeWord)

            # Indicate correct form of the answer, if different from the response
            if userResponse != spellBee.activeWord:
                testValuation = testValuation + " (" + spellBee.activeWord + ")"

            # Display valuation
            if correctResponse:
                coutput.print_color('green', " " * 50 + testValuation)
            else:
                coutput.print_color('red', " " * 50 + testValuation)
            
            # Save valuation
            spellBee.log_test_valuation(testValuation)
            

        # Move to next word
        wordIndex += 1
    
    spellBee.log_test_result(testDate, str(testCorrectCount) + "/" + str(testTotalCount))
    print "\nYour test is complete. Displaying results...\n"
    
    spellBee.display_about()
    print ""
    spellBee.display_test_result()


def run_error_scan(spellBee):

    spellBee.display_about()
    userInput = cinput.get_keypress("\nReady for error scan? Press any key when ready ... ")
    print ("\n")

    wordIndex = spellBee.activeRangeStart
    while True:
        if (wordIndex < spellBee.activeRangeStart) or (wordIndex > spellBee.activeRangeEnd):
            break

        # Lookup word definition
        spellBee.lookup_dictionary_by_index(wordIndex)
        print "Scanned word #{0}: {1}".format(wordIndex + 1, spellBee.activeWord)

        # Move to next word
        wordIndex += 1
    
    print "\nError scan is complete. All errors are logged to {0}/{1}.".format(SB_DATA_DIR, SB_ERR_LOG)
    

################################################################
# Main Program
################################################################

# Process command line arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("runMode", type=str, choices=['study', 'practice', 'test', 'scan'], help="is study, practice, test or scan")
argParser.add_argument("contestList", type=str, help="is the word list identifier for the contest in YYYY[-language][-challenge] format")
argParser.add_argument("mode", type=str, choices=['chapter', 'count', 'word'], nargs='?', default='count', help="is chapter, count or word")
argParser.add_argument("selection", type=str, nargs='?', default='1', help="is the chapter number, word index range or word range")
args = argParser.parse_args()

# Setup Spelling Bee word list
spellBee = SpellingBee(args.contestList, args.mode, args.selection)

init_app()

# Run Spelling Bee assistant in practice, test or scan mode
if args.runMode.lower() == "study" or args.runMode.lower() == "practice":
    run_practice(spellBee, args.runMode.lower())
elif args.runMode.lower() == "test":
    run_test(spellBee)
elif args.runMode.lower() == "scan":
    run_error_scan(spellBee)

exit_app()
