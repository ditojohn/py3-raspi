#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################
# Syntax :   sudo python spelling_bee.py runMode contestList mode selection -s -o
# where      runMode is study, practice, revise, scan or test.
#            contestList is the word list identifier for the contest in YYYY[-language][-challenge] format
#            mode is chapter, count, word, random.
#                In chapter mode, selection is the chapter number of the word list to be practiced.
#                    Default chapter size is 50 words.
#                In count mode, selection is the index range of words in the word list to be practiced.
#                In word mode, selection is the range of words in the word list to be practiced.
#                In random mode, selection is the range of words in the word list to be practiced.
#            -s (--silent) is for silent mode
#            -o (--offline) is for offline mode
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

sys.path.insert(0, "..")
import common.rpimod.stdio.input as cinput
import common.rpimod.stdio.output as coutput
import common.rpimod.stdio.fileio as cfile
import common.rpimod.wordproc.dict.dictionaryapi as cdictassist
import common.rpimod.wordproc.dict.mwcollegiateapi as cdictapi

# Set to True to turn debug messages on
#APP_DEBUG_MODE_ENABLED = True
APP_DEBUG_MODE_ENABLED = False

################################################################
# Configuration variables
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

SB_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}

################################################################
# Application Directories
################################################################

SB_DATA_DIR = "data/"
SB_STUDY_DIR = SB_DATA_DIR + 'study/'
SB_LOG_DIR = SB_DATA_DIR + 'log/'
SB_DICT_OFFLINE_DIR = SB_DATA_DIR + 'dict/'
#SB_DICT_OVERRIDE_DIR = SB_DICT_OFFLINE_DIR + 'override/'

SB_DICT_OVERRIDE_DIR_LIST = [
    SB_DICT_OFFLINE_DIR + 'override/test/',
    SB_DICT_OFFLINE_DIR + 'override/spellpundit/',
    '/home/ditoj/projects/py3-raspi/spelling-bee/data/download/spellpundit/dict/'
]

SB_APP_DIR_LIST = [SB_DATA_DIR, SB_STUDY_DIR, SB_LOG_DIR, SB_DICT_OFFLINE_DIR ] + SB_DICT_OVERRIDE_DIR_LIST

################################################################
# Application Files
################################################################

SB_ERR_LOG = SB_LOG_DIR + "spelling_bee_errors.log"
SB_TEST_LOG = SB_LOG_DIR + "spelling_bee_tests.log"
SB_CURRENT_TEST_LOG = SB_LOG_DIR + "spelling_bee_current_test.log"
SB_REVISION_LOG = SB_LOG_DIR + "spelling_bee_revision.log"

SB_RULEBOOK_MULTI_FILES = SB_DATA_DIR + "spelling_bee_*rulebook.txt"
SB_WORDSET_MULTI_FILES = SB_DATA_DIR + "spelling_bee_*wordset.txt"

SB_WORD_MULTI_FILES = SB_DATA_DIR + "spelling_bee_{WORD_FILE_PATTERN}.txt"
SB_PRACTICE_MULTI_FILES = SB_STUDY_DIR + "spelling_bee_{WORD_FILE_PATTERN}.txt"

SB_PRACTICE_WORD_FILE = "spelling_bee_practice_{LISTID}.txt"

SB_DICT_OFFLINE_ENTR = "sb_{WORD}.xml"
SB_DICT_OFFLINE_CLIP = "sb_{WORD}.wav"

SB_DICT_OVERRIDE_DEFN = "sb_{WORD}.dat"
SB_DICT_OVERRIDE_CLIP = "sb_{WORD}.mp3"
SB_DICT_OVERRIDE_MSG = "sb_{WORD}.msg"

SB_FEEDBACK_RIGHT = SB_DATA_DIR + "sb_feedback_correct.wav"
SB_FEEDBACK_WRONG = SB_DATA_DIR + "sb_feedback_incorrect.wav"

################################################################
# Internal variables
################################################################

SB_LIST_BULLET = '• '
SB_SPL_BULLET = '✱ '
SB_SEC_BULLET = '‣ '
SB_PROMPT_SYMBOL = "> "
SB_RIGHT_SYMBOL = '√'
SB_WRONG_SYMBOL = 'X'
SB_MASK_SYMBOL = '*'
SB_SPL_SYMBOL = '*'

SB_PRI_SEP_SYMBOL = '='
SB_PRI_SEP_LEN = 80

SB_SEC_SEP_SYMBOL = '-'
SB_SEC_SEP_LEN = 80

SB_PRACTICE_KEYBOARD_MENU = "[N]ext [P]revious [R]epeat [G]oto Re[v]iew [S]how [L]ookup [K]ey [H]elp E[x]it"
SB_TEST_KEYBOARD_MENU = "[R]epeat [K]ey [H]elp E[x]it"
SB_REVISE_KEYBOARD_MENU = "[Y]es [N]o [R]epeat Re[v]iew [K]ey [H]elp E[x]it"

SB_STUDY_WORD_DEFN_TITLE = "Definition of word #{INDEX} ({WORD}) [{SEQ}/{COUNT}]:"
SB_PRACTICE_WORD_DEFN_TITLE = "Definition of word #{INDEX} [{SEQ}/{COUNT}]:"
SB_LOOKUP_WORD_DEFN_TITLE = "\nDictionary Entry ({WORD}):"

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
    def __init__(self, runMode, listID, mode, selection, silentMode, offlineMode):

        self.runMode = runMode.lower()
        self.activeMode = mode.lower()
        self.silentMode = silentMode
        self.offlineMode = offlineMode
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

        # Setup application directories
        cfile.make_directory(SB_APP_DIR_LIST)

        # Setup rulebook for advanced techniques
        wordFileDir = SB_RULEBOOK_MULTI_FILES

        for wordFileName in sorted(glob.glob(wordFileDir)):
            coutput.print_watcher('wordFileName')

            for ruleLine in cfile.read(wordFileName).splitlines():
                ruleSegments = ruleLine.split(SB_WORD_DELIMITER)
                ruleCategory = ruleSegments[0].strip()
                ruleTechnique = ruleSegments[1].strip()
                ruleWords = [w.strip().lower() for w in ruleSegments[2].split(",")]

                for ruleWord in ruleWords:
                    if ruleWord not in self.ruleBook:
                        self.ruleBook[ruleWord] = {'Category': ruleCategory, 'Rule': [ruleTechnique]}
                    else:
                        if ruleTechnique not in self.ruleBook[ruleWord]['Rule']:
                            self.ruleBook[ruleWord]['Rule'] = self.ruleBook[ruleWord]['Rule'] + [ruleTechnique]

        coutput.print_watcher('self.ruleBook')
        
        # Setup rulebook for word sets
        wordFileDir = SB_WORDSET_MULTI_FILES

        for wordFileName in sorted(glob.glob(wordFileDir)):
            coutput.print_watcher('wordFileName')

            for ruleLine in cfile.read(wordFileName).splitlines():
                ruleSegments = ruleLine.split("|")
                
                ruleCategory = "Word Set"
                ruleType = ruleSegments[0].strip()
                ruleSegments.pop(0)
                ruleTechnique = "{}: {}".format(ruleType, ", ".join(ruleSegments))

                for ruleSegment in ruleSegments:
                    ruleWords = [w.strip().lower() for w in ruleSegment.split(";")]
                    for ruleWord in ruleWords:
                        if ruleWord not in self.ruleBook:
                            self.ruleBook[ruleWord] = {'Category': ruleCategory, 'Rule': [ruleTechnique]}
                        else:
                            if ruleTechnique not in self.ruleBook[ruleWord]['Rule']:
                                self.ruleBook[ruleWord]['Rule'] = self.ruleBook[ruleWord]['Rule'] + [ruleTechnique]

        if re.match(r'^practice', listID):
            wordFileDir = SB_PRACTICE_MULTI_FILES.format(WORD_FILE_PATTERN=listID)
        else:
            wordFileDir = SB_WORD_MULTI_FILES.format(WORD_FILE_PATTERN=listID)

        for wordFileName in sorted(glob.glob(wordFileDir)):
            coutput.print_watcher('wordFileName')

            # Retrieve words from rule book files (*rulebook.txt)
            if re.search(r'rulebook.txt$', wordFileName) and not re.search(r'(practice|revision)', wordFileName):
                ruleWordSet = set()
                for ruleLine in cfile.read(wordFileName).splitlines():
                    ruleSegments = ruleLine.split(";")
                    ruleWords = [w.strip() for w in ruleSegments[2].split(",")]

                    for ruleWord in ruleWords:
                        ruleWordSet.add(ruleWord)
                    
                for ruleWord in ruleWordSet:
                    self.wordList.append(ruleWord)
                    self.vocabList.append(None)

            # Retrieve words from word set files (*wordset.txt)
            elif re.search(r'wordset.txt$', wordFileName) and not re.search(r'(practice|revision)', wordFileName):
                wordSet = []
                for setLine in cfile.read(wordFileName).splitlines():
                    setSegments = setLine.split("|")
                    
                    setCategory = setSegments[0]
                    setSegments.pop(0)
                    
                    for setSegment in setSegments:
                        setWord = setSegment.strip()
                        if setWord not in wordSet:
                            wordSet.append(setWord)
                            self.wordList.append(setWord)
                            self.vocabList.append(None)

            # Retrieve words and vocabulary entries from word list files (*.txt)
            else:
                # Use of splitlines() avoids the newline character from being stored in the word list
                entryList = cfile.read(wordFileName).splitlines()
                for entry in entryList:
                    entryElements = entry.split("|")
                    self.wordList.append(entryElements[0])
                    if len(entryElements) > 1:
                        self.vocabList.append(entryElements[1])
                    else:
                        self.vocabList.append(None)

            coutput.print_watcher('self.wordList')
            coutput.print_watcher('self.vocabList')

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

        # Close connection
        coutput.print_watcher('self')
        coutput.print_watcher('self.connectionPool')
        if self.connectionPool is not None:
            self.connectionPool.clear()


    def __del__(self):

        # No action required
        pass


    def word_count(self):

        return len(self.wordList)


    def chapter_count(self):

        return int(math.ceil(float(len(self.wordList))/float(SB_CHAPTER_SIZE)))


    def active_word_count(self):

        return len(self.activeWordIndexList)


    def display_about(self):

        coutput.print_watcher('self.activeMode')

        titleText = "Spelling Bee {0}".format(self.contestList)
        if self.silentMode:
            titleText += " [Silent]"
        if self.offlineMode:
            titleText += " [Offline]"
        print(titleText)

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

        coutput.print_watcher('word')

        self.activeWordAlternatives = word.strip()
        activeWordAlternativesList = [w.strip() for w in self.activeWordAlternatives.split(SB_WORD_DELIMITER)]
        coutput.print_watcher('activeWordAlternativesList')

        self.activeWord = activeWordAlternativesList[0]
        coutput.print_watcher('self.activeWord')
       
        # Setup error logging
        SB_ERR_CLIP_MISSING = False
        SB_ERR_CLIP_MISMATCH = False

        self.activeEntry = SB_EMPTY_STRING
        self.activeDictEntry = None      

        # Pass #1: Check primary source offline for word entry
        coutput.print_debug("Pass #1: Check primary source offline for word entry")
        offlineEntryFileName = SB_DICT_OFFLINE_DIR + cfile.cleanse_filename(SB_DICT_OFFLINE_ENTR.format(WORD=self.activeWord))

        if os.path.isfile(offlineEntryFileName) and os.path.getsize(offlineEntryFileName) > 100:
            coutput.print_watcher('os.path.getsize(offlineEntryFileName)')
            
            self.activeEntry = cfile.read(offlineEntryFileName)
  
            # Set active dictionary entry
            self.activeDictEntry = cdictapi.DictionaryEntry(self.dictConfig, self.activeWord, self.activeEntry).simplified_word_entry

            coutput.print_watcher('self.activeDictEntry')

        # Pass #2: Check primary source online for word entry
        coutput.print_debug("Pass #2: Check primary source online for word entry")
        if self.offlineMode is False:
            if self.activeDictEntry is None:
                try:
                    # Download dictionary entry
                    coutput.print_watcher('offlineEntryFileName')
                    coutput.print_watcher('self.activeWord')

                    self.activeEntry = self.dictAssist.download_entry(self.connectionPool, self.activeWord)

                    coutput.print_debug("Saving offline dictionary entry to file")
                    coutput.print_watcher('self.activeEntry')

                    # Save dictionary entry offline
                    cfile.write(offlineEntryFileName, self.activeEntry)

                    # Set active dictionary entry
                    if os.path.isfile(offlineEntryFileName) and os.path.getsize(offlineEntryFileName) > 100:
                        self.activeDictEntry = cdictapi.DictionaryEntry(self.dictConfig, self.activeWord, self.activeEntry).simplified_word_entry
            
                    coutput.print_watcher('self.activeDictEntry')

                except:
                    coutput.print_warn('Unable to connect to the internet. Switching to offline mode.')
                    self.offlineMode = True
            

        # Pass #3A: Check for dictionary definition and respelling override
        coutput.print_debug("Pass #3A: Check for dictionary definition and respelling override")
        overrideDefnFileName = cfile.find_file(cfile.cleanse_filename(SB_DICT_OVERRIDE_DEFN.format(WORD=self.activeWordAlternatives)), SB_DICT_OVERRIDE_DIR_LIST)
        coutput.print_watcher('overrideDefnFileName')

        #if os.path.isfile(overrideDefnFileName) and os.path.getsize(overrideDefnFileName) > 0:
        if overrideDefnFileName is not None:
            coutput.print_watcher('overrideDefnFileName')
            overrideSource = "[Dictionary Definition Override]"
            self.activeEntry = overrideSource

            if self.activeDictEntry is None:
                # Set active dictionary entry
                self.activeDictEntry = cdictapi.DictionaryEntry(self.dictConfig, self.activeWord, self.activeEntry).simplified_word_entry
                coutput.print_watcher('self.activeDictEntry')
            
            # Override definition and respelling, if any
            self.activeDictEntry.override_entry(overrideSource, self.activeWord, cfile.read(overrideDefnFileName).splitlines())
            coutput.print_watcher('self.activeDictEntry')

        # Pass #3B: Check for word list definition override
        coutput.print_debug("Pass #3B: Check for word list definition override")
        
        override_definition = self.vocabList[self.get_word_index(self.activeWord)]
        if override_definition is not None:
            coutput.print_watcher('override_definition')
            overrideSource = "[Word List Definition Override]"
            self.activeEntry = overrideSource

            if self.activeDictEntry is None:
                # Set active dictionary entry
                self.activeDictEntry = cdictapi.DictionaryEntry(self.dictConfig, self.activeWord, self.activeEntry).simplified_word_entry
            
            # Override definition
            self.activeDictEntry.override_entry(overrideSource, self.activeWord, [SB_SPL_SYMBOL + override_definition])
   
            coutput.print_watcher('self.activeDictEntry')

        # Pass #4: Check primary source offline for word pronunciation
        coutput.print_debug("Pass #4: Check primary source offline for word pronunciation")
        offlineProncnFileName = SB_DICT_OFFLINE_DIR + cfile.cleanse_filename(SB_DICT_OFFLINE_CLIP.format(WORD=self.activeWord))

        if os.path.isfile(offlineProncnFileName) and os.path.getsize(offlineProncnFileName) > 1000:
            coutput.print_watcher('os.path.getsize(offlineProncnFileName)')
            coutput.print_watcher('self.activeWord')

            offlineProncnURL = "[Offline Dictionary Pronunciation]"
            offlineProncnForm = "[Offline Dictionary Pronunciation Form]"
            offlineProncnSpell = "[Offline Dictionary Pronunciation Spelling]"

            self.activeDictEntry.set_offline_pronunciation(offlineProncnURL, offlineProncnForm, offlineProncnSpell, offlineProncnFileName)

            coutput.print_watcher('self.activeDictEntry')

        # Pass #5: Check primary source online for word pronunciation
        coutput.print_debug("Pass #5: Check primary source online for word pronunciation")

        if self.offlineMode is False:
            if self.activeDictEntry is not None and self.activeDictEntry.has_pronunciation() and self.activeDictEntry.has_pronunciation_audio() is False:
                try:
                    # Download and save pronunciation audio offline
                    cfile.download(self.connectionPool, self.activeDictEntry.pronunciation.audio_url, offlineProncnFileName)

                    if os.path.isfile(offlineProncnFileName) and os.path.getsize(offlineProncnFileName) > 1000:
                        onlineProncnURL = "[Online Dictionary Pronunciation URL]"
                        onlineProncnForm = "[Online Dictionary Pronunciation Form]"
                        onlineProncnSpell = "[Online Dictionary Pronunciation Spelling]"

                        self.activeDictEntry.set_offline_pronunciation(onlineProncnURL, onlineProncnForm, onlineProncnSpell, offlineProncnFileName)

                        coutput.print_watcher('self.activeDictEntry')

                except:
                    coutput.print_warn('Unable to connect to the internet. Switching to offline mode.')
                    self.offlineMode = True

        # Pass #6: Check for dictionary pronunciation override
        coutput.print_debug("Pass #6: Check for dictionary pronunciation override")
        overrideProncnFileName = cfile.find_file(cfile.cleanse_filename(SB_DICT_OVERRIDE_CLIP.format(WORD=self.activeWordAlternatives)), SB_DICT_OVERRIDE_DIR_LIST)
        coutput.print_watcher('overrideProncnFileName')

        #if os.path.isfile(overrideProncnFileName) and os.path.getsize(overrideProncnFileName) > 0:
        if overrideProncnFileName is not None:
            overrideProncnForm = self.activeWord
            overrideProncnSpell = self.activeWord

            if self.activeDictEntry is None:
                # Set active dictionary entry
                self.activeDictEntry = cdictapi.DictionaryEntry(self.dictConfig, self.activeWord, self.activeEntry).simplified_word_entry

            self.activeDictEntry.override_pronunciation(overrideProncnForm, overrideProncnSpell, overrideProncnFileName)

            coutput.print_watcher('self.activeDictEntry')

        # Check and log errors
        wordToken = coutput.tokenize(self.activeWord)

        pronunciationToken = SB_EMPTY_STRING
        if self.activeDictEntry is not None and self.activeDictEntry.has_pronunciation():
            pronunciationToken = coutput.tokenize(self.activeDictEntry.pronunciation.spelling)

        coutput.print_watcher('wordToken')
        coutput.print_watcher('pronunciationToken')
        coutput.print_watcher('self.activeDictEntry')
       
        errorText = "ERROR:{0}:".format(self.activeWord)

        if self.activeDictEntry is None or self.activeDictEntry.has_definitions() is False:
            errorText += ">Definition Missing"
        
        if self.activeDictEntry is None or self.activeDictEntry.has_pronunciation() is False:
            errorText += ">Audio Missing"
        elif wordToken != pronunciationToken or (self.activeDictEntry is not None and self.activeDictEntry.has_mispronunciation()):
            errorText += ">Audio Mismatch"
        
        if errorText != "ERROR:{0}:".format(self.activeWord):
            errorText += "\n"
            cfile.append(SB_ERR_LOG, errorText)

        coutput.print_watcher('errorText')


    def lookup_dictionary_by_index(self, index):
        self.lookup_dictionary_by_word(self.wordList[index])


    def lookup_all_dictionaries_by_word(self, word):

        cdictall.lookup_word(self.connectionPool, SB_AUDIO_OUTPUT, SB_REPEAT_COUNT, SB_REPEAT_DELAY, word)


    def mask_active_word(self, word, text, mask_flag):

        if mask_flag:
            return re.sub(word, SB_MASK_SYMBOL * len(word), text, flags=re.IGNORECASE)
        else:
            return text

       
    def print_word_definition(self, word, dictEntry):

        if dictEntry is None or dictEntry.has_definitions() is False:
            if self.offlineMode is True:
                coutput.print_err("Unable to lookup definition while offline")
            else:
                coutput.print_err("Unable to lookup definition")
        else:
            # Print definitions
            definitionIndex = 0
            for definition in dictEntry.definitions:
                coutput.print_watcher('definition')
                               
                # Ignore comments and info lines with # prefix
                if re.match(r'^#', definition):
                    pass
                else:
                    if definitionIndex >= SB_DEFINITION_COUNT:
                        break

                    # Mask definitions that contain the word itself and remove importance prefix "*"
                    masked_definition = re.sub('^\*', SB_EMPTY_STRING, self.mask_active_word(word, definition, SB_DEFINITION_HIDE_EXPLICIT), flags=re.IGNORECASE)

                    # Check for override definitions from the word list prefixed with "*"
                    if re.match(r'^\*', definition):
                        coutput.print_color('cyan', SB_SPL_BULLET + masked_definition )
                    else:
                        print(SB_LIST_BULLET + masked_definition)
                    
                    definitionIndex += 1

            # Print etymology, examples
            if dictEntry.etymology != SB_EMPTY_STRING:
                coutput.print_color('cyan', 'Etymology: ' + dictEntry.etymology )
            if dictEntry.examples != SB_EMPTY_STRING:
                coutput.print_color('white', 'Examples: ' + re.sub(';', ', ', dictEntry.examples) )

            # Print info lines
            for definition in dictEntry.definitions:
                coutput.print_watcher('definition')

                # Ignore extraneous info lines
                if definition.startswith(('#!Source:', '#!Word:', '#!AudioURL:', '#!Meta:')):
                    pass

                # Print info with #! prefix
                elif re.match(r'^#!', definition):
                    infoText = re.sub('^#!', SB_EMPTY_STRING, definition, flags=re.IGNORECASE)
                    reMatch = re.search(":[ ]*(.*)$", infoText, flags=re.M)

                    # Ignore empty info lines
                    if reMatch.group(1) != SB_EMPTY_STRING:
                        # Mask info lines that contain the word itself
                        coutput.print_color('cyan', self.mask_active_word(word, infoText, SB_DEFINITION_HIDE_EXPLICIT))

            # Print usage
            if len(dictEntry.usage) > 0:
                for usage in dictEntry.usage:
                    print(SB_SEC_BULLET + self.mask_active_word(word, usage, SB_DEFINITION_HIDE_EXPLICIT))


    def pronounce_word(self, word, dictEntry, fileMode):

        if dictEntry is None:
            if self.offlineMode is True:
                coutput.print_err("Unable to lookup pronunciation while offline")
            else:
                coutput.print_err("Unable to lookup pronunciation")
            
        else:
            if dictEntry.has_respelling():            
                coutput.print_watcher('dictEntry.respelling')
                coutput.print_watcher('dictEntry.respelling.text')
                coutput.print_color('cyan', 'Respelling: ' + dictEntry.respelling.text )
            
            if not self.silentMode:
                if dictEntry.has_pronunciation_audio() is False and dictEntry.has_pronunciation_audio_url() is False:
                    coutput.print_err("Unable to lookup pronunciation")

                else:
                    keyWord = word

                    if dictEntry.has_pronunciation():
                        entryWord = dictEntry.pronunciation.spelling
                    else:
                        entryWord = SB_EMPTY_STRING

                    coutput.print_watcher('keyWord')
                    coutput.print_watcher('entryWord')
                   
                    self.dictAssist.compare_word_form(keyWord, entryWord)
                    
                    if fileMode is True:
                        coutput.print_debug("Executing cfile.play")
                        cfile.play(dictEntry.pronunciation.audio_file, SB_AUDIO_OUTPUT, SB_REPEAT_COUNT, SB_REPEAT_DELAY)
                    else:
                        coutput.print_debug("Executing cfile.play_url")
                        cfile.play_url(self.connectionPool, dictEntry.pronunciation.audio_url, SB_AUDIO_OUTPUT, SB_REPEAT_COUNT, SB_REPEAT_DELAY)


    def print_word_tip(self, word):
        overrideTipFileName = cfile.find_file(cfile.cleanse_filename(SB_DICT_OVERRIDE_MSG.format(WORD=self.activeWord)), SB_DICT_OVERRIDE_DIR_LIST)

        # Check for word message/instruction override
        #if os.path.isfile(overrideTipFileName) and os.path.getsize(overrideTipFileName) > 0:
        if overrideTipFileName is not None:
            activeTip = cfile.read(overrideTipFileName)
            coutput.print_tip(activeTip)


    def print_word_rule(self, word):
        # Check for word rules
        if word.lower() in self.ruleBook:
            coutput.print_color('green', '\nRule Book: ' + self.ruleBook[word.lower()]['Category'])
            for rule in self.ruleBook[word.lower()]['Rule']:
                coutput.print_color('magenta', SB_LIST_BULLET + rule)


    def print_pronunciation_key(self, dictEntry):

        # Retrieve respelling override
        respellText = SB_EMPTY_STRING
        for override in dictEntry.definitions:
            overrideRespell = re.search(r"#!Respelling: (.*)", override)

            if overrideRespell is not None:
                respellText = overrideRespell.group(1)
                break

        # Retrieve respelling
        if respellText == SB_EMPTY_STRING and dictEntry.has_respelling():
            respellText = dictEntry.respelling.text

        if respellText != SB_EMPTY_STRING:
            coutput.print_color('green', "\nPronunciation Key:")
            coutput.print_columnized_list(self.dictConfig.pronunciation_key(respellText), SB_KEY_COLUMN_COUNT)
        else:
            coutput.print_warn("No respelling available")
            coutput.print_color('cyan', "\nPronunciation Guide:")
            coutput.print_columnized_list(self.dictConfig.build_pronunciation_guide(), SB_GUIDE_COLUMN_COUNT)


    def display_word_cue(self, title, testMode):

        coutput.print_color('green', title)
        coutput.print_debug("Executing self.print_word_definition")
        self.print_word_definition(self.activeWord, self.activeDictEntry)

        if testMode.lower() != "test":
            coutput.print_debug("Executing self.print_word_rule")
            self.print_word_rule(self.activeWord)

        coutput.print_color('green', '\nPronunciation:')
        coutput.print_debug("Executing self.pronounce_word")
        self.pronounce_word(self.activeWord, self.activeDictEntry, True)

        coutput.print_debug("Executing self.print_word_tip")
        self.print_word_tip(self.activeWord)


    def display_pronunciation_key(self):

        self.print_pronunciation_key(self.activeDictEntry)


    def display_word_lookup(self, word, title, testMode):

        try:
            entryData = self.dictAssist.download_entry(self.connectionPool, word)
            dictEntry = cdictapi.DictionaryEntry(self.dictConfig, word, entryData).simplified_word_entry
        
            if dictEntry.source == SB_EMPTY_STRING:
                coutput.print_err("Unable to lookup dictionary entry for " + word)
            else:    
                coutput.print_color('green', title)

                for entryLine in dictEntry.__unicode__().splitlines():
                    print(entryLine)

                if testMode.lower() != "test":
                    self.print_word_rule(word)

                coutput.print_debug("Executing self.pronounce_word")
                print(SB_EMPTY_STRING)
                self.pronounce_word(word, dictEntry, False)

        except Exception as e:
            coutput.print_err("Unable to lookup while offline")
            # Displays the trace for the error
            coutput.print_err(traceback.format_exc())


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

        practiceFileName = SB_STUDY_DIR + SB_PRACTICE_WORD_FILE.format(LISTID=self.contestList)

        if self.enableSavePracticeWords:
            cfile.append(practiceFileName, word)


    def get_current_test_context(self):

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

        if self.enableSaveResults:
            cfile.write(SB_CURRENT_TEST_LOG, self.get_current_test_context())


    def save_current_test_result(self, valuation):

        if self.enableSaveResults:
            cfile.append(SB_CURRENT_TEST_LOG, valuation)


    def display_evaluation_result(self, practiceMode):

        if practiceMode.lower() == "test":
            testHeader  = "=============== Start of Test Log ==============="
            testTrailer = "================ End of Test Log ================"
            testFileName = SB_TEST_LOG

        elif practiceMode.lower() == "revise":
            testHeader  = "=============== Start of Revision Log ==============="
            testTrailer = "================ End of Revision Log ================"
            testFileName = SB_REVISION_LOG
     
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
    #os.system("clear")

    # Suspend input from stdin
    cinput.set_term_input(False)


def exit_app():
    # Resume input from stdin
    cinput.set_term_input(True)

    print("\n\nThank you for practicing for Spelling Bee.\n")
    exit()


def display_help(runMode):

    if runMode.lower() == "test":
        print("\n{0} Keyboard Menu: {1}".format(runMode.title(), SB_TEST_KEYBOARD_MENU))
    elif runMode.lower() == "revise":
        print("\n{0} Keyboard Menu: {1}".format(runMode.title(), SB_REVISE_KEYBOARD_MENU))
    else:
        print("\n{0} Keyboard Menu: {1}".format(runMode.title(), SB_PRACTICE_KEYBOARD_MENU))


def run_study(app, practiceMode):

    userPracticeMode = practiceMode.strip().lower()
    coutput.print_watcher('userPracticeMode')

    if userPracticeMode == "study":
        app.print_active_word_list()
    else:
        app.display_about()
    display_help(userPracticeMode)
    userInput = cinput.get_keypress("\nReady to {0}? Press any key when ready ... ".format(userPracticeMode))

    activeWordIndex = 0

    while True:

        coutput.print_watcher('activeWordIndex')
        coutput.print_watcher('len(app.activeWordIndexList)')
        if (activeWordIndex < 0) or (activeWordIndex >= len(app.activeWordIndexList)):
            break

        wordIndex = app.activeWordIndexList[activeWordIndex]
        coutput.print_watcher('wordIndex')

        # Lookup word definition
        coutput.print_debug("Executing self.lookup_dictionary_by_index")
        app.lookup_dictionary_by_index(wordIndex)

        if userPracticeMode == "study":
            titleText = SB_STUDY_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1, WORD=app.wordList[wordIndex], SEQ=activeWordIndex + 1, COUNT=len(app.activeWordIndexList))
        else:
            titleText = SB_PRACTICE_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1, SEQ=activeWordIndex + 1, COUNT=len(app.activeWordIndexList))

        coutput.print_debug("Executing self.display_word_cue")
        print("\n" + SB_PRI_SEP_SYMBOL * SB_PRI_SEP_LEN)
        app.display_word_cue(titleText, userPracticeMode)

        coutput.print_debug("Prompting for user keypress")
        userInput = cinput.get_keypress(SB_PROMPT_SYMBOL).lower()
        print(SB_PRI_SEP_SYMBOL * SB_PRI_SEP_LEN)

        while True:
            # Move to [n]ext word
            if userInput == "n":
                activeWordIndex += 1
                break
            # Move to [p]revious word
            elif userInput == "p":
                activeWordIndex -= 1
                break
            # [R]epeat current word
            elif userInput == "r":
                break
            # Re[v]iew active word list
            elif userInput == "v":
                print(SB_EMPTY_STRING)
                app.print_active_word_list()
            # [S]how current word spelling and dictionary entry
            elif userInput == "s":
                print("\n" + SB_PRI_SEP_SYMBOL * SB_PRI_SEP_LEN)
                app.display_word_cue(titleText, userPracticeMode)
                coutput.print_color('green', "\nDictionary Entry:")
                #print app.activeDictEntry
                for entryLine in app.activeDictEntry.__unicode__().splitlines():
                    print(entryLine)
            # [G]oto to word
            elif userInput == "g":
                nextWord = cinput.get_input("\nEnter goto word: ")
                nextIndex = app.get_active_word_index(nextWord)                
                if (nextIndex < 0) or (nextIndex >= len(app.activeWordIndexList)):
                    coutput.print_err("Unable to locate '{0}' in word list".format(nextWord))
                else:
                    activeWordIndex = nextIndex
                    break
            # [L]ookup word definition and pronunciation
            elif userInput == "l":
                userLookupWord = cinput.get_input("\nEnter lookup word: ")
                #coutput.print_warn("Lookup feature under construction.")
                #app.lookup_all_dictionaries_by_word(userLookupWord)
                app.display_word_lookup(userLookupWord, SB_LOOKUP_WORD_DEFN_TITLE.format(WORD=userLookupWord), userPracticeMode)
            # Display pronunciation [k]ey
            elif userInput == "k":
                print("\n" + SB_PRI_SEP_SYMBOL * SB_PRI_SEP_LEN)
                app.display_word_cue(titleText, userPracticeMode)
                app.display_pronunciation_key()
            # Display [h]elp and statistics
            elif userInput == "h":
                print(SB_EMPTY_STRING)
                app.display_about()
            # E[x]it application
            elif userInput == "x":
                app.shut_down()
                exit_app()
            else:
                print(SB_EMPTY_STRING)
                coutput.print_err("Invalid response")

            # Prompt for user input
            print(SB_SEC_SEP_SYMBOL * SB_SEC_SEP_LEN)
            display_help(userPracticeMode)
            userInput = cinput.get_keypress(SB_PROMPT_SYMBOL).lower()
            print(SB_PRI_SEP_SYMBOL * SB_PRI_SEP_LEN)


def run_test(app, practiceMode):

    userPracticeMode = practiceMode.strip().lower()

    if userPracticeMode == "test":
        app.display_about()
        display_help(userPracticeMode)
        userInput = cinput.get_keypress("\nReady for the test? Press any key when ready ... ")
    else:
        app.print_active_word_list()
        display_help(userPracticeMode)
        userInput = cinput.get_keypress("\nReady to revise? Press any key when ready ... ")

    testTotalCount = app.active_word_count()
    testCorrectCount = 0

    userResponse = SB_EMPTY_STRING
    testValuation = SB_EMPTY_STRING

    app.reset_test_result()
    app.reset_current_test_result()

    activeWordIndex = 0

    while True:
        coutput.print_watcher('app.activeWordIndexList')
        coutput.print_watcher('activeWordIndex')

        if (activeWordIndex < 0) or (activeWordIndex >= len(app.activeWordIndexList)):
            break

        wordIndex = app.activeWordIndexList[activeWordIndex]
        coutput.print_watcher('wordIndex')

        # Lookup word definition
        app.lookup_dictionary_by_index(wordIndex)

        if userPracticeMode == "test":
            titleText = SB_PRACTICE_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1, SEQ=activeWordIndex + 1, COUNT=len(app.activeWordIndexList))
            print("\n" + SB_PRI_SEP_SYMBOL * SB_PRI_SEP_LEN)
            app.display_word_cue(titleText, userPracticeMode)
            print(SB_SEC_SEP_SYMBOL * SB_SEC_SEP_LEN)
            userResponse = cinput.get_input("Enter spelling: ")
        else:
            titleText = SB_STUDY_WORD_DEFN_TITLE.format(INDEX=wordIndex + 1, WORD=app.activeWordAlternatives, SEQ=activeWordIndex + 1, COUNT=len(app.activeWordIndexList))
            print("\n" + SB_PRI_SEP_SYMBOL * SB_PRI_SEP_LEN)
            app.display_word_cue(titleText, userPracticeMode)
            print(SB_SEC_SEP_SYMBOL * SB_SEC_SEP_LEN)
            userResponse = cinput.get_keypress("Enter response: ")

        # E[x]it test
        if userResponse.lower() == "x":
            break

        # [R]epeat question
        elif userResponse.lower() == "r":
            continue

        # Display pronunciation [k]ey
        elif userResponse.lower() == "k":
            print(SB_EMPTY_STRING)
            app.display_pronunciation_key()
            display_help(userPracticeMode)
            continue

        # Display [h]elp and statistics
        elif userResponse.lower() == "h":
            print(SB_EMPTY_STRING)
            app.display_about()
            display_help(userPracticeMode)
            continue

        # Revision mode: Re[v]iew active word list
        elif userPracticeMode == "revise" and userResponse.lower() == "v":
            print(SB_EMPTY_STRING)
            app.print_active_word_list()
            continue

        # Revision mode: Process correct response
        elif userPracticeMode == "revise" and userResponse.lower() == "y":
            correctResponse = True
            testValuation = SB_RIGHT_SYMBOL + " " + app.activeWordAlternatives
            testCorrectCount += 1

            # Display valuation
            coutput.print_color('green', " " * 50 + testValuation)
            cfile.play(SB_FEEDBACK_RIGHT, SB_AUDIO_OUTPUT, 1, SB_REPEAT_DELAY)

            # Save valuation
            app.log_test_valuation(testValuation)
            app.save_current_test_result(testValuation)

            # Move to next word
            activeWordIndex += 1

        # Revision mode: Process incorrect response
        elif userPracticeMode == "revise" and userResponse.lower() == "n":
            correctResponse = False
            testValuation = SB_WRONG_SYMBOL + " " + app.activeWordAlternatives

            # Save practice word            
            app.log_practice_word(app.activeWord)
            app.save_practice_word(app.activeWord)

            # Display valuation
            coutput.print_color('red', " " * 50 + testValuation)
            cfile.play(SB_FEEDBACK_WRONG, SB_AUDIO_OUTPUT, 1, SB_REPEAT_DELAY)

            # Save valuation
            app.log_test_valuation(testValuation)
            app.save_current_test_result(testValuation)

            # Move to next word
            activeWordIndex += 1

        # Test mode: Process response
        elif userPracticeMode == "test" :
            correctResponse = False

            # Process correct response
            if app.valuate_test_response(userResponse, app.activeWordAlternatives, SB_TEST_MODE):
                correctResponse = True
                testValuation = SB_RIGHT_SYMBOL + " " + userResponse
                testCorrectCount += 1
            # Process incorrect response
            else:
                testValuation = SB_WRONG_SYMBOL + " " + userResponse
                app.log_practice_word(app.activeWord)
                app.save_practice_word(app.activeWord)

            # Indicate correct form of the answer, if different from the response
            if userResponse != app.activeWord:
                testValuation = testValuation + " (" + app.activeWordAlternatives + ")"

            # Display valuation
            if correctResponse:
                coutput.print_color('green', " " * 50 + testValuation)
                cfile.play(SB_FEEDBACK_RIGHT, SB_AUDIO_OUTPUT, 1, SB_REPEAT_DELAY)
            else:
                coutput.print_color('red', " " * 50 + testValuation)
                cfile.play(SB_FEEDBACK_WRONG, SB_AUDIO_OUTPUT, 1, SB_REPEAT_DELAY)
            
            # Save valuation
            app.log_test_valuation(testValuation)
            app.save_current_test_result(testValuation)

            # Move to next word
            activeWordIndex += 1

        else:
            print(SB_EMPTY_STRING)
            coutput.print_err("Invalid response")

        print("\n" + SB_PRI_SEP_SYMBOL * SB_PRI_SEP_LEN)
   
    logText="{0}/{1}".format(testCorrectCount, testTotalCount)
    app.log_test_result(logText)

    print("\n" + SB_PRI_SEP_SYMBOL * SB_PRI_SEP_LEN + "\n")
    if userPracticeMode == "test":
        print("Your test is complete. Displaying results...")
    else:
        print("Your revision is complete. Displaying results...")
    
    app.display_evaluation_result(userPracticeMode)
    print("\n" + SB_PRI_SEP_SYMBOL * SB_PRI_SEP_LEN)



def run_scan(app):

    userPracticeMode = "scan"

    app.display_about()
    userInput = cinput.get_keypress("\nReady for scan? Press any key when ready ... ")
    print(SB_EMPTY_STRING)

    activeWordIndex = 0

    coutput.print_watcher('activeWordIndex')
    coutput.print_watcher('len(app.activeWordIndexList)')

    while True:
        if (activeWordIndex < 0) or (activeWordIndex >= len(app.activeWordIndexList)):
            break

        wordIndex = app.activeWordIndexList[activeWordIndex]

        # Lookup word definition
        app.lookup_dictionary_by_index(wordIndex)

        coutput.print_debug("Building display title")
        displayText = "Scanned word #{0}: {1}"

        coutput.print_debug("Displaying title")
        print(displayText.format(wordIndex + 1, app.activeWord))

        # Move to next word
        activeWordIndex += 1
    
    print("\nError scan is complete. All errors logged to " + SB_ERR_LOG)
    

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
argParser.add_argument("-o", "--offline", help="run in offline mode", action="store_true")
args = argParser.parse_args()

# Setup Spelling Bee word list and run mode
spellBee = SpellingBee(args.runMode, args.contestList, args.mode, args.selection, args.silent, args.offline)
spellBeeMode = args.runMode.lower()

try:
    init_app()

    # Run Spelling Bee assistant in practice, test or scan mode
    if spellBeeMode in ["study", "practice"]:
        run_study(spellBee, spellBeeMode)
    elif spellBeeMode in ["test", "revise"]:
        run_test(spellBee, spellBeeMode)
    elif spellBeeMode == "scan":
        run_scan(spellBee)

    spellBee.shut_down()
    exit_app()

except Exception as e:
    # Displays the trace for the error
    coutput.print_err(traceback.format_exc())

    spellBee.shut_down()
    exit_app()
    

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

########################################################################
# Checkin Commands
########################################################################
'''
git status
git add <filename>
git commit -m "<comment>"
git push "https://<user>:<pwd>@github.com/<user>/<repo>.git" master
'''