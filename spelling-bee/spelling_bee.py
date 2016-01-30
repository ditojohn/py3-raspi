#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################
# Syntax :   sudo python spelling_bee.py runMode contestYear mode selection
# where      runMode is practice, scan or test.
#            contestYear is the year of the contest in YYYY format
#            mode is chapter, count or word.
#                In chapter mode, the next argument is the chapter number
#                    selection is the chapter number of the word list to be practiced.
#                    Default chapter size is 50 words.
#                In count mode, the next argument is the word range
#                    selection is the index range of words in the word list to be practiced.
#                In word mode, the next argument is the word range
#                    selection is the range of words in the word list to be practiced.
# Example:    sudo python spelling_bee.py practice 2016 chapter 7
#             sudo python spelling_bee.py test 2016 count 10-15
#             sudo python spelling_bee.py practice 2016 word lary-frees
#             sudo python spelling_bee.py scan 2016 count 10-15
################################################################

# todo: Reduce import execution time
import sys
import os
import time
import argparse
import math
import re
import urllib3
import codecs
from xml.dom import minidom
import pygame

sys.path.insert(0, "/home/pi/projects/raspi")
import common.rpimod.stdio.input as cinput
import common.rpimod.stdio.output as coutput

################################################################
# Spelling Bee Configuration variables
################################################################

SB_CHAPTER_SIZE = 50
SB_MEANING_COUNT = 3
SB_REPEAT_COUNT = 1
SB_REPEAT_DELAY = 1.5
SB_DATA_DIR = "/home/pi/projects/raspi/spelling-bee/data"

################################################################
# Internal variables
################################################################

SB_DICT_OFFLINE_DIR = SB_DATA_DIR
SB_DICT_WORD_FILE = "spelling_bee_{YEAR}.txt"
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

SB_ERR_LOG = "sberr.log"


class SpellingBee(object):
    """
    A Spelling Bee assistant to help with word list navigation and dictionary lookup.
    It has the following attributes:
        contestYear: A string representing the year of the spelling bee contest
        wordList: A list containing words loaded from wordFile
        activeChapter: 
        activeRangeStart: 
        activeRangeEnd: 

        activeWord:
        activeEntry:
        activeDefinition:
        activePronunciation:
        activeTestValuations:

        word_count():
        chapter_count():
        active_word_count():
    """
    def __init__(self, year, mode, selection):
        self.contestYear = year

        wordFileName = SB_DATA_DIR + "/" + SB_DICT_WORD_FILE
        wordFileName = wordFileName.format(YEAR=year)
        #wordFile = open(wordFileName, "r")
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
        self.activeDefinition = ""
        self.activePronunciation = ""
        
        self.activeTestDate = ""
        self.activeTestScore = ""
        self.activeTestValuations = []
        self.activePracticeWords = []

    def word_count(self):
        return len(self.wordList)

    def chapter_count(self):
        return int(math.ceil(len(self.wordList)/SB_CHAPTER_SIZE))

    def active_word_count(self):
        return (self.activeRangeEnd - self.activeRangeStart + 1)

    def display_about(self):
        print "Spelling Bee {0}".format(self.contestYear)
        print "Word Count [{0}] Chapter [{1}/{2}] Words [{3}-{4}]".format(self.word_count(), self.activeChapter, self.chapter_count(), self.activeRangeStart + 1, self.activeRangeEnd + 1)

    def print_active_word_list(self):
        self.display_about()
        print ""
        # todo: fix columnize function considering number of bytes instead of characters
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

    def parse_word_clip(self, entryXML):
        wordClip = ""

        wordClips = []
        dictEntryXML = minidom.parseString(entryXML)
        # Process <wav> elements
        wavElements = dictEntryXML.getElementsByTagName('wav')
        for wavElement in wavElements:
            if wavElement.firstChild.nodeType == wavElement.firstChild.TEXT_NODE:
                wordClips.append(wavElement.firstChild.data)
        if len(wordClips) != 0:
            wordClips.sort()
            wordClip = wordClips[0]

        return wordClip

    def parse_word_root(self, entryXML):
        wordRoot = ""

        dictEntryXML = minidom.parseString(entryXML)
        # Process <entry> elements
        entryElements = dictEntryXML.getElementsByTagName('entry')
        if len(entryElements) != 0:
            # Process <ew> elements
            ewElements = entryElements[0].getElementsByTagName('ew')
            if len(ewElements) != 0:
                if ewElements[0].childNodes[0].nodeType == ewElements[0].childNodes[0].TEXT_NODE:
                    wordRoot = ewElements[0].childNodes[0].data

        return wordRoot

    def parse_word_definition(self, entryXML):
        wordDefinition = ""

        sourceXML = entryXML
        sourceXML = self.cleanse_formatting(sourceXML)

        dictEntryXML = minidom.parseString(sourceXML)
        # Process <entry> elements
        entryElements = dictEntryXML.getElementsByTagName('entry')
        if len(entryElements) != 0:
            for entryElement in entryElements:
                # Retrieve definition from dictionary entry
                # Process <dt> elements
                dtElements = entryElement.getElementsByTagName('dt')
                for dtIndex, dtElement in enumerate(dtElements, start=0):
                    if dtElement.firstChild.nodeType == dtElement.firstChild.TEXT_NODE:
                        dtText = dtElement.firstChild.data.replace(":", "")
                        if dtText != "":
                            wordDefinition = wordDefinition + dtText.strip() + "\n"
                    
                    # Process <sx> elements
                    sxElements = dtElement.getElementsByTagName('sx')
                    for sxIndex, sxElement in enumerate(sxElements, start=0):
                        if sxElement.firstChild.nodeType == dtElement.firstChild.TEXT_NODE:
                            sxText = sxElement.firstChild.data.replace(":", "")
                            if sxIndex < len(sxElements) - 1:
                                wordDefinition = wordDefinition + sxText.strip() + ", "
                            else:
                                wordDefinition = wordDefinition + sxText.strip() + "\n"

                if wordDefinition != "":
                    break

        return wordDefinition

    def lookup_word_definition(self, index):
        self.activeWord = self.wordList[index]
        
        # Setup connection and error logging
        connectionPool = urllib3.PoolManager()
        errorFileName = SB_DATA_DIR + "/" + SB_ERR_LOG
        #errorFile = open(errorFileName, "a")
        errorFile = codecs.open(errorFileName, mode='a', encoding='utf-8')

        # Check offline for dictionary entry
        self.activeEntry = ""
        self.activeDefinition = ""
        offlineEntryFileName = SB_DICT_OFFLINE_DIR + "/" + SB_DICT_OFFLINE_ENTR.format(WORD=self.activeWord).replace(" ", "_")

        if os.path.isfile(offlineEntryFileName) and os.path.getsize(offlineEntryFileName) > 0:
            offlineEntryFile = codecs.open(offlineEntryFileName, mode='r', encoding='utf-8')
            # Encode as utf-8 while reading XML file
            self.activeEntry = offlineEntryFile.read().encode('utf-8')
            offlineEntryFile.close()

            self.activeDefinition = self.parse_word_definition(self.activeEntry)
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
            wordEntry = self.parse_word_root(self.activeEntry)
            if self.activeWord.lower() != str(wordEntry).lower():
                errorFile.write("ERROR:Entry Mismatch:{0}\n".format(self.activeWord).decode('utf-8'))

            # Retrieve word definition
            self.activeDefinition = self.parse_word_definition(dictEntryResponse.data)
            if self.activeDefinition == "":
                errorFile.write("ERROR:Missing Definition:{0}\n".format(self.activeWord).decode('utf-8'))


        # Check offline for word pronunciation
        self.activePronunciation = ""
        offlineProncnFileName = SB_DICT_OFFLINE_DIR + "/" + SB_DICT_OFFLINE_CLIP.format(WORD=self.activeWord).replace(" ", "_")

        if os.path.isfile(offlineProncnFileName) and os.path.getsize(offlineProncnFileName) > 0:
            self.activePronunciation = offlineProncnFileName
        else:
            # Retrieve pronunciation audio clip filename
            wordClip = self.parse_word_clip(self.activeEntry)

            # Save pronunciation offline
            if wordClip == "":
                errorFile.write("ERROR:Missing Audio:{0}\n".format(self.activeWord).decode('utf-8'))
            else:
                # Determine audio clip folder
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

        # Close connection and error logging
        errorFile.close()
        connectionPool.clear()
        

    def print_word_definition(self):
        if self.activeDefinition == "":
            print "ERROR: Unable to lookup dictionary definition"
        else:
            definitionCount = len(self.activeDefinition.splitlines())
            if definitionCount > SB_MEANING_COUNT:
                definitionCount = SB_MEANING_COUNT
            for i in range (0, definitionCount):
                print "{0} {1}".format(SB_LIST_BULLET, self.activeDefinition.encode('utf-8').splitlines()[i])

    def pronounce_word(self):
        if self.activePronunciation == "":
            print "ERROR: Unable to lookup audio pronunciation"
        else:
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

    def log_test_result(self, testDate, testScore):
        self.activeTestDate = testDate
        self.activeTestScore = testScore

    def log_practice_word(self, testWord):
        self.activePracticeWords.append(testWord)

    def log_test_valuation(self, testValuation):
        self.activeTestValuations.append(testValuation)

    def display_test_result(self):
        print "Test Date [{0}] Score [{1}]".format(self.activeTestDate, self.activeTestScore)
        coutput.columnize(self.activeTestValuations, 5)

        if len(self.activePracticeWords) > 0:
            print "\nPractice Words:"
            coutput.columnize(self.activePracticeWords, 5)

def init_app():
    # Clear screen
    os.system("clear")

    # Switch audio output to 3.5 mm jack
    os.system("amixer -q cset numid=3 1")

def exit_app():
    # Switch audio output back to auto
    os.system("amixer -q cset numid=3 0")

    print "\n\nThank you for practicing for Spelling Bee.\n"
    exit()

def display_help(runMode):
    if runMode.lower() == "practice":
        print "{0} Keyboard Menu: {1}".format(runMode.title(), SB_PRACTICE_KEYBOARD_MENU)
    else:
        print "{0} Keyboard Menu: {1}".format(runMode.title(), SB_TEST_KEYBOARD_MENU)

def run_practice(spellBee):

    spellBee.display_about()
    display_help("practice")
    userInput = cinput.get_keypress("\nReady to practice? Press any key when ready ... ")

    wordIndex = spellBee.activeRangeStart

    while True:
        if (wordIndex < spellBee.activeRangeStart) or (wordIndex > spellBee.activeRangeEnd):
            break

        # Lookup word definition
        spellBee.lookup_word_definition(wordIndex)
        spellBee.display_word_cue("\n\nWord #" + str(wordIndex) + " means:")
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
                spellBee.display_word_cue("\n\nWord #" + str(wordIndex) + " means:")
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # Re[v]iew active word list
            elif userInput.lower() == "v":
                print "\n"
                spellBee.print_active_word_list()
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # [S]how current word spelling
            elif userInput.lower() == "s":
                print "\n\nWord #{0} is {1}".format(wordIndex, spellBee.wordList[wordIndex])
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # [L]ookup word definition and pronunciation
            elif userInput.lower() == "l":
                print "\n"
                # todo: implement lookup function
                print "Under construction..."
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # Display [h]elp and statistics
            elif userInput.lower() == "h":
                print "\n"
                spellBee.display_about()
                display_help("practice")
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)
            # E[x]it application
            elif userInput.lower() == "x":
                exit_app()
            else:
                print "\nInvalid response.\n"
                spellBee.display_about()
                display_help("practice")
                userInput = cinput.get_keypress(SB_PROMPT_SYMBOL)


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
        spellBee.lookup_word_definition(wordIndex)
        spellBee.display_word_cue("\n\nWord #" + str(wordIndex) + " means:")
        userResponse = raw_input("Enter spelling: ")

        # E[x]it test
        if userResponse.lower() == "x":
            break
        # [R]epeat question
        elif userResponse.lower() == "r":
            continue
        else:
            # Process correct response
            if userResponse == spellBee.activeWord:
                testValuation = SB_RIGHT_SYMBOL + " " + userResponse
                testCorrectCount += 1
            # Process incorrect response
            else:
                testValuation = SB_WRONG_SYMBOL + " " + userResponse + " (" + spellBee.activeWord + ")"
                spellBee.log_practice_word(spellBee.activeWord)
            
            # Save and display valuation
            spellBee.log_test_valuation(testValuation)
            print " " * 50 + testValuation
    

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
        spellBee.lookup_word_definition(wordIndex)
        print "Scanned word #{0}: {1}".format(wordIndex + 1, spellBee.activeWord)

        # Move to next word
        wordIndex += 1
    
    print "\nError scan is complete. All errors are logged to {0}/{1}.".format(SB_DATA_DIR, SB_ERR_LOG)
    

################################################################
# Main Program
################################################################

# Process command line arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("runMode", help="is practice, scan or test", type=str)
argParser.add_argument("contestYear", help="is the year of the contest in YYYY format", type=str)
argParser.add_argument("mode", help="is chapter, count or word", type=str)
argParser.add_argument("selection", help="is the chapter number, word index range or word range", type=str)
args = argParser.parse_args()

# Setup Spelling Bee word list
spellBee = SpellingBee(args.contestYear, args.mode, args.selection)

init_app()

# Run Spelling Bee assistant in practice, test or scan mode
if args.runMode.lower() == "practice":
    run_practice(spellBee)
elif args.runMode.lower() == "test":
    run_test(spellBee)
elif args.runMode.lower() == "scan":
    run_error_scan(spellBee)

exit_app()
