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

import sys
import argparse
import math

sys.path.insert(0, "/home/pi/projects/raspi")
import common.rpimod.stdio.input as INPUT

################################################################
# Spelling Bee Configuration variables
################################################################

SB_CHAPTER_SIZE = 50
SB_MEANING_COUNT = 3
SB_REPEAT_COUNT = 2
SB_REPEAT_DELAY = 1.5
SB_DATA_DIR = "/home/pi/projects/raspi/spelling-bee/data"

################################################################
# Internal variables
################################################################

SB_DICT_OFFLINE_DIR = SB_DATA_DIR
SB_DICT_WORD_FILE = "spelling_bee_@YEAR@.txt"
SB_DICT_OFFLINE_DEFN = "sb_@WORD@.dat"
SB_DICT_OFFLINE_CLIP = "sb_@WORD@.wav"

#Sample dictionary API URL - http://www.dictionaryapi.com/api/v1/references/collegiate/xml/test?key=cbbd4001-c94d-493a-ac94-7268a7e41f6f
SB_DICT_MW_KEY="cbbd4001-c94d-493a-ac94-7268a7e41f6f"
SB_DICT_MW_ENTRY_URL="http://www.dictionaryapi.com/api/v1/references/collegiate/xml/@WORD@?key=" + SB_DICT_MW_KEY
SB_DICT_MW_CLIP_URL="http://media.merriam-webster.com/soundc11/@FOLDER@/@CLIP@"

SB_LIST_BULLET = '•'
SB_RIGHT_SYMBOL = '√'
SB_WRONG_SYMBOL = 'X'
SB_PRACTICE_KEYBOARD_MENU = "[N]ext [P]revious [R]epeat Re[v]iew [S]how [L]ookup [H]elp E[x]it"
SB_TEST_KEYBOARD_MENU = "E[x]it"

SB_TMP_WORD_ENTRY = "sbtmpentry.xml"
SB_TMP_WORD_DEFN = "sbtmpdefn.dat"
SB_TMP_WORD_CLIP = "sbtmpclip.wav"
SB_TMP_TEST_RESULTS = "sbtmptest.dat"

SB_ERR_LOG = "sberr.log"
SB_DICT_MW_ENTRY_ERR=0
SB_DICT_MW_CLIP_ERR=0


class SpellingBee(object):
    """
    A Spelling Bee assistant to help with word list navigation and dictionary lookup.
    It has the following attributes:
        contestYear: A string representing the year of the spelling bee contest
        wordList: A list containing words loaded from wordFile
        activeChapter: 
        activeRangeStart: 
        activeRangeEnd: 

        word_count():
        chapter_count():
        active_word_count():
    """
    def __init__(self, year, mode, selection):
        self.contestYear = year

        wordFileName = SB_DATA_DIR + "/" + SB_DICT_WORD_FILE
        wordFileName = wordFileName.replace("@YEAR@", year)
        wordFile = open(wordFileName, "r")
        self.wordList = wordFile.read().splitlines()                # Use of splitlines() avoids the newline character from being stored in the word list
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
            # todo: Implement regex based search in list
            self.activeRangeStart = self.wordList.index(rangeSelection[0])
            if len(rangeSelection) > 1:
                self.activeRangeEnd = self.wordList.index(rangeSelection[1])
            else:
                self.activeRangeEnd = len(self.wordList) - 1

        if self.activeRangeEnd >= len(self.wordList):
            self.activeRangeEnd = len(self.wordList) - 1

    def word_count(self):
        return len(self.wordList)

    def chapter_count(self):
        return int(math.ceil(len(self.wordList)/SB_CHAPTER_SIZE))

    def active_word_count(self):
        return (self.activeRangeEnd - self.activeRangeStart + 1)

    def display_about(self):
        print "Spelling Bee " + self.contestYear
        print "Word Count [" + str(self.word_count()) + "] Chapter [" + str(self.activeChapter) + "/" + str(self.chapter_count()) + "] Words [" + str(self.activeRangeStart + 1) + "-" + str(self.activeRangeEnd + 1) + "]"

    def print_active_word_list(self):
        self.display_about()
        # todo: format word list display
        print self.wordList[self.activeRangeStart : self.activeRangeEnd]

    def print_word_meaning(self, index):
        print self.wordList[index] + " meaning"

    def pronounce_word(self, index):
        print self.wordList[index] + " pronunciation"

    def display_word_cue(self, index, title):
        print "\n" + title
        self.print_word_meaning(index)
        for i in range (1, SB_REPEAT_COUNT):
            self.pronounce_word(index)

def capture_user_input(prompt):
    #return raw_input("\n" + prompt)
    print "\n" + prompt ,
    return INPUT.getch()

def run_practice(spellBee):

    spellBee.display_about()
    userInput = capture_user_input("Ready to practice? Press any key when ready ... ")

    wordIndex = spellBee.activeRangeStart

    while True:
        if (wordIndex < spellBee.activeRangeStart) or (wordIndex > spellBee.activeRangeEnd):
            break

        # Lookup word meaning
        spellBee.display_word_cue(wordIndex, "\nWord #" + str(wordIndex) + " means:")
        userInput = capture_user_input("> ")
        print ""
        
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
                spellBee.display_word_cue(wordIndex, "\nWord #" + str(wordIndex) + " means:")
                userInput = capture_user_input("> ")
                print ""
            # Re[v]iew active word list
            elif userInput.lower() == "v":
                spellBee.print_active_word_list()
                userInput = capture_user_input("> ")
                print ""
            # [S]how current word spelling
            elif userInput.lower() == "s":
                print "\nWord #" + str(wordIndex) + " is " + spellBee.wordList[wordIndex]
                userInput = capture_user_input("> ")
                print ""
            # [L]ookup word meaning and pronunciation
            elif userInput.lower() == "l":
                print ""
                print "Under construction..."
                userInput = capture_user_input("> ")
                print ""
            # Display [h]elp and statistics
            elif userInput.lower() == "h":
                print ""
                spellBee.display_about()
                userInput = capture_user_input("> ")
                print ""
            # E[x]it application
            elif userInput.lower() == "x":
                exit()
            else:
                print "\nInvalid response.\n"
                spellBee.display_about()
                userInput = capture_user_input("> ")
                print ""


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

# Run Spelling Bee assistant in practice, test or scan mode
if args.runMode.lower() == "practice" :
    run_practice(spellBee)