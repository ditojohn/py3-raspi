#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################
# Syntax :   sudo python spelling_bee.py runMode contestList mode selection
# where      runMode is study, practice, revise, scan or test.
#            contestList is the word list identifier for the contest in YYYY[-language][-challenge] format
#            mode is chapter, count, word, random.
#                In chapter mode, selection is the chapter number of the word list to be practiced.
#                    Default chapter size is 50 words.
#                In count mode, selection is the index range of words in the word list to be practiced.
#                In word mode, selection is the range of words in the word list to be practiced.
#                In random mode, selection is the range of words in the word list to be practiced.
# Example:    sudo python spelling_bee.py study 2016 chapter 7
#             sudo python spelling_bee.py practice 2016-asian-languages count 1
#             sudo python spelling_bee.py test 2016 count 10-15
#             sudo python spelling_bee.py practice 2016 word lary-frees
#             sudo python spelling_bee.py scan 2016 count 10-15
#             sudo python spelling_bee.py test 2016 random 30
#             sudo python spelling_bee.py revise 2016 random 10
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
import random
import glob

import traceback
import logging

#sys.path.insert(0, "/home/pi/projects/raspi")
sys.path.insert(0, "..")
import common.rpimod.stdio.input as cinput
import common.rpimod.stdio.output as coutput
import common.rpimod.stdio.fileio as cfile
import common.rpimod.wordproc.dict.merriamwebster as cdict
import common.rpimod.wordproc.dict.dictionary as cdictall

################################################################
# Spelling Bee Configuration variables
################################################################

SB_CHAPTER_SIZE = 50

SB_DEFINITION_COUNT = 3
SB_DEFINITION_HIDE_EXPLICIT = True                              # Set to True if definitions containing the word are to be hidden
SB_COLUMN_COUNT = 5

SB_AUDIO_OUTPUT = 'Speaker'
SB_REPEAT_COUNT = 1
SB_REPEAT_DELAY = 1.5

SB_TEST_MODE = "easy"                                           # Available test modes are: easy, medium and difficult
SB_TEST_SAVE_RESULT = True
SB_TEST_SAVE_PRACTICE = True

SB_DATA_DIR = "data/"
SB_STUDY_DIR = "data/study/"
SB_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}

################################################################
# Internal variables
################################################################

# Set to True to turn debug messages on
SB_ERR_DEBUG = False

SB_ERR_LOG = unicode("log/spelling_bee_errors.log", 'utf-8')
SB_TEST_LOG = unicode("log/spelling_bee_tests.log", 'utf-8')
SB_REVISION_LOG = unicode("log/spelling_bee_revision.log", 'utf-8')

SB_WORD_MULTI_FILES = unicode(SB_DATA_DIR + "spelling_bee_{WORD_FILE_PATTERN}.txt", 'utf-8')
SB_PRACTICE_WORD_FILE = unicode("spelling_bee_practice_{LISTID}.txt", 'utf-8')
SB_REVISION_WORD_FILE = unicode("spelling_bee_revision_2016.txt", 'utf-8')

SB_DICT_OFFLINE_DIR = unicode(SB_DATA_DIR + 'dict/', 'utf-8')
SB_DICT_OFFLINE_ENTR = unicode("sb_{WORD}.xml", 'utf-8')
SB_DICT_OFFLINE_CLIP = unicode("sb_{WORD}.wav", 'utf-8')

SB_DICT_OVERRIDE_DIR = unicode(SB_DATA_DIR + 'dict/override/', 'utf-8')
SB_DICT_OVERRIDE_DEFN = unicode("sb_{WORD}.dat", 'utf-8')
SB_DICT_OVERRIDE_CLIP = unicode("sb_{WORD}.mp3", 'utf-8')
SB_DICT_OVERRIDE_MSG = unicode("sb_{WORD}.msg", 'utf-8')

SB_LIST_BULLET = unicode('• ', 'utf-8')
SB_PROMPT_SYMBOL = unicode("> ", 'utf-8')
SB_RIGHT_SYMBOL = unicode('√', 'utf-8')
SB_WRONG_SYMBOL = unicode('X', 'utf-8')
SB_PRACTICE_KEYBOARD_MENU = unicode("[N]ext [P]revious [R]epeat Re[v]iew [S]how [L]ookup [H]elp E[x]it", 'utf-8')
SB_TEST_KEYBOARD_MENU = unicode("[R]epeat [H]elp E[x]it", 'utf-8')
SB_REVISE_KEYBOARD_MENU = unicode("[Y]es [N]o [R]epeat Re[v]iew [H]elp E[x]it", 'utf-8')

SB_STUDY_WORD_DEFN_TITLE = unicode("\nDefinition of word #{INDEX} ({WORD}):", 'utf-8')
SB_PRACTICE_WORD_DEFN_TITLE = unicode("\nDefinition of word #{INDEX}:", 'utf-8')
SB_LOOKUP_WORD_DEFN_TITLE = unicode("\nDefinition of {WORD}:", 'utf-8')

SB_NEWLINE = unicode("\n", 'utf-8')
SB_EMPTY_STRING = unicode("", 'utf-8')


class SpellingBee(object):
    """
    A Spelling Bee assistant to help with word list navigation and dictionary lookup.
    It has the following attributes:
        contestList: A string representing the word list identifier for the contest in YYYY[-language][-challenge] format
        wordList: A list containing words loaded from wordFile

        activeWordIndexList:
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
        _FUNC_NAME_ = "__init__"

        self.contestList = listID
        self.wordList = []

        wordFileDir = SB_WORD_MULTI_FILES.format(WORD_FILE_PATTERN=listID)
        for wordFileName in sorted(glob.glob(wordFileDir)):
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "wordFileName :: {0}".format(wordFileName))
            self.wordList = self.wordList + cfile.read(wordFileName).splitlines()                # Use of splitlines() avoids the newline character from being stored in the word list

        rangeSelection = selection.split("-")
        self.activeChapter = "0"

        if mode.lower() == "chapter":
            self.activeChapter = int(rangeSelection[0])
            self.activeRangeStart = (self.activeChapter - 1) * SB_CHAPTER_SIZE
            self.activeRangeEnd = self.activeRangeStart + SB_CHAPTER_SIZE - 1
            self.activeWordIndexList = list(range(self.activeRangeStart, self.activeRangeEnd+1))

        elif mode.lower() == "count":
            self.activeRangeStart = int(rangeSelection[0]) - 1
            if len(rangeSelection) > 1:
                self.activeRangeEnd = int(rangeSelection[1]) - 1
            else:
                self.activeRangeEnd = len(self.wordList) - 1
            self.activeWordIndexList = list(range(self.activeRangeStart, self.activeRangeEnd+1))

        elif mode.lower() == "word":
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
            self.activeWordIndexList = list(range(self.activeRangeStart, self.activeRangeEnd+1))
        else:
            self.activeRangeStart = -1
            self.activeRangeEnd = -1

            sampleSize = int(rangeSelection[0])
            if sampleSize > self.word_count():
                sampleSize = self.word_count()

            self.activeWordIndexList = random.sample(xrange(0, self.word_count()), sampleSize)

        if mode.lower() != "random":
            if self.activeRangeEnd >= len(self.wordList):
                self.activeRangeEnd = len(self.wordList) - 1

        self.activeWord = SB_EMPTY_STRING
        self.activeEntry = SB_EMPTY_STRING
        self.activeDefinition = []
        self.activePronunciation = SB_EMPTY_STRING
        self.activePronunciationWord = SB_EMPTY_STRING
        
        self.activeTestDate = SB_EMPTY_STRING
        self.activeTestScore = SB_EMPTY_STRING
        self.activeTestValuations = []
        self.activePracticeWords = []

    def word_count(self):
        return len(self.wordList)

    def chapter_count(self):
        return int(math.ceil(float(len(self.wordList))/float(SB_CHAPTER_SIZE)))

    def active_word_count(self):
        return len(self.activeWordIndexList)

    def display_about(self):
        print "Spelling Bee {0}".format(self.contestList)
        print "Word Count [{0}] Chapter [{1}/{2}] Words [{3}-{4}]".format(self.word_count(), self.activeChapter, self.chapter_count(), self.activeRangeStart + 1, self.activeRangeEnd + 1)

    def print_active_word_list(self):
        self.display_about()
        print SB_EMPTY_STRING
        coutput.print_columnized_slice(self.wordList, self.activeWordIndexList, SB_COLUMN_COUNT)

    def get_word_index(self, searchWord):
        resultIndex = -1
        for wordIndex, word in enumerate(self.wordList, start=0):
            if re.match('^' + searchWord.lower() + '.*', word.lower()):
                resultIndex = wordIndex
                break
        return resultIndex

    def lookup_dictionary_by_word(self, word):
        _FUNC_NAME_ = "lookup_dictionary_by_word"

        DEBUG_VAR="self.wordList[0]"
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(self.wordList[0])))
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        DEBUG_VAR="word"
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(word)))
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        self.activeWord = word.strip()

        DEBUG_VAR="self.activeWord"
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(self.activeWord)))
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))
        
        # Setup connection and error logging
        connectionPool = urllib3.PoolManager(10, headers=SB_USER_AGENT)
        errorFileName = SB_DATA_DIR + SB_ERR_LOG

        # Check offline for dictionary entry
        self.activeEntry = SB_EMPTY_STRING
        self.activeDefinition = []

        overrideDefnFileName = SB_DICT_OVERRIDE_DIR + SB_DICT_OVERRIDE_DEFN.format(WORD=word).replace(" ", "_")
        offlineEntryFileName = SB_DICT_OFFLINE_DIR + SB_DICT_OFFLINE_ENTR.format(WORD=word).replace(" ", "_")

        # Check for dictionary definition override
        if os.path.isfile(overrideDefnFileName) and os.path.getsize(overrideDefnFileName) > 0:
            self.activeEntry = unicode("[Dictionary Definition Override]", 'utf-8')
            self.activeDefinition = cfile.read(overrideDefnFileName).splitlines()

            DEBUG_VAR="self.activeEntry"
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(self.activeEntry)))
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

            DEBUG_VAR="self.activeDefinition"
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(self.activeDefinition)))
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        # Check primary source for dictionary entry
        elif os.path.isfile(offlineEntryFileName) and os.path.getsize(offlineEntryFileName) > 100:
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "offlineEntryFile size :: {0}".format(os.path.getsize(offlineEntryFileName)))
            self.activeEntry = cfile.read(offlineEntryFileName)
            self.activeDefinition = cdict.parse_word_definition(self.activeWord, self.activeEntry)

            DEBUG_VAR="self.activeEntry"
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(self.activeEntry)))
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        else:
            # Download dictionary entry
            self.activeEntry = cdict.get_dictionary_entry(connectionPool, self.activeWord)

            DEBUG_VAR="self.activeEntry"
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(self.activeEntry)))
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

            # Save dictionary entry offline
            cfile.write(offlineEntryFileName, self.activeEntry)

            # Retrieve word definition
            self.activeDefinition = cdict.parse_word_definition(self.activeWord, self.activeEntry)
            if len(self.activeDefinition) == 0:
                # Log missing definition error
                errorText = unicode("ERROR:Missing Definition:{0}\n", 'utf-8')
                errorText = errorText.format(self.activeWord)
                cfile.append(errorFileName, errorText)

        # Check offline for word pronunciation
        self.activePronunciation = SB_EMPTY_STRING
        self.activePronunciationWord = SB_EMPTY_STRING

        overrideProncnFileName = SB_DICT_OVERRIDE_DIR + SB_DICT_OVERRIDE_CLIP.format(WORD=self.activeWord).replace(" ", "_")
        offlineProncnFileName = SB_DICT_OFFLINE_DIR + SB_DICT_OFFLINE_CLIP.format(WORD=self.activeWord).replace(" ", "_")

        # Check for dictionary pronunciation override
        if os.path.isfile(overrideProncnFileName) and os.path.getsize(overrideProncnFileName) > 0:
            self.activePronunciation = overrideProncnFileName
            self.activePronunciationWord = self.activeWord

        # Check primary source for dictionary entry and pronunciation
        elif os.path.isfile(offlineEntryFileName) and os.path.getsize(offlineEntryFileName) > 100 and os.path.isfile(offlineProncnFileName) and os.path.getsize(offlineProncnFileName) > 1000:

            self.activePronunciation = offlineProncnFileName
        
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "offlineProncnFile size :: {0}".format(os.path.getsize(offlineProncnFileName)))
           
            DEBUG_VAR="self.activePronunciation"
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(self.activePronunciation)))
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

            DEBUG_VAR="self.activeWord"
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(self.activeWord)))
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

            DEBUG_VAR="self.activeEntry"
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(self.activeEntry)))
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

            # Retrieve pronunciation audio clip word form and filename
            [wordClipForm, wordClipURL] = cdict.parse_word_clip(self.activeWord, cfile.read(offlineEntryFileName))
            self.activePronunciationWord = wordClipForm

            DEBUG_VAR="self.activePronunciationWord"
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(self.activePronunciationWord)))
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

        else:
            # Retrieve pronunciation audio clip word form and filename
            [wordClipForm, wordClipURL] = cdict.parse_word_clip(self.activeWord, self.activeEntry)

            # Save pronunciation offline
            if wordClipURL == SB_EMPTY_STRING:
                # Log missing audio error
                errorText = unicode("ERROR:Missing Audio:{0}\n", 'utf-8')
                errorText = errorText.format(self.activeWord)
                cfile.append(errorFileName, errorText)
            else:
                # Download audio clip
                cfile.download(connectionPool, wordClipURL, offlineProncnFileName)

                self.activePronunciation = offlineProncnFileName
                self.activePronunciationWord = wordClipForm

        # Log audio mismatch error
        wordToken = re.sub('[^a-zA-Z]', SB_EMPTY_STRING, self.activeWord.lower())
        pronunciationToken = re.sub('[^a-zA-Z]', SB_EMPTY_STRING, self.activePronunciationWord.lower())
        if self.activePronunciation != SB_EMPTY_STRING and wordToken != pronunciationToken:
            errorText = unicode("ERROR:Audio Mismatch:{0}\n", 'utf-8')
            errorText = errorText.format(self.activeWord)
            cfile.append(errorFileName, errorText)

        # Close connection
        connectionPool.clear()

    def lookup_dictionary_by_index(self, index):
        self.lookup_dictionary_by_word(self.wordList[index])

    def lookup_all_dictionaries_by_word(self, word):
        _FUNC_NAME_ = "lookup_all_dictionaries_by_word"
        # Setup connection and error logging
        connectionPool = urllib3.PoolManager(10, headers=SB_USER_AGENT)
        cdictall.lookup_word(connectionPool, SB_AUDIO_OUTPUT, SB_REPEAT_COUNT, SB_REPEAT_DELAY, word)
        # Close connection
        connectionPool.clear()
       
    def print_word_definition(self):
        if len(self.activeDefinition) == 0:
            coutput.print_err("Unable to lookup dictionary definition")
        else:
            definitionIndex = 0
            for definition in self.activeDefinition:
                if definitionIndex >= SB_DEFINITION_COUNT:
                    break

                # Check for definitions that contain the word itself
                if SB_DEFINITION_HIDE_EXPLICIT:
                    formattedDefinition = re.sub(self.activeWord, '*' * len(self.activeWord), definition, flags=re.IGNORECASE)

                formattedDefinition = SB_LIST_BULLET + formattedDefinition
                print formattedDefinition
                definitionIndex += 1

    def pronounce_word(self):
        _FUNC_NAME_ = "pronounce_word"
        if self.activePronunciation == SB_EMPTY_STRING:
            coutput.print_err("Unable to lookup audio pronunciation")
        else:
            wordToken = re.sub('[^a-zA-Z]', SB_EMPTY_STRING, self.activeWord.lower())
            DEBUG_VAR="wordToken"
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(wordToken)))
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

            pronunciationToken = re.sub('[^a-zA-Z]', SB_EMPTY_STRING, self.activePronunciationWord.lower())
            DEBUG_VAR="pronunciationToken"
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(pronunciationToken)))
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

            if wordToken != pronunciationToken:
                coutput.print_warn("A different form of the word is being pronounced.")
            
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Executing cfile.play")
            cfile.play(self.activePronunciation, SB_AUDIO_OUTPUT, SB_REPEAT_COUNT, SB_REPEAT_DELAY)

    def print_word_tip(self):
        overrideTipFileName = SB_DICT_OVERRIDE_DIR + SB_DICT_OVERRIDE_MSG.format(WORD=self.activeWord).replace(" ", "_")

        # Check for word message/instruction override
        if os.path.isfile(overrideTipFileName) and os.path.getsize(overrideTipFileName) > 0:
            activeTip = cfile.read(overrideTipFileName)
            coutput.print_tip(activeTip)

    def display_word_cue(self, title):
        _FUNC_NAME_ = "display_word_cue"
        print title
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Executing self.print_word_definition")
        self.print_word_definition()

        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Executing self.pronounce_word")
        self.pronounce_word()

        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Executing self.print_word_tip")
        self.print_word_tip()

    def reset_test_result(self):
        self.activeTestDate = SB_EMPTY_STRING
        self.activeTestScore = SB_EMPTY_STRING
        self.activeTestValuations = []
        self.activePracticeWords = []

    def valuate_test_response(self, testResponse, testWord, testMode):
        valuationMode = testMode.lower()
        valuationResponse = unicode(testResponse, 'utf-8').strip()
        valuationWord = testWord.strip()

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

    def save_evaluation_practice_words(self, practiceMode, saveEnabled):
        _FUNC_NAME_ = "save_evaluation_practice_words"

        if saveEnabled:
            if len(self.activePracticeWords) > 0:

                if practiceMode.lower() == "test":
                    practiceFileName = SB_STUDY_DIR + SB_PRACTICE_WORD_FILE
                    practiceFileName = practiceFileName.format(LISTID=self.contestList)
                elif practiceMode.lower() == "revise":
                    practiceFileName = SB_STUDY_DIR + SB_REVISION_WORD_FILE

                currentPracticeWordList = []

                # Get previously saved practice words
                if os.path.isfile(practiceFileName) and os.path.getsize(practiceFileName) > 0:
                    currentPracticeWordList = cfile.read(practiceFileName).splitlines()                # Use of splitlines() avoids the newline character from being stored in the word list

                # Save practice words to practice file, if not already saved
                for word in self.activePracticeWords:
                    
                    DEBUG_VAR="word"
                    coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format(DEBUG_VAR, type(word)))
                    coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, eval(DEBUG_VAR))

                    practiceFileText = SB_EMPTY_STRING
                    if word not in currentPracticeWordList:
                        practiceFileText = practiceFileText + word + SB_NEWLINE

                if practiceFileText != SB_EMPTY_STRING:
                    cfile.append(practiceFileName, practiceFileText)

    def display_evaluation_result(self, practiceMode, saveResultEnabled, savePracticeEnabled):

        if practiceMode.lower() == "test":
            testHeader  = unicode("=============== Start of Test Log ===============", 'utf-8')
            testTrailer = unicode("================ End of Test Log ================", 'utf-8')
            testFileName = SB_DATA_DIR + SB_TEST_LOG

        elif practiceMode.lower() == "revise":
            testHeader  = unicode("=============== Start of Revision Log ===============", 'utf-8')
            testTrailer = unicode("================ End of Revision Log ================", 'utf-8')
            testFileName = SB_DATA_DIR + SB_REVISION_LOG
     
        # Test header
        testStats = SB_NEWLINE + unicode("Spelling Bee {0}".format(self.contestList), 'utf-8')
        testStats += SB_NEWLINE + unicode("Word Count [{0}] Chapter [{1}/{2}] Words [{3}-{4}]".format(self.word_count(), self.activeChapter, self.chapter_count(), self.activeRangeStart + 1, self.activeRangeEnd + 1), 'utf-8')
        testStats += SB_NEWLINE + SB_NEWLINE + unicode("Test Date [{0}] Score [{1}]".format(self.activeTestDate, self.activeTestScore), 'utf-8')

        displayText = testStats
        print displayText,

        logText = testHeader + testStats

        # Test valuations
        # Print colorized test valuations
        coloredTestValuations = []
        for valuation in self.activeTestValuations:
            if re.match('^' + SB_RIGHT_SYMBOL + '.*', valuation):
                textColor = coutput.get_term_color('green', 'normal', 'normal')
            else:
                textColor = coutput.get_term_color('red', 'normal', 'normal')
            coloredTestValuations.append(textColor + valuation + coutput.get_term_color('normal', 'normal', 'normal'))

        print SB_NEWLINE,
        coutput.print_columnized_list(coloredTestValuations, SB_COLUMN_COUNT)

        columnizedTestValuations = coutput.columnize(self.activeTestValuations, SB_COLUMN_COUNT)
        for row in columnizedTestValuations:
            logText += SB_NEWLINE
            for col in row:
                logText += col

        # Test practice words
        if len(self.activePracticeWords) > 0:
            practiceWordsText = SB_NEWLINE + unicode("Practice Words:", 'utf-8')
            for row in coutput.columnize(self.activePracticeWords, SB_COLUMN_COUNT):
                practiceWordsText += SB_NEWLINE
                for col in row:
                    practiceWordsText += col
                
            print practiceWordsText,

            logText += SB_NEWLINE + practiceWordsText

        # Test trailer
        logText += SB_NEWLINE + testTrailer + SB_NEWLINE

        if saveResultEnabled:
            # Save practice words
            self.save_evaluation_practice_words(practiceMode, savePracticeEnabled)

            # Save test log
            cfile.append(testFileName, logText)


def init_app():
    # Clear screen
    os.system("clear")

    # Suspend input from stdin
    cinput.set_term_input(False)

def exit_app():
    # Resume input from stdin
    cinput.set_term_input(True)

    print "\n\nThank you for practicing for Spelling Bee.\n"
    exit()

def display_help(runMode):
    if runMode.lower() == "test":
        print "\n{0} Keyboard Menu: {1}".format(runMode.title(), SB_TEST_KEYBOARD_MENU)
    elif runMode.lower() == "revise":
        print "\n{0} Keyboard Menu: {1}".format(runMode.title(), SB_REVISE_KEYBOARD_MENU)
    else:
        print "\n{0} Keyboard Menu: {1}".format(runMode.title(), SB_PRACTICE_KEYBOARD_MENU)


# todo: Implement goto feature to specify new start/stop words
def run_practice(spellBee, practiceMode):

    userPracticeMode = practiceMode.strip().lower()

    if userPracticeMode == "study":
        spellBee.print_active_word_list()
    else:
        spellBee.display_about()
    display_help(userPracticeMode)
    userInput = cinput.get_keypress("\nReady to {0}? Press any key when ready ... ".format(userPracticeMode))

    activeWordIndex = 0

    while True:
        if (activeWordIndex < 0) or (activeWordIndex >= len(spellBee.activeWordIndexList)):
            break

        wordIndex = spellBee.activeWordIndexList[activeWordIndex]

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
                activeWordIndex += 1
                break
            # Move to [p]revious word
            elif userInput.lower() == "p":
                activeWordIndex -= 1
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
                print SB_EMPTY_STRING
                spellBee.print_active_word_list()
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # [S]how current word spelling
            elif userInput.lower() == "s":
                spellBee.display_word_cue(SB_STUDY_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1, WORD=spellBee.wordList[wordIndex]))
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # [L]ookup word definition and pronunciation
            elif userInput.lower() == "l":
                userLookupWord = cinput.get_input("\nEnter word to be looked up: ")
                spellBee.lookup_all_dictionaries_by_word(userLookupWord)
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # Display [h]elp and statistics
            elif userInput.lower() == "h":
                print SB_EMPTY_STRING
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


def run_test(spellBee):
    _FUNC_NAME_ = "run_test"

    spellBee.display_about()
    display_help("test")
    userInput = cinput.get_keypress("\nReady for the test? Press any key when ready ... ")

    testDate = time.strftime('%a %d-%b-%Y %H:%M:%S')
    testTotalCount = spellBee.active_word_count()
    testCorrectCount = 0

    userResponse = SB_EMPTY_STRING
    testValuation = SB_EMPTY_STRING

    spellBee.reset_test_result()

    
    # Disable saving practice words if :
    # saving is disabled for test results, or
    # the test is based on practice, revision or wild card lists
    savePracticeWordsEnabled = SB_TEST_SAVE_PRACTICE
    if SB_TEST_SAVE_RESULT == False or 'practice' in spellBee.contestList.lower() or 'revision' in spellBee.contestList.lower() or '*' in spellBee.contestList:
        savePracticeWordsEnabled = False
    coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "SB_TEST_SAVE_PRACTICE :: {0}".format(SB_TEST_SAVE_PRACTICE))
    coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "savePracticeWordsEnabled :: {0}".format(savePracticeWordsEnabled))

    activeWordIndex = 0

    while True:
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "activeWordIndexList :: {0}".format(spellBee.activeWordIndexList))
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "activeWordIndex :: {0}".format(activeWordIndex))
        if (activeWordIndex < 0) or (activeWordIndex >= len(spellBee.activeWordIndexList)):
            break

        wordIndex = spellBee.activeWordIndexList[activeWordIndex]
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "wordIndex :: {0}".format(wordIndex))

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

        # Display [h]elp and statistics
        elif userResponse.lower() == "h":
            print SB_EMPTY_STRING
            spellBee.display_about()
            display_help("test")
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
            # Handle display text in ascii
            asciiTestValuation = testValuation.encode('utf-8')
            if correctResponse:
                coutput.print_color('green', " " * 50 + asciiTestValuation)
            else:
                coutput.print_color('red', " " * 50 + asciiTestValuation)
            
            # Save valuation
            spellBee.log_test_valuation(testValuation)

            # Move to next word
            activeWordIndex += 1
    
    spellBee.log_test_result(testDate, str(testCorrectCount) + "/" + str(testTotalCount))
    print "\nYour test is complete. Displaying results..."
    
    spellBee.display_evaluation_result('test', SB_TEST_SAVE_RESULT, savePracticeWordsEnabled)


def run_revision(spellBee):
    _FUNC_NAME_ = "run_revision"

    spellBee.print_active_word_list()
    display_help("revise")
    userInput = cinput.get_keypress("\nReady to revise? Press any key when ready ... ")

    testDate = time.strftime('%a %d-%b-%Y %H:%M:%S')
    testTotalCount = spellBee.active_word_count()
    testCorrectCount = 0

    userResponse = SB_EMPTY_STRING
    testValuation = SB_EMPTY_STRING

    spellBee.reset_test_result()
  
    activeWordIndex = 0

    while True:
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "activeWordIndexList :: {0}".format(spellBee.activeWordIndexList))
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "activeWordIndex :: {0}".format(activeWordIndex))
        if (activeWordIndex < 0) or (activeWordIndex >= len(spellBee.activeWordIndexList)):
            break

        wordIndex = spellBee.activeWordIndexList[activeWordIndex]
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "wordIndex :: {0}".format(wordIndex))

        # Lookup word definition
        spellBee.lookup_dictionary_by_index(wordIndex)
        spellBee.display_word_cue(SB_STUDY_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1, WORD=spellBee.activeWord))
        userResponse = cinput.get_keypress("Enter response: ")

        # E[x]it test
        if userResponse.lower() == "x":
            break

        # Re[v]iew active word list
        elif userResponse.lower() == "v":
            print SB_EMPTY_STRING
            spellBee.print_active_word_list()
            continue

        # Display [h]elp and statistics
        elif userResponse.lower() == "h":
            print SB_EMPTY_STRING
            spellBee.display_about()
            display_help("revise")
            continue

        # Process correct response
        elif userResponse.lower() == "y":
            correctResponse = True
            testValuation = SB_RIGHT_SYMBOL + " " + spellBee.activeWord
            testCorrectCount += 1

            # Display valuation
            # Handle display text in ascii
            asciiTestValuation = testValuation.encode('utf-8')
            coutput.print_color('green', " " * 50 + asciiTestValuation)

            # Save valuation
            spellBee.log_test_valuation(testValuation)

            # Move to next word
            activeWordIndex += 1

        # Process incorrect response
        elif userResponse.lower() == "n":
            correctResponse = False
            testValuation = SB_WRONG_SYMBOL + " " + spellBee.activeWord
            spellBee.log_practice_word(spellBee.activeWord)

            # Display valuation
            # Handle display text in ascii
            asciiTestValuation = testValuation.encode('utf-8')
            coutput.print_color('red', " " * 50 + asciiTestValuation)

            # Save valuation
            spellBee.log_test_valuation(testValuation)

            # Move to next word
            activeWordIndex += 1

        # [R]epeat question as default action
        else:
            continue
    
    spellBee.log_test_result(testDate, str(testCorrectCount) + "/" + str(testTotalCount))
    print "\nYour revision is complete. Displaying results..."
    
    spellBee.display_evaluation_result('revise', SB_TEST_SAVE_RESULT, True)


def run_error_scan(spellBee):

    spellBee.display_about()
    userInput = cinput.get_keypress("\nReady for error scan? Press any key when ready ... ")
    print SB_EMPTY_STRING

    activeWordIndex = 0

    while True:
        if (activeWordIndex < 0) or (activeWordIndex >= len(spellBee.activeWordIndexList)):
            break

        wordIndex = spellBee.activeWordIndexList[activeWordIndex]

        # Lookup word definition
        spellBee.lookup_dictionary_by_index(wordIndex)
        displayText = unicode("Scanned word #{0}: {1}", 'utf-8')
        print displayText.format(wordIndex + 1, spellBee.activeWord)

        # Move to next word
        activeWordIndex += 1
    
    displayText = unicode("\nError scan is complete. All errors are logged to {0}{1}.", 'utf-8')
    print displayText.format(SB_DATA_DIR, SB_ERR_LOG)
    

################################################################
# Main Program
################################################################

# Process command line arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("runMode", type=str, choices=['study', 'practice', 'test', 'revise', 'scan'], help="is study, practice, test, revise or scan")
argParser.add_argument("contestList", type=str, help="is the word list identifier for the contest in YYYY[-language][-challenge] format")
argParser.add_argument("mode", type=str, choices=['chapter', 'count', 'word', 'random'], nargs='?', default='count', help="is chapter, count, word or random")
argParser.add_argument("selection", type=str, nargs='?', default='1', help="is the chapter number, word index range, word range or random sample size")
args = argParser.parse_args()

# Setup Spelling Bee word list
spellBee = SpellingBee(args.contestList, args.mode, args.selection)

try:
    init_app()

    # Run Spelling Bee assistant in practice, test or scan mode
    if args.runMode.lower() == "study" or args.runMode.lower() == "practice":
        run_practice(spellBee, args.runMode.lower())
    elif args.runMode.lower() == "test":
        run_test(spellBee)
    elif args.runMode.lower() == "revise":
        run_revision(spellBee)
    elif args.runMode.lower() == "scan":
        run_error_scan(spellBee)

    exit_app()

except Exception as e:
    # Logs the error appropriately
    logging.error(traceback.format_exc())
    print "\nERROR: " + traceback.format_exc()

    # Resume input from stdin
    cinput.set_term_input(True)
    
########################################################################
# Debugging Commands
########################################################################
'''
cd $PROJ
sudo python spelling_bee.py study 2016-004-french-challenge
sudo python spelling_bee.py practice 2016-004-french-challenge
sudo python spelling_bee.py test 2016-004-french-challenge
sudo python spelling_bee.py revise 2016-004-french-challenge
sudo python spelling_bee.py scan 2016-004-french-challenge
'''
