#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################
# Syntax :   sudo python spellit_download_mwapi.py
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
import common.rpimod.wordproc.dict.mwcollegiateapi as cdictapi


SB_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}
SB_CONN_URL = unicode("https://www.merriam-webster.com/dictionary/{WORD}", 'utf-8')

word = "turpentine"

########################################################################
# Sample application to test the python module
########################################################################

#connectionPool = urllib3.PoolManager(10, headers=SB_USER_AGENT)
#connectionURL = SB_CONN_URL.format(WORD=word).replace(" ", "%20").encode('utf-8')
#connectionResponse = connectionPool.request('GET', connectionURL)
#connectionData = connectionResponse.data
#connectionPool.clear()

word=u'turpentine'
connectionData = cfile.read('turpentine.xml')

dictConfig = cdictapi.DictionaryConfig()
wordDictionary = cdictapi.DictionaryEntry(dictConfig, word, connectionData)
print wordDictionary.word_entries
print wordDictionary.simplified_word_entry

"""
for entry in soup.find_all("entry", limit=1):
    for ew in entry.find_all("ew", limit=1):
        print ew.get_text()
    for fl in entry.find_all("fl", limit=1):
        print fl.get_text()
    for hw in entry.find_all("hw", limit=1):
        print hw.get_text()
    for pr in entry.find_all("pr", limit=1):
        print pr.get_text()
    for et in entry.find_all("et", limit=1):
        print et.get_text()
    for dt in entry.find_all("dt"):
        print dt.get_text()
"""