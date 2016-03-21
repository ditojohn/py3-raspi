#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################
# Syntax :   sudo python spellit_download_lists.py contestYear
# where      contestYear is the year of the contest.
# Example:    sudo python spellit_download_lists.py 2016
################################################################

import sys
import argparse
import urllib3

sys.path.insert(0, "..")
import common.rpimod.stdio.output as coutput
import common.rpimod.stdio.fileio as cfile
import common.rpimod.wordproc.textparser as cparser

SB_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}

SB_WORD_LIST_URL = {
    '2016': 'http://myspellit.com/print_{LANG}.html'
}

SB_WORD_LIST_OUT = {
    '2016': 'data/downloads/spelling_bee_{YEAR}-{SEQ}-{LANG}-{TYPE}.txt'
}

SB_WORD_LIST = {
    '2016': [
        'Latin',
        'Arabic',
        'Asian Languages',
        'French',
        'Eponyms',
        'German',
        'Slavic Languages',
        'Dutch',
        'Old English',
        'New World Languages',
        'Japanese',
        'Greek',
        'Italian',
        'Spanish'
    ]
}

SB_CLEAN_TEXT_PATTERNS = [
    r'<span.*?>.*?</span>',
    r'<div class="section tip spell">.*?</div>'
]

SB_CLEAN_INNER_TEXT_PATTERNS = [
]

SB_CLEAN_OUTER_TEXT_PATTERNS = [
]

'''
################################################################
# Main Program
################################################################

# Process command line arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("contestYear", type=str, help="is the year of the contest")
args = argParser.parse_args()

connectionPool = urllib3.PoolManager(10, headers=SB_USER_AGENT)

listYear = args.contestYear
for index, listID in enumerate(SB_WORD_LIST[args.contestYear]):
    print "\nProcessing language: " + listID

    listSeq = str(index + 1).zfill(3)
    
    listLang = listID.lower().replace(' ', '_')
    listURL = SB_WORD_LIST_URL[args.contestYear].format(LANG=listLang)

    listURLResponse = connectionPool.request('GET', listURL)
    listURLData = listURLResponse.data.decode('cp1252')

    if isinstance(listURLData, str):
        listRawText = unicode(listURLData, 'utf-8')
    else:
        listRawText = listURLData
    
    cleansedText = cparser.cleanse_text(listRawText, SB_CLEAN_TEXT_PATTERNS, SB_CLEAN_INNER_TEXT_PATTERNS, SB_CLEAN_OUTER_TEXT_PATTERNS)

    listLang = listID.lower().replace(' ', '-')

    # Process basic word list
    listType = "basic"
    listFileName = SB_WORD_LIST_OUT[args.contestYear].format(YEAR=listYear, SEQ=listSeq, LANG=listLang, TYPE=listType)

    sectionOuterTextPatterns = [
    [r'.*<div class="section word study">', r'</div>.*']
    ]
    sectionText = cparser.cleanse_text(cleansedText, SB_CLEAN_TEXT_PATTERNS, SB_CLEAN_INNER_TEXT_PATTERNS, sectionOuterTextPatterns)
    words = cparser.find_enclosed_text(r'<li>\s*', r'\s*</li>', sectionText)
    print "Writing " + listFileName
    cfile.write(listFileName, coutput.multiline_text(words))

    # Process challenge word list
    listType = "challenge" 
    listFileName = SB_WORD_LIST_OUT[args.contestYear].format(YEAR=listYear, SEQ=listSeq, LANG=listLang, TYPE=listType)

    sectionOuterTextPatterns = [
    [r'.*<div class="section word challenge">', r'</div>.*']
    ]
    sectionText = cparser.cleanse_text(cleansedText, SB_CLEAN_TEXT_PATTERNS, SB_CLEAN_INNER_TEXT_PATTERNS, sectionOuterTextPatterns)
    words = cparser.find_enclosed_text(r'<li>\s*', r'\s*</li>', sectionText)
    print "Writing " + listFileName
    cfile.write(listFileName, coutput.multiline_text(words))

connectionPool.clear()
'''

########################################################################
# Debugging Commands
########################################################################
'''
cd $PROJ
sudo python spellit_download_lists.py 2016
'''

########################################################################
# Sample application to test the python module
########################################################################

connectionPool = urllib3.PoolManager(10, headers=SB_USER_AGENT)

#listURLResponse = connectionPool.request('GET', 'http://myspellit.com/print_french.html')
#print listURLResponse.data.decode('cp1252')

textlines = cfile.read('data/downloads/spelling_bee_2016-003-asian-languages-challenge.txt').splitlines()
print len(textlines)
print textlines

connectionPool.clear()

