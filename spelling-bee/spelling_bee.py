#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################
# Syntax :   sudo python spelling_bee.py runMode contestList mode selection
# where      runMode is study, practice, scan or test.
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
import pygame
import random

sys.path.insert(0, "/home/pi/projects/raspi")
import common.rpimod.stdio.input as cinput
import common.rpimod.stdio.output as coutput
import common.rpimod.wordproc.dict.merriamwebster as cdict

################################################################
# Spelling Bee Configuration variables
################################################################

SB_CHAPTER_SIZE = 50
SB_DEFINITION_COUNT = 3
SB_DEFINITION_HIDE_EXPLICIT = True                              # Set to True if definitions containing the word are to be hidden
SB_REPEAT_COUNT = 1
SB_REPEAT_DELAY = 1.5
SB_COLUMN_COUNT = 5
SB_TEST_MODE = "easy"                                           # Available test modes are: easy, medium and difficult
SB_TEST_SAVE_RESULT = True
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

SB_PRACTICE_WORD_FILE = "spelling_bee_{LISTID}-practice.txt"

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

        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "activeWordIndexList :: {0}".format(self.activeWordIndexList))

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
        coutput.print_columnized_list(self.wordList[self.activeRangeStart : self.activeRangeEnd + 1], SB_COLUMN_COUNT)

    def get_word_index(self, searchWord):
        resultIndex = -1
        for wordIndex, word in enumerate(self.wordList, start=0):
            if re.match('^' + searchWord.lower() + '.*', word.lower()):
                resultIndex = wordIndex
                break
        return resultIndex

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

            self.activeDefinition = cdict.parse_word_definition(self.activeWord, self.activeEntry)
        else:
            # Download dictionary entry
            self.activeEntry = cdict.get_dictionary_entry(connectionPool, self.activeWord)

            # Save dictionary entry offline
            offlineEntryFile = codecs.open(offlineEntryFileName, mode='w', encoding='utf-8')
            # Decode as utf-8 while writing XML file
            # todo: Implement file read/write operations as a library
            offlineEntryFile.write(self.activeEntry.decode('utf-8'))
            offlineEntryFile.close()

            # Retrieve word definition
            self.activeDefinition = cdict.parse_word_definition(self.activeWord, self.activeEntry)
            if len(self.activeDefinition) == 0:
                errorFile.write("ERROR:Missing Definition:{0}\n".format(self.activeWord).decode('utf-8'))


        # Check offline for word pronunciation
        self.activePronunciation = ""
        self.activePronunciationWord = ""
        offlineProncnFileName = SB_DICT_OFFLINE_DIR + "/" + SB_DICT_OFFLINE_CLIP.format(WORD=self.activeWord).replace(" ", "_")

        # Retrieve pronunciation audio clip word form and filename
        [wordClipForm, wordClipURL] = cdict.parse_word_clip(self.activeWord, self.activeEntry)

        if os.path.isfile(offlineProncnFileName) and os.path.getsize(offlineProncnFileName) > 1000:
            coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "offlineProncnFile size :: {0}".format(os.path.getsize(offlineProncnFileName)))
            self.activePronunciation = offlineProncnFileName
            self.activePronunciationWord = wordClipForm
        else:
            # Save pronunciation offline
            if wordClipURL == "":
                errorFile.write("ERROR:Missing Audio:{0}\n".format(self.activeWord).decode('utf-8'))
            else:
                # Download audio clip
                wordClipAudio = cdict.get_dictionary_audio(connectionPool, wordClipURL)
                offlineProncnFile = open(offlineProncnFileName, "wb")
                offlineProncnFile.write(wordClipAudio)
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

    def save_practice_words(self, saveEnabled):
        separator = unicode("\n", 'utf-8')

        if len(self.activePracticeWords) > 0:

            if saveEnabled:
                practiceFileName = SB_DATA_DIR + "/" + SB_PRACTICE_WORD_FILE
                practiceFileName = practiceFileName.format(LISTID=self.contestList)

                # Get previously saved practice words
                if os.path.isfile(practiceFileName) and os.path.getsize(practiceFileName) > 0:
                    practiceFile = codecs.open(practiceFileName, mode='r', encoding='utf-8')
                    currentPracticeWordList = practiceFile.read().encode('utf-8').splitlines()                # Use of splitlines() avoids the newline character from being stored in the word list
                    practiceFile.close()
                else:
                    currentPracticeWordList = []

                # Save practice words to practice file, if not already saved
                practiceFile = codecs.open(practiceFileName, mode='a', encoding='utf-8')
                for word in self.activePracticeWords:
                    if word not in currentPracticeWordList:
                        practiceFile.write(word)
                        practiceFile.write(separator)
                practiceFile.close()


    def display_test_result(self, saveEnabled):
        testHeader  = unicode("=============== Start of Test Log ===============", 'utf-8')
        testTrailer = unicode("================ End of Test Log ================", 'utf-8')
        separator = unicode("\n", 'utf-8')

        # Test header
        displayText = separator + unicode("Spelling Bee {0}".format(self.contestList), 'utf-8')
        displayText += separator + unicode("Word Count [{0}] Chapter [{1}/{2}] Words [{3}-{4}]".format(self.word_count(), self.activeChapter, self.chapter_count(), self.activeRangeStart + 1, self.activeRangeEnd + 1), 'utf-8')
        displayText += separator
        displayText += separator + unicode("Test Date [{0}] Score [{1}]".format(self.activeTestDate, self.activeTestScore), 'utf-8')

        print displayText,

        if saveEnabled:
            testFileName = SB_DATA_DIR + "/" + SB_TEST_LOG
            testFile = codecs.open(testFileName, mode='a', encoding='utf-8')
            testFile.write(testHeader)
            testFile.write(displayText)

        # Test valuations
        # Print colorized test valuations
        coloredTestValuations = []
        for valuation in self.activeTestValuations:
            if re.match('^' + SB_RIGHT_SYMBOL + '.*', valuation):
                textColor = coutput.get_term_color('green', 'normal', 'normal')
            else:
                textColor = coutput.get_term_color('red', 'normal', 'normal')
            coloredTestValuations.append(textColor + valuation + coutput.get_term_color('normal', 'normal', 'normal'))

        print separator,
        coutput.print_columnized_list(coloredTestValuations, SB_COLUMN_COUNT)

        if saveEnabled:
            columnizedTestValuations = coutput.columnize(self.activeTestValuations, SB_COLUMN_COUNT)
            for row in columnizedTestValuations:
                testFile.write(separator)
                for col in row:
                    testFile.write(col)

        # Test practice words
        if len(self.activePracticeWords) > 0:
            displayText = separator + unicode("Practice Words:", 'utf-8')
            for row in coutput.columnize(self.activePracticeWords, SB_COLUMN_COUNT):
                displayText += separator
                for col in row:
                    displayText += col
                
            print displayText,

            if saveEnabled:
                testFile.write(separator)
                testFile.write(displayText)

                # Save practice words
                self.save_practice_words(saveEnabled)

        # Test trailer
        if saveEnabled:
            # Save test trailer to test log
            testFile.write(separator)
            testFile.write(testTrailer)
            testFile.write(separator)
            testFile.close()


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
    _FUNC_NAME_ = "run_test"

    spellBee.display_about()
    display_help("test")
    userInput = cinput.get_keypress("\nReady for the test? Press any key when ready ... ")

    testDate = time.strftime('%a %d-%b-%Y %H:%M:%S')
    testTotalCount = spellBee.active_word_count()
    testCorrectCount = 0

    userResponse = ""
    testValuation = ""

    spellBee.reset_test_result()

    activeWordIndex = 0

    while True:
        coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "activeWordIndex :: {0}".format(activeWordIndex))
        if (activeWordIndex < 0) or (activeWordIndex >= len(spellBee.activeWordIndexList)):
            break

        wordIndex = spellBee.activeWordIndexList[activeWordIndex]

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
        activeWordIndex += 1
    
    spellBee.log_test_result(testDate, str(testCorrectCount) + "/" + str(testTotalCount))
    print "\nYour test is complete. Displaying results..."
    
    spellBee.display_test_result(SB_TEST_SAVE_RESULT)


def run_error_scan(spellBee):

    spellBee.display_about()
    userInput = cinput.get_keypress("\nReady for error scan? Press any key when ready ... ")
    print ("\n")

    activeWordIndex = 0

    while True:
        if (activeWordIndex < 0) or (activeWordIndex >= len(spellBee.activeWordIndexList)):
            break

        wordIndex = spellBee.activeWordIndexList[activeWordIndex]

        # Lookup word definition
        spellBee.lookup_dictionary_by_index(wordIndex)
        print "Scanned word #{0}: {1}".format(wordIndex + 1, spellBee.activeWord)

        # Move to next word
        activeWordIndex += 1
    
    print "\nError scan is complete. All errors are logged to {0}/{1}.".format(SB_DATA_DIR, SB_ERR_LOG)
    

################################################################
# Main Program
################################################################

# Process command line arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("runMode", type=str, choices=['study', 'practice', 'test', 'scan'], help="is study, practice, test or scan")
argParser.add_argument("contestList", type=str, help="is the word list identifier for the contest in YYYY[-language][-challenge] format")
argParser.add_argument("mode", type=str, choices=['chapter', 'count', 'word', 'random'], nargs='?', default='count', help="is chapter, count, word or random")
argParser.add_argument("selection", type=str, nargs='?', default='1', help="is the chapter number, word index range, word range or random sample size")
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
