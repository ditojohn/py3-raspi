#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################
# Syntax :   sudo python spellit_download_mwonlineapi.py
# where      contestYear is the year of the contest.
# Example:    sudo python spellit_download_lists.py 2016
################################################################

import sys
import argparse
import urllib3

from xml.etree import ElementTree
from bs4 import BeautifulSoup

sys.path.insert(0, "..")
import common.rpimod.stdio.output as coutput
import common.rpimod.stdio.fileio as cfile
import common.rpimod.wordproc.dict.dictionaryapi as cdictassist
import common.rpimod.wordproc.dict.mwonlineapi as cdictapi


SB_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}


########################################################################
# Sample application to test the python module
########################################################################

dictConfig = cdictapi.DictionaryConfig()
dictAssist = cdictassist.DictionaryAssistant(dictConfig)

listFile = 'data/spelling_bee_overrides.txt'
connectionPool = urllib3.PoolManager(10, headers=SB_USER_AGENT)

for activeWord in cfile.read(listFile).splitlines():

    print "+++++++++++++++++++++++++++++++++++++++++++"
    print activeWord
    print "+++++++++++++++++++++++++++++++++++++++++++"

    #activeWord=u'cephalalgia'
    saveFile = activeWord + u".html"
    overrideFile = activeWord + u".dat"

    ##### Online Entry #####
    activeEntry = dictAssist.download_entry(connectionPool, activeWord)
    cfile.write(saveFile, activeEntry)

    ##### Offline Entry #####
    connectionData = cfile.read(saveFile)

    wordDictionary = cdictapi.DictionaryEntry(dictConfig, activeWord, connectionData)
    print len(wordDictionary.word_entries)
    print "+++++++++++++++++++++++++++++++++++++++++++"
    print wordDictionary.simplified_word_entry
    print "+++++++++++++++++++++++++++++++++++++++++++"
    
    overrideData = wordDictionary.simplified_word_entry.generate_override()
    print overrideData
    #cfile.write(overrideFile, overrideData)


connectionPool.clear()
