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

################################################################
# Message color codes
# White : Normal text - words, definitions, etc.
# Cyan  : Pronunciations; Tips
# Green : Spelling rules; Positive test results
# Red   : Error messages; Negative test results
# Yellow: Warning messages
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
import random
import glob

import traceback
import logging

sys.path.insert(0, "..")
import common.rpimod.stdio.input as cinput
import common.rpimod.stdio.output as coutput
import common.rpimod.stdio.fileio as cfile
import common.rpimod.wordproc.dict.dictionaryapi as cdictassist
import common.rpimod.wordproc.dict.mwcollegiateapi as cdictapi

# Set to True to turn debug messages on
#SB_ERR_DEBUG = True
SB_ERR_DEBUG = False

################################################################
# Spelling Bee Configuration variables
################################################################

SB_CHAPTER_SIZE = 50

SB_DEFINITION_COUNT = 3
SB_DEFINITION_HIDE_EXPLICIT = True                              # Set to True if definitions containing the word are to be hidden
SB_COLUMN_COUNT = 5
SB_GUIDE_COLUMN_COUNT = 4
SB_KEY_COLUMN_COUNT = 2

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

SB_ERR_LOG = "log/spelling_bee_errors.log"
SB_TEST_LOG = "log/spelling_bee_tests.log"
SB_CURRENT_TEST_LOG = "log/spelling_bee_current_test.log"
SB_REVISION_LOG = "log/spelling_bee_revision.log"

SB_RULEBOOK_MULTI_FILES = SB_DATA_DIR + "spelling_bee_*rulebook.txt"

SB_WORD_MULTI_FILES = SB_DATA_DIR + "spelling_bee_{WORD_FILE_PATTERN}.txt"
SB_PRACTICE_MULTI_FILES = SB_STUDY_DIR + "spelling_bee_{WORD_FILE_PATTERN}.txt"

SB_PRACTICE_WORD_FILE = "spelling_bee_practice_{LISTID}.txt"

SB_DICT_OFFLINE_DIR = SB_DATA_DIR + 'dict/'
SB_DICT_OFFLINE_ENTR = "sb_{WORD}.xml"
SB_DICT_OFFLINE_CLIP = "sb_{WORD}.wav"

SB_DICT_OVERRIDE_DIR = SB_DATA_DIR + 'dict/override/'
SB_DICT_OVERRIDE_DEFN = "sb_{WORD}.dat"
SB_DICT_OVERRIDE_CLIP = "sb_{WORD}.mp3"
SB_DICT_OVERRIDE_MSG = "sb_{WORD}.msg"

SB_LIST_BULLET = '• '
SB_SPL_BULLET = '✱ '
SB_PROMPT_SYMBOL = "> "
SB_RIGHT_SYMBOL = '√'
SB_WRONG_SYMBOL = 'X'
SB_MASK_SYMBOL = '*'
SB_SPL_SYMBOL = '*'
SB_PRACTICE_KEYBOARD_MENU = "[N]ext [P]revious [R]epeat [G]oto Re[v]iew [S]how [L]ookup [K]ey [H]elp E[x]it"
SB_TEST_KEYBOARD_MENU = "[R]epeat [K]ey [H]elp E[x]it"
SB_REVISE_KEYBOARD_MENU = "[Y]es [N]o [R]epeat Re[v]iew [K]ey [H]elp E[x]it"

SB_STUDY_WORD_DEFN_TITLE = "\nDefinition of word #{INDEX} ({WORD}) [{SEQ}/{COUNT}]:"
SB_PRACTICE_WORD_DEFN_TITLE = "\nDefinition of word #{INDEX} [{SEQ}/{COUNT}]:"
SB_LOOKUP_WORD_DEFN_TITLE = "\nDefinition of {WORD}:"

SB_ERR_CLIP_MISSING = False
SB_ERR_CLIP_MISMATCH = False

SB_NEWLINE = "\n"
SB_EMPTY_STRING = ""
SB_WORD_DELIMITER = ";"


class SpellingBee(object):
    """
    A Spelling Bee assistant to help with word list navigation and dictionary lookup.
    It has the following attributes:
        activeMode:

        contestList: A string representing the word list identifier for the contest in YYYY[-language][-challenge] format
        wordList: A list containing words loaded from wordFile
        vocabList: A list containing vocabulary entries loaded from wordFile

        activeWordIndexList:
        activeChapter: 
        activeRangeStart: 
        activeRangeEnd:

        activeDictEntry:

        activeTestValuations:

        word_count():
        chapter_count():
        active_word_count():
    """
    def __init__(self, runMode, listID, mode, selection, silentMode):
        _FUNC_NAME_ = "__init__"

        self.runMode = runMode.lower()
        self.activeMode = mode.lower()
        self.silentMode = silentMode
        self.contestList = listID
        self.wordList = []
        self.vocabList = []
        self.ruleBook = {}

        self.enableSaveResults = SB_TEST_SAVE_RESULT
        self.enableSavePracticeWords = SB_TEST_SAVE_PRACTICE
        # Disable saving practice words if:
        #   saving is disabled for test results, or
        #   the test is based on practice, revision or wild card lists
        if self.enableSaveResults == False or self.contestList.lower() in ['practice', 'revision'] or '*' in self.contestList:
            self.enableSavePracticeWords = False

        # Setup and configure dictionary
        self.dictConfig = cdictapi.DictionaryConfig()
        self.dictAssist = cdictassist.DictionaryAssistant(self.dictConfig)

        # Setup connection pool
        self.connectionPool = urllib3.PoolManager(10, headers=SB_USER_AGENT)

        # Setup rulebook for advanced techniques
        wordFileDir = SB_RULEBOOK_MULTI_FILES

        for wordFileName in sorted(glob.glob(wordFileDir)):
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'wordFileName')

            for ruleLine in cfile.read(wordFileName).splitlines():
                ruleSegments = ruleLine.split(SB_WORD_DELIMITER)
                ruleEtymology = ruleSegments[0].strip()
                ruleTechnique = ruleSegments[1].strip()
                ruleWords = [w.strip().lower() for w in ruleSegments[2].split(",")]

                for ruleWord in ruleWords:
                    if (ruleWord in self.ruleBook) == False:
                        self.ruleBook[ruleWord] = {'Etymology': ruleEtymology, 'Rule': [ruleTechnique]}
                    else:
                        self.ruleBook[ruleWord]['Rule'] = self.ruleBook[ruleWord]['Rule'] + [ruleTechnique]

        if re.match(r'^practice', listID):
            wordFileDir = SB_PRACTICE_MULTI_FILES.format(WORD_FILE_PATTERN=listID)
        else:
            wordFileDir = SB_WORD_MULTI_FILES.format(WORD_FILE_PATTERN=listID)

        for wordFileName in sorted(glob.glob(wordFileDir)):
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'wordFileName')

            # Retrieve words from rule book files (*rulebook.txt)
            if re.search(r'rulebook.txt$', wordFileName) and not re.search(r'(practice|revision)', wordFileName):
                ruleWordSet = set()
                for ruleLine in cfile.read(wordFileName).splitlines():
                    ruleSegments = ruleLine.split(";")
                    ruleWords = [w.strip() for w in ruleSegments[2].split(",")]

                    for ruleWord in ruleWords:
                        ruleWordSet.add(ruleWord)
                    
                for ruleWord in ruleWordSet:
                    self.wordList = self.wordList + [ruleWord]
                    self.vocabList = self.vocabList + [None]

            # Retrieve words and vocabulary entries from word list files (*.txt)
            else:
                # Use of splitlines() avoids the newline character from being stored in the word list
                entryList = cfile.read(wordFileName).splitlines()
                for entry in entryList:
                    entryElements = entry.split("|")
                    self.wordList = self.wordList + [entryElements[0]]
                    if len(entryElements) > 1:
                        self.vocabList = self.vocabList + [entryElements[1]]
                    else:
                        self.vocabList = self.vocabList + [None]

        rangeSelection = selection.split("-")
        self.activeChapter = "0"

        if self.activeMode == "chapter":
            self.activeChapter = int(rangeSelection[0])
            self.activeRangeStart = (self.activeChapter - 1) * SB_CHAPTER_SIZE
            self.activeRangeEnd = self.activeRangeStart + SB_CHAPTER_SIZE - 1
            self.activeWordIndexList = list(range(self.activeRangeStart, self.activeRangeEnd+1))

        elif self.activeMode == "count":
            self.activeRangeStart = int(rangeSelection[0]) - 1
            if len(rangeSelection) > 1:
                self.activeRangeEnd = int(rangeSelection[1]) - 1
            else:
                self.activeRangeEnd = len(self.wordList) - 1
            self.activeWordIndexList = list(range(self.activeRangeStart, self.activeRangeEnd+1))

        elif self.activeMode == "word":
            self.activeRangeStart = self.get_word_index(rangeSelection[0])
            if self.activeRangeStart < 0:
                coutput.print_err("Unable to locate '{0}' in word list".format(rangeSelection[0]))
                exit(1)

            if len(rangeSelection) > 1:
                self.activeRangeEnd = self.get_word_index(rangeSelection[1])
                if self.activeRangeEnd < 0:
                    coutput.print_err("Unable to locate '{0}' in word list".format(rangeSelection[1]))
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

            self.activeWordIndexList = random.sample(range(0, self.word_count()), sampleSize)

        if self.activeMode != "random":
            if self.activeRangeEnd >= len(self.wordList):
                self.activeRangeEnd = len(self.wordList) - 1

        self.activeWord = SB_EMPTY_STRING
        self.activeEntry = SB_EMPTY_STRING
        self.activeDictEntry = None

        self.activeTestDate = time.strftime('%a %d-%b-%Y %H:%M:%S')
        self.activeTestScore = SB_EMPTY_STRING
        self.activeTestValuations = []
        self.activePracticeWords = []


    def shut_down(self):
        _FUNC_NAME_ = "shut_down"

        # Close connection
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self')
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.connectionPool')
        if self.connectionPool is not None:
            self.connectionPool.clear()


    def __del__(self):
        _FUNC_NAME_ = "__del__"

        # No action required


    def word_count(self):
        return len(self.wordList)

    def chapter_count(self):
        return int(math.ceil(float(len(self.wordList))/float(SB_CHAPTER_SIZE)))

    def active_word_count(self):
        return len(self.activeWordIndexList)

    def display_about(self):
        _FUNC_NAME_ = "display_about"

        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeMode')

        if self.silentMode:
            print("Spelling Bee {0} (Silent Mode)".format(self.contestList))
        else:
            print("Spelling Bee {0}".format(self.contestList))

        if self.activeMode == "chapter":
            print("Word Count [{0}] Chapter [{1}/{2}] Words [{3}-{4}]".format(self.word_count(), self.activeChapter, self.chapter_count(), self.activeRangeStart + 1, self.activeRangeEnd + 1))

        elif self.activeMode == "random":
            print("Word Count [{0}] Random [{1}]".format(self.word_count(), self.active_word_count()))

        else:
            print("Word Count [{0}] Words [{1}-{2}]".format(self.word_count(), self.activeRangeStart + 1, self.activeRangeEnd + 1))

    def print_active_word_list(self):
        self.display_about()
        print(SB_EMPTY_STRING)
        coutput.print_columnized_slice(self.wordList, self.activeWordIndexList, SB_COLUMN_COUNT)

    def get_word_index(self, searchWord):
        resultIndex = -1
        for wordIndex, word in enumerate(self.wordList, start=0):
            if re.match('^' + searchWord.lower() + '.*', word.lower()):
                resultIndex = wordIndex
                break
        return resultIndex

    def get_active_word_index(self, searchWord):
        resultIndex = -1

        wordIndex = self.get_word_index(searchWord)
        if wordIndex > -1 and wordIndex in self.activeWordIndexList:
            resultIndex = self.activeWordIndexList.index(wordIndex)

        return resultIndex

    def lookup_dictionary_by_word(self, word):
        _FUNC_NAME_ = "lookup_dictionary_by_word"

        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'word')

        self.activeWordAlternatives = word.strip()
        activeWordAlternativesList = [w.strip() for w in self.activeWordAlternatives.split(SB_WORD_DELIMITER)]
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'activeWordAlternativesList')

        self.activeWord = activeWordAlternativesList[0]
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeWord')
       
        # Setup error logging
        errorFileName = SB_DATA_DIR + SB_ERR_LOG
        SB_ERR_CLIP_MISSING = False
        SB_ERR_CLIP_MISMATCH = False

        self.activeEntry = SB_EMPTY_STRING
        self.activeDictEntry = None      

        # Pass #1: Check primary source offline for word entry
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Pass #1: Check primary source offline for word entry")
        offlineEntryFileName = SB_DICT_OFFLINE_DIR + SB_DICT_OFFLINE_ENTR.format(WORD=self.activeWord).replace(" ", "_")

        if os.path.isfile(offlineEntryFileName) and os.path.getsize(offlineEntryFileName) > 100:
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'os.path.getsize(offlineEntryFileName)')
            
            self.activeEntry = cfile.read(offlineEntryFileName)
  
            # Set active dictionary entry
            self.activeDictEntry = cdictapi.DictionaryEntry(self.dictConfig, self.activeWord, self.activeEntry).simplified_word_entry

            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeDictEntry')

        # Pass #2: Check primary source online for word entry
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Pass #2: Check primary source online for word entry")
        if self.activeDictEntry is None:
            # Download dictionary entry
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'offlineEntryFileName')
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeWord')
            self.activeEntry = self.dictAssist.download_entry(self.connectionPool, self.activeWord)
            
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Saving offline dictionary entry to file")
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeEntry')

            # Save dictionary entry offline
            cfile.write(offlineEntryFileName, self.activeEntry)

            # Set active dictionary entry
            if os.path.isfile(offlineEntryFileName) and os.path.getsize(offlineEntryFileName) > 100:
                self.activeDictEntry = cdictapi.DictionaryEntry(self.dictConfig, self.activeWord, self.activeEntry).simplified_word_entry
    
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeDictEntry')

        # Pass #3A: Check for dictionary definition and respelling override
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Pass #3A: Check for dictionary definition and respelling override")
        overrideDefnFileName = SB_DICT_OVERRIDE_DIR + SB_DICT_OVERRIDE_DEFN.format(WORD=self.activeWord).replace(" ", "_")

        if os.path.isfile(overrideDefnFileName) and os.path.getsize(overrideDefnFileName) > 0:
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'overrideDefnFileName')
            overrideSource = "[Dictionary Definition Override]"
            self.activeEntry = overrideSource

            if self.activeDictEntry is None:
                # Set active dictionary entry
                self.activeDictEntry = cdictapi.DictionaryEntry(self.dictConfig, self.activeWord, self.activeEntry).simplified_word_entry
            
            # Override definition and respelling, if any
            self.activeDictEntry.override_definitions(overrideSource, self.activeWord, cfile.read(overrideDefnFileName).splitlines())
   
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeDictEntry')

        # Pass #3B: Check for word list definition override
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Pass #3B: Check for word list definition override")
        
        override_definition = self.vocabList[self.get_word_index(self.activeWord)]
        if override_definition is not None:
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'override_definition')
            overrideSource = "[Word List Definition Override]"
            self.activeEntry = overrideSource

            if self.activeDictEntry is None:
                # Set active dictionary entry
                self.activeDictEntry = cdictapi.DictionaryEntry(self.dictConfig, self.activeWord, self.activeEntry).simplified_word_entry
            
            # Override definition
            self.activeDictEntry.override_definitions(overrideSource, self.activeWord, [SB_SPL_SYMBOL + override_definition])
   
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeDictEntry')

        # Pass #4: Check primary source offline for word pronunciation
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Pass #4: Check primary source offline for word pronunciation")
        offlineProncnFileName = SB_DICT_OFFLINE_DIR + SB_DICT_OFFLINE_CLIP.format(WORD=self.activeWord).replace(" ", "_")

        if os.path.isfile(offlineProncnFileName) and os.path.getsize(offlineProncnFileName) > 1000:
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'os.path.getsize(offlineProncnFileName)')
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeWord')

            offlineProncnURL = "[Offline Dictionary Pronunciation]"
            offlineProncnForm = "[Offline Dictionary Pronunciation Form]"
            offlineProncnSpell = "[Offline Dictionary Pronunciation Spelling]"

            self.activeDictEntry.set_offline_pronunciation(offlineProncnURL, offlineProncnForm, offlineProncnSpell, offlineProncnFileName)

            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeDictEntry')

        # Pass #5: Check for dictionary pronunciation override
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Pass #5: Check for dictionary pronunciation override")
        overrideProncnFileName = SB_DICT_OVERRIDE_DIR + SB_DICT_OVERRIDE_CLIP.format(WORD=self.activeWord).replace(" ", "_")
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'overrideProncnFileName')

        if os.path.isfile(overrideProncnFileName) and os.path.getsize(overrideProncnFileName) > 0:
            overrideProncnForm = self.activeWord
            overrideProncnSpell = self.activeWord

            if self.activeDictEntry is None:
                # Set active dictionary entry
                self.activeDictEntry = cdictapi.DictionaryEntry(self.dictConfig, self.activeWord, self.activeEntry).simplified_word_entry

            self.activeDictEntry.override_pronunciation(overrideProncnForm, overrideProncnSpell, overrideProncnFileName)

            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeDictEntry')

        # Pass #6: Check primary source online for word pronunciation
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Pass #6: Check primary source online for word pronunciation")

        if self.activeDictEntry is not None and self.activeDictEntry.has_pronunciation() and self.activeDictEntry.has_pronunciation_audio() is False:

            # Download and save pronunciation audio offline
            cfile.download(self.connectionPool, self.activeDictEntry.pronunciation.audio_url, offlineProncnFileName)

            if os.path.isfile(offlineProncnFileName) and os.path.getsize(offlineProncnFileName) > 1000:
                onlineProncnURL = "[Online Dictionary Pronunciation URL]"
                onlineProncnForm = "[Online Dictionary Pronunciation Form]"
                onlineProncnSpell = "[Online Dictionary Pronunciation Spelling]"

                self.activeDictEntry.set_offline_pronunciation(onlineProncnURL, onlineProncnForm, onlineProncnSpell, offlineProncnFileName)

                coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeDictEntry')

        # Check and log errors
        wordToken = coutput.tokenize(self.activeWord)

        pronunciationToken = SB_EMPTY_STRING
        if self.activeDictEntry is not None and self.activeDictEntry.has_pronunciation():
            pronunciationToken = coutput.tokenize(self.activeDictEntry.pronunciation.spelling)

        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'wordToken')
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'pronunciationToken')
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeDictEntry')
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeDictEntry.has_mispronunciation()')
       
        errorText = "ERROR:{0}:".format(self.activeWord)

        if self.activeDictEntry is None or self.activeDictEntry.has_definitions() is False:
            errorText += ">Definition Missing"
        
        if self.activeDictEntry is None or self.activeDictEntry.has_pronunciation() is False:
            errorText += ">Audio Missing"
        elif wordToken != pronunciationToken or (self.activeDictEntry is not None and self.activeDictEntry.has_mispronunciation()):
            errorText += ">Audio Mismatch"
        
        if errorText != "ERROR:{0}:".format(self.activeWord):
            errorText += "\n"
            cfile.append(errorFileName, errorText)

        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'errorText')


    def lookup_dictionary_by_index(self, index):
        self.lookup_dictionary_by_word(self.wordList[index])


    def lookup_all_dictionaries_by_word(self, word):
        _FUNC_NAME_ = "lookup_all_dictionaries_by_word"

        cdictall.lookup_word(self.connectionPool, SB_AUDIO_OUTPUT, SB_REPEAT_COUNT, SB_REPEAT_DELAY, word)


    def mask_active_word(self, text, mask_flag):
        _FUNC_NAME_ = "mask_active_word"

        if mask_flag:
            return re.sub(self.activeWord, SB_MASK_SYMBOL * len(self.activeWord), text, flags=re.IGNORECASE)
        else:
            return text

       
    def print_word_definition(self):
        _FUNC_NAME_ = "print_word_definition"

        if self.activeDictEntry is None or self.activeDictEntry.has_definitions() is False:
            coutput.print_err("Unable to lookup dictionary definition")
        else:
            # Print definitions
            definitionIndex = 0
            for definition in self.activeDictEntry.definitions:
                coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'definition')
                               
                # Ignore comments and info lines with # prefix
                if re.match(r'^#', definition):
                    pass
                else:
                    if definitionIndex >= SB_DEFINITION_COUNT:
                        break

                    # Mask definitions that contain the word itself and remove importance prefix "*"
                    masked_definition = re.sub('^\*', SB_EMPTY_STRING, self.mask_active_word(definition, SB_DEFINITION_HIDE_EXPLICIT), flags=re.IGNORECASE)

                    # Check for override definitions from the word list prefixed with "*"
                    if re.match(r'^\*', definition):
                        coutput.print_color('cyan', SB_SPL_BULLET + masked_definition )
                    else:
                        print(SB_LIST_BULLET + masked_definition)
                    
                    definitionIndex += 1

            # Print info lines
            for definition in self.activeDictEntry.definitions:
                coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'definition')

                # Print info with #! prefix

                # Ignore extraneous info lines
                if definition.startswith(('#!Source:', '#!AudioURL:', '#!Meta:')):
                    pass
                elif re.match(r'^#!', definition):
                    infoText = re.sub('^#!', SB_EMPTY_STRING, definition, flags=re.IGNORECASE)

                    # Mask info lines that contain the word itself
                    coutput.print_color('cyan', self.mask_active_word(infoText, SB_DEFINITION_HIDE_EXPLICIT))


    def pronounce_word(self):
        _FUNC_NAME_ = "pronounce_word"

        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeDictEntry.has_pronunciation_audio()')

        if self.activeDictEntry is None:
            coutput.print_err("Unable to lookup audio pronunciation")
        else:
            if self.activeDictEntry.has_respelling():            
                coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeDictEntry.respelling')
                coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'self.activeDictEntry.respelling.text')
                coutput.print_color('cyan', 'Respelling: ' + self.activeDictEntry.respelling.text )
            
            if not self.silentMode:
                if self.activeDictEntry.has_pronunciation_audio() is False:
                    coutput.print_err("Unable to lookup audio pronunciation")

                else:
                    keyWord = self.activeWord

                    if self.activeDictEntry.has_pronunciation():
                        entryWord = self.activeDictEntry.pronunciation.spelling
                    else:
                        entryWord = SB_EMPTY_STRING

                    coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'keyWord')
                    coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'entryWord')
                   
                    self.dictAssist.compare_word_form(keyWord, entryWord)

                    coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Executing cfile.play")
                    
                    cfile.play(self.activeDictEntry.pronunciation.audio_file, SB_AUDIO_OUTPUT, SB_REPEAT_COUNT, SB_REPEAT_DELAY)


    def print_word_tip(self):
        overrideTipFileName = SB_DICT_OVERRIDE_DIR + SB_DICT_OVERRIDE_MSG.format(WORD=self.activeWord).replace(" ", "_")

        # Check for word message/instruction override
        if os.path.isfile(overrideTipFileName) and os.path.getsize(overrideTipFileName) > 0:
            activeTip = cfile.read(overrideTipFileName)
            coutput.print_tip(activeTip)


    def print_word_rule(self):
        # Check for word rules
        if self.activeWord.lower() in self.ruleBook:
            coutput.print_color('green', 'RULE BOOK: ' + self.ruleBook[self.activeWord.lower()]['Etymology'])
            for rule in self.ruleBook[self.activeWord.lower()]['Rule']:
                coutput.print_color('green', SB_LIST_BULLET + rule)


    def print_pronunciation_key(self):
        _FUNC_NAME_ = "print_pronunciation_key"

        # Retrieve respelling override
        respellText = SB_EMPTY_STRING
        for override in self.activeDictEntry.definitions:
            overrideRespell = re.search(r"#!Respelling: (.*)", override)

            if overrideRespell is not None:
                respellText = overrideRespell.group(1)
                break

        # Retrieve respelling
        if respellText == SB_EMPTY_STRING and self.activeDictEntry.has_respelling():
            respellText = self.activeDictEntry.respelling.text

        if respellText != SB_EMPTY_STRING:
            print("Pronunciation Key:")
            coutput.print_columnized_list(self.dictConfig.pronunciation_key(respellText), SB_KEY_COLUMN_COUNT)
        else:
            print("Pronunciation Guide:")
            coutput.print_columnized_list(self.dictConfig.build_pronunciation_guide(), SB_GUIDE_COLUMN_COUNT)


    def display_word_cue(self, title, testMode):
        _FUNC_NAME_ = "display_word_cue"
        coutput.print_color('green', title)

        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Executing self.print_word_definition")
        self.print_word_definition()

        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Executing self.pronounce_word")
        self.pronounce_word()

        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Executing self.print_word_tip")
        self.print_word_tip()

        if testMode.lower() != "test":
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "Executing self.print_word_rule")
            self.print_word_rule()


    def reset_test_result(self):
        self.activeTestScore = SB_EMPTY_STRING
        self.activeTestValuations = []
        self.activePracticeWords = []


    def normalize_word(self, normWord, normMode):
        
        if isinstance(normWord, str):
            valuationWord = normWord
        else:
            valuationWord = normWord
        
        valuationWord = valuationWord.strip()
        valuationMode = normMode.lower()

        if valuationMode == "easy":
            normDifficultyLevel = 0
        elif valuationMode == "medium":
            normDifficultyLevel = 1
        elif valuationMode == "difficult":
            normDifficultyLevel = 2

        # Rule difficulty goes from high to low
        # Most difficult rule would be relaxed in most number of levels
        if normDifficultyLevel < 2:
            # Relax foreign character restriction
            valuationWord = coutput.normalize(valuationWord)

        if normDifficultyLevel < 1:
            # Relax letter case restriction
            valuationWord = valuationWord.lower()

        return valuationWord


    def valuate_test_response(self, testResponse, testWords, testMode):
        valuationResponse = self.normalize_word(testResponse, testMode)
        valuationWords = [self.normalize_word(testWord, testMode) for testWord in testWords.split(SB_WORD_DELIMITER)]

        valuationResult = False

        for valuationWord in valuationWords:
            if valuationResponse == valuationWord:
                valuationResult = True
                break
    
        return valuationResult


    def log_test_result(self, testScore):
        self.activeTestScore = testScore


    def log_practice_word(self, testWord):
        self.activePracticeWords.append(testWord)


    def log_test_valuation(self, testValuation):
        self.activeTestValuations.append(testValuation)


    def trim_practice_word_list(self):
        _FUNC_NAME_ = "trim_practice_word_list"

        practiceFileName = SB_STUDY_DIR + SB_PRACTICE_WORD_FILE.format(LISTID=self.contestList)

        # Get saved practice words
        currentPracticeWordList = []
        if os.path.isfile(practiceFileName) and os.path.getsize(practiceFileName) > 0:
            currentPracticeWordList = cfile.read(practiceFileName).splitlines()     # Use of splitlines() avoids the newline character from being stored in the word list

        # Remove empty and duplicate practice words
        trimmedPracticeWordList = []
        practiceFileText = SB_EMPTY_STRING
        for word in currentPracticeWordList:
            if word != SB_EMPTY_STRING and word not in trimmedPracticeWordList:
                trimmedPracticeWordList.append(word)
                practiceFileText = practiceFileText + word + SB_NEWLINE

        # Save to practice file
        if practiceFileText != SB_EMPTY_STRING:
            cfile.write(practiceFileName, practiceFileText)


    def save_practice_word(self, word):
        _FUNC_NAME_ = "save_practice_word"

        practiceFileName = SB_STUDY_DIR + SB_PRACTICE_WORD_FILE.format(LISTID=self.contestList)

        if self.enableSavePracticeWords:
            cfile.append(practiceFileName, word)


    def get_current_test_context(self):
        _FUNC_NAME_ = "get_current_test_context"

        # Test Context
        testContext = "Spelling Bee {0}".format(self.contestList)
        testContext += SB_NEWLINE + "Test Date [{0}]".format(self.activeTestDate)

        if self.activeMode == "chapter":
            testContext += SB_NEWLINE + "Word Count [{0}] Chapter [{1}/{2}] Words [{3}-{4}]".format(self.word_count(), self.activeChapter, self.chapter_count(), self.activeRangeStart + 1, self.activeRangeEnd + 1)

        elif self.activeMode == "random":
            testContext += SB_NEWLINE + "Word Count [{0}] Random [{1}]".format(self.word_count(), self.active_word_count())

        else:
            testContext += SB_NEWLINE + "Word Count [{0}] Words [{1}-{2}]".format(self.word_count(), self.activeRangeStart + 1, self.activeRangeEnd + 1)

        return testContext


    def reset_current_test_result(self):
        _FUNC_NAME_ = "reset_current_test_result"

        currResultFileName = SB_DATA_DIR + SB_CURRENT_TEST_LOG
        
        if self.enableSaveResults:
            cfile.write(currResultFileName, self.get_current_test_context())


    def save_current_test_result(self, valuation):
        _FUNC_NAME_ = "save_current_test_result"

        currResultFileName = SB_DATA_DIR + SB_CURRENT_TEST_LOG

        if self.enableSaveResults:
            cfile.append(currResultFileName, valuation)


    def display_evaluation_result(self, practiceMode):

        if practiceMode.lower() == "test":
            testHeader  = "=============== Start of Test Log ==============="
            testTrailer = "================ End of Test Log ================"
            testFileName = SB_DATA_DIR + SB_TEST_LOG

        elif practiceMode.lower() == "revise":
            testHeader  = "=============== Start of Revision Log ==============="
            testTrailer = "================ End of Revision Log ================"
            testFileName = SB_DATA_DIR + SB_REVISION_LOG
     
        # Test header
        testStats = SB_NEWLINE + self.get_current_test_context()
        testStats += SB_NEWLINE + SB_NEWLINE + "Score [{0}]".format(self.activeTestScore)

        displayText = testStats
        print(displayText)

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

        coutput.print_columnized_list(coloredTestValuations, SB_COLUMN_COUNT)

        columnizedTestValuations = coutput.columnize(self.activeTestValuations, SB_COLUMN_COUNT)
        for row in columnizedTestValuations:
            logText += SB_NEWLINE
            for col in row:
                logText += col

        # Test practice words
        if len(self.activePracticeWords) > 0:
            practiceWordsText = SB_NEWLINE + "Practice Words:"
            for row in coutput.columnize(self.activePracticeWords, SB_COLUMN_COUNT):
                practiceWordsText += SB_NEWLINE
                for col in row:
                    practiceWordsText += col
                
            print(practiceWordsText)

            logText += SB_NEWLINE + practiceWordsText

        # Test trailer
        logText += SB_NEWLINE + testTrailer + SB_NEWLINE

        # Save test log
        if self.enableSaveResults:
            cfile.append(testFileName, logText)

        # Trim practice word list
        self.trim_practice_word_list()


def init_app():
    # Clear screen
    os.system("clear")

    # Suspend input from stdin
    cinput.set_term_input(False)


def exit_app():
    # Resume input from stdin
    cinput.set_term_input(True)

    print("\n\nThank you for practicing for Spelling Bee.\n")
    exit()


def display_help(runMode):
    _FUNC_NAME_ = "display_help"

    if runMode.lower() == "test":
        print("\n{0} Keyboard Menu: {1}".format(runMode.title(), SB_TEST_KEYBOARD_MENU))
    elif runMode.lower() == "revise":
        print("\n{0} Keyboard Menu: {1}".format(runMode.title(), SB_REVISE_KEYBOARD_MENU))
    else:
        print("\n{0} Keyboard Menu: {1}".format(runMode.title(), SB_PRACTICE_KEYBOARD_MENU))


def run_practice(spellBee, practiceMode):
    _FUNC_NAME_ = "run_practice"

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
            titleText = SB_STUDY_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1, WORD=spellBee.wordList[wordIndex], SEQ=activeWordIndex + 1, COUNT=len(spellBee.activeWordIndexList))
        else:
            titleText = SB_PRACTICE_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1)

        spellBee.display_word_cue(titleText, userPracticeMode)
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
                spellBee.display_word_cue(titleText, userPracticeMode)
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # Re[v]iew active word list
            elif userInput.lower() == "v":
                print(SB_EMPTY_STRING)
                spellBee.print_active_word_list()
                display_help(userPracticeMode)
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # [S]how current word spelling and dictionary entry
            elif userInput.lower() == "s":
                spellBee.display_word_cue(titleText, userPracticeMode)
                coutput.print_color('cyan', "\nDictionary Entry:")
                #print spellBee.activeDictEntry
                for entryLine in spellBee.activeDictEntry.__unicode__().splitlines():
                    print(entryLine)
                display_help(userPracticeMode)
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # [G]oto to word
            elif userInput.lower() == "g":
                nextWord = cinput.get_input("\nEnter word to be jumped to: ")
                nextIndex = spellBee.get_active_word_index(nextWord)                
                if (nextIndex < 0) or (nextIndex >= len(spellBee.activeWordIndexList)):
                    coutput.print_err("Unable to locate '{0}' in word list".format(nextWord))
                    display_help(userPracticeMode)
                    userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
                else:
                    activeWordIndex = nextIndex
                    break
            # [L]ookup word definition and pronunciation
            elif userInput.lower() == "l":
                print("\nLookup feature under construction.")
                display_help(userPracticeMode)
                #userLookupWord = cinput.get_input("\nEnter word to be looked up: ")
                #spellBee.lookup_all_dictionaries_by_word(userLookupWord)
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # Display pronunciation [k]ey
            elif userInput.lower() == "k":
                print(SB_EMPTY_STRING)
                spellBee.print_pronunciation_key()
                display_help(userPracticeMode)
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # Display [h]elp and statistics
            elif userInput.lower() == "h":
                print(SB_EMPTY_STRING)
                spellBee.display_about()
                display_help(userPracticeMode)
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # E[x]it application
            elif userInput.lower() == "x":
                spellBee.shut_down()
                exit_app()
            else:
                print("\nInvalid response.")
                display_help(userPracticeMode)
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)


def run_test(spellBee):
    _FUNC_NAME_ = "run_test"

    userPracticeMode = "test"

    spellBee.display_about()
    display_help(userPracticeMode)
    userInput = cinput.get_keypress("\nReady for the test? Press any key when ready ... ")

    testTotalCount = spellBee.active_word_count()
    testCorrectCount = 0

    userResponse = SB_EMPTY_STRING
    testValuation = SB_EMPTY_STRING

    spellBee.reset_test_result()
    spellBee.reset_current_test_result()

    activeWordIndex = 0

    while True:
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'spellBee.activeWordIndexList')
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'activeWordIndex')

        if (activeWordIndex < 0) or (activeWordIndex >= len(spellBee.activeWordIndexList)):
            break

        wordIndex = spellBee.activeWordIndexList[activeWordIndex]
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'wordIndex')

        # Lookup word definition
        spellBee.lookup_dictionary_by_index(wordIndex)
        titleText = SB_PRACTICE_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1, SEQ=activeWordIndex + 1, COUNT=len(spellBee.activeWordIndexList))
        spellBee.display_word_cue(titleText, userPracticeMode)
        userResponse = cinput.get_input("Enter spelling: ")

        # E[x]it test
        if userResponse.lower() == "x":
            break

        # [R]epeat question
        elif userResponse.lower() == "r":
            continue

        # Display pronunciation [k]ey
        elif userResponse.lower() == "k":
            print(SB_EMPTY_STRING)
            spellBee.print_pronunciation_key()
            display_help(userPracticeMode)
            continue

        # Display [h]elp and statistics
        elif userResponse.lower() == "h":
            print(SB_EMPTY_STRING)
            spellBee.display_about()
            display_help(userPracticeMode)
            continue

        else:
            correctResponse = False

            # Process correct response
            if spellBee.valuate_test_response(userResponse, spellBee.activeWordAlternatives, SB_TEST_MODE):
                correctResponse = True
                testValuation = SB_RIGHT_SYMBOL + " " + userResponse
                testCorrectCount += 1
            # Process incorrect response
            else:
                testValuation = SB_WRONG_SYMBOL + " " + userResponse
                spellBee.log_practice_word(spellBee.activeWord)
                spellBee.save_practice_word(spellBee.activeWord)

            # Indicate correct form of the answer, if different from the response
            if userResponse != spellBee.activeWord:
                testValuation = testValuation + " (" + spellBee.activeWordAlternatives + ")"

            # Display valuation
            if correctResponse:
                coutput.print_color('green', " " * 50 + testValuation)
            else:
                coutput.print_color('red', " " * 50 + testValuation)
            
            # Save valuation
            spellBee.log_test_valuation(testValuation)
            spellBee.save_current_test_result(testValuation)

            # Move to next word
            activeWordIndex += 1
    
    spellBee.log_test_result(str(testCorrectCount) + "/" + str(testTotalCount))
    print("Your test is complete. Displaying results...")
    
    spellBee.display_evaluation_result(userPracticeMode)


def run_revision(spellBee):
    _FUNC_NAME_ = "run_revision"

    userPracticeMode = "revise"

    spellBee.print_active_word_list()
    display_help(userPracticeMode)
    userInput = cinput.get_keypress("\nReady to revise? Press any key when ready ... ")

    testTotalCount = spellBee.active_word_count()
    testCorrectCount = 0

    userResponse = SB_EMPTY_STRING
    testValuation = SB_EMPTY_STRING

    spellBee.reset_test_result()
    spellBee.reset_current_test_result()
  
    activeWordIndex = 0

    while True:
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'activeWordIndexList')
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'activeWordIndex')

        if (activeWordIndex < 0) or (activeWordIndex >= len(spellBee.activeWordIndexList)):
            break

        wordIndex = spellBee.activeWordIndexList[activeWordIndex]        
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'wordIndex')

        # Lookup word definition
        spellBee.lookup_dictionary_by_index(wordIndex)
        titleText = SB_STUDY_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1, WORD=spellBee.activeWordAlternatives, SEQ=activeWordIndex + 1, COUNT=len(spellBee.activeWordIndexList))
        spellBee.display_word_cue(titleText, userPracticeMode)
        userResponse = cinput.get_keypress("Enter response: ")

        # E[x]it test
        if userResponse.lower() == "x":
            break

        # Re[v]iew active word list
        elif userResponse.lower() == "v":
            print(SB_EMPTY_STRING)
            spellBee.print_active_word_list()
            continue

        # Display pronunciation [k]ey
        elif userResponse.lower() == "k":
            print(SB_EMPTY_STRING)
            spellBee.print_pronunciation_key()
            display_help(userPracticeMode)
            continue

        # Display [h]elp and statistics
        elif userResponse.lower() == "h":
            print(SB_EMPTY_STRING)
            spellBee.display_about()
            display_help(userPracticeMode)
            continue

        # Process correct response
        elif userResponse.lower() == "y":
            correctResponse = True
            testValuation = SB_RIGHT_SYMBOL + " " + spellBee.activeWordAlternatives
            testCorrectCount += 1

            # Display valuation
            coutput.print_color('green', " " * 50 + testValuation)

            # Save valuation
            spellBee.log_test_valuation(testValuation)
            spellBee.save_current_test_result(testValuation)

            # Move to next word
            activeWordIndex += 1

        # Process incorrect response
        elif userResponse.lower() == "n":
            correctResponse = False
            testValuation = SB_WRONG_SYMBOL + " " + spellBee.activeWordAlternatives

            # Save practice word            
            spellBee.log_practice_word(spellBee.activeWord)
            spellBee.save_practice_word(spellBee.activeWord)

            # Display valuation
            coutput.print_color('red', " " * 50 + testValuation)

            # Save valuation
            spellBee.log_test_valuation(testValuation)
            spellBee.save_current_test_result(testValuation)

            # Move to next word
            activeWordIndex += 1

        # [R]epeat question as default action
        else:
            continue
    
    spellBee.log_test_result(str(testCorrectCount) + "/" + str(testTotalCount))
    print("Your revision is complete. Displaying results...")
    
    spellBee.display_evaluation_result(userPracticeMode)


def run_error_scan(spellBee):

    spellBee.display_about()
    userInput = cinput.get_keypress("\nReady for error scan? Press any key when ready ... ")
    print(SB_EMPTY_STRING)

    activeWordIndex = 0

    while True:
        if (activeWordIndex < 0) or (activeWordIndex >= len(spellBee.activeWordIndexList)):
            break

        wordIndex = spellBee.activeWordIndexList[activeWordIndex]

        # Lookup word definition
        spellBee.lookup_dictionary_by_index(wordIndex)
        displayText = str("Scanned word #{0}: {1}", 'utf-8')
        print(displayText.format(wordIndex + 1, spellBee.activeWord))

        # Move to next word
        activeWordIndex += 1
    
    displayText = str("\nError scan is complete. All errors are logged to {0}{1}", 'utf-8')
    print(displayText.format(SB_DATA_DIR, SB_ERR_LOG))
    

################################################################
# Main Program
################################################################

# Process command line arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("runMode", type=str, choices=['study', 'practice', 'test', 'revise', 'scan'], help="is study, practice, test, or revise")
argParser.add_argument("contestList", type=str, help="is the word list identifier for the contest in YYYY[-language][-challenge] format")
argParser.add_argument("mode", type=str, choices=['chapter', 'count', 'word', 'random'], nargs='?', default='count', help="is chapter, count, word or random")
argParser.add_argument("selection", type=str, nargs='?', default='1', help="is the chapter number, word index range, word range or random sample size")
argParser.add_argument("-s", "--silent", help="run in silent mode, without pronunciation", action="store_true")
args = argParser.parse_args()

# Setup Spelling Bee word list and run mode
spellBee = SpellingBee(args.runMode, args.contestList, args.mode, args.selection, args.silent)
spellBeeMode = args.runMode.lower()

try:
    init_app()

    # Run Spelling Bee assistant in practice, test or scan mode
    if spellBeeMode == "study" or spellBeeMode == "practice":
        run_practice(spellBee, spellBeeMode)
    elif spellBeeMode == "test":
        run_test(spellBee)
    elif spellBeeMode == "revise":
        run_revision(spellBee)
    elif spellBeeMode == "scan":
        run_error_scan(spellBee)

    spellBee.shut_down()
    exit_app()

except Exception as e:
    # Logs the error appropriately
    logging.error(traceback.format_exc())
    #print "\nERROR: " + traceback.format_exc()
    coutput.print_err(traceback.format_exc())

    # Resume input from stdin
    cinput.set_term_input(True)
    
########################################################################
# Debugging Commands
########################################################################
'''
. ~/projects/py3-raspi/config/.bashrc
sudo python3 $PROJ/spelling_bee.py study CONTROL

cd $PROJ
sudo python3 spelling_bee.py study 2016-004-french-challenge
sudo python3 spelling_bee.py practice 2016-004-french-challenge
sudo python3 spelling_bee.py test 2016-004-french-challenge
sudo python3 spelling_bee.py revise 2016-004-french-challenge
sudo python3 spelling_bee.py scan 2016-004-french-challenge
'''
