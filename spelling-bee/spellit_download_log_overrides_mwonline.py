#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################
# Syntax :   sudo python spellit_download_log_overrides_mwonline.py
# Example:    sudo python spellit_download_log_overrides_mwonline.py
################################################################

import os
import sys
import re
import urllib3

sys.path.insert(0, "..")
import common.rpimod.stdio.output as coutput
import common.rpimod.stdio.fileio as cfile
import common.rpimod.wordproc.dict.dictionaryapi as cdictassist
import common.rpimod.wordproc.dict.mwonlineapi as cdictapi

SDO_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}

SDO_LIST_FILE = unicode("data/log/spelling_bee_errors.list", 'utf-8')
SDO_LOG_FILE = unicode("data/log/spellit_download_log_overrides_mwonline.log", 'utf-8')

SDO_OVERRIDE_ENTRY_FILE = unicode("data/download/tmp/sb_{WORD}.html", 'utf-8')
SDO_OVERRIDE_DEFN_FILE = unicode("data/download/sb_{WORD}.dat", 'utf-8')
SDO_OVERRIDE_PRON_FILE = unicode("data/download/sb_{WORD}.mp3", 'utf-8')

SDO_ERR_DEFN_REGEX_PATTERN = re.compile(".*Definition Missing.*")
SDO_ERR_AUDIO_REGEX_PATTERN = re.compile(".*Audio (Missing|Mismatch).*")
SDO_ERR_DEFN_MISSING = False
SDO_ERR_CLIP_MISSING = False

# Set to True to turn debug messages on
#SDO_ERR_DEBUG = True
SDO_ERR_DEBUG = False

################################################################
# Main Program
################################################################

_FUNC_NAME_ = "main"

dictConfig = cdictapi.DictionaryConfig()
dictAssist = cdictassist.DictionaryAssistant(dictConfig)

connectionPool = urllib3.PoolManager(10, headers=SDO_USER_AGENT)

logEntries = cfile.read(SDO_LIST_FILE).splitlines()

print "Downloading overrides ..."

for entry in logEntries:
    coutput.print_watcher(SDO_ERR_DEBUG, _FUNC_NAME_, 'entry')

    logValues = entry.split(':')
    
    word = logValues[1]
    
    if not os.path.isfile(SDO_OVERRIDE_ENTRY_FILE.format(WORD=word)):
        cfile.write(SDO_OVERRIDE_ENTRY_FILE.format(WORD=word), dictAssist.download_entry(connectionPool, word))
    
    wordEntry = cfile.read(SDO_OVERRIDE_ENTRY_FILE.format(WORD=word))
    wordDictionary = cdictapi.DictionaryEntry(dictConfig, word, wordEntry)
    coutput.print_watcher(SDO_ERR_DEBUG, _FUNC_NAME_, 'wordEntry')

    SDO_ERR_DEFN_MISSING = False
    SDO_ERR_CLIP_MISSING = False
    
    print unicode("\nWord: {0}\t{1}", 'utf-8').format(word, logValues[2])

    if SDO_ERR_DEFN_REGEX_PATTERN.match(logValues[2]):
        coutput.print_watcher(SDO_ERR_DEBUG, _FUNC_NAME_, 'wordEntry[1]')
        if len(wordDictionary.word_entries) > 0 and len(wordEntry[1]) > 0:
            print ">> Downloaded definition override"

            overrideData = wordDictionary.simplified_word_entry.generate_override()
            coutput.print_watcher(SDO_ERR_DEBUG, _FUNC_NAME_, 'overrideData')
            cfile.write(SDO_OVERRIDE_DEFN_FILE.format(WORD=word), overrideData)

        else:
            SDO_ERR_DEFN_MISSING = True
            coutput.print_color('yellow', "WARNING: Definition override not available")
 
    if SDO_ERR_AUDIO_REGEX_PATTERN.match(logValues[2]):
        coutput.print_watcher(SDO_ERR_DEBUG, _FUNC_NAME_, 'wordDictionary.simplified_word_entry.pronunciation')
        if wordDictionary.simplified_word_entry.pronunciation is not None and wordDictionary.simplified_word_entry.pronunciation.audio_url != "" :
            print ">> Downloaded pronunciation override"
            cfile.download(connectionPool, wordDictionary.simplified_word_entry.pronunciation.audio_url, SDO_OVERRIDE_PRON_FILE.format(WORD=word))
        else:
            SDO_ERR_CLIP_MISSING = True
            coutput.print_color('yellow', "WARNING: Pronunciation override not available")

    # Log errors
    errorText = unicode("ERROR:{0}:", 'utf-8').format(word)
    if SDO_ERR_DEFN_MISSING:
        errorText += unicode(">Definition Missing", 'utf-8')
    if SDO_ERR_CLIP_MISSING:
        errorText += unicode(">Audio Missing", 'utf-8')
    
    if errorText != unicode("ERROR:{0}:", 'utf-8').format(word):
        errorText += unicode("\n", 'utf-8')
        cfile.append(SDO_LOG_FILE, errorText)

connectionPool.clear()


########################################################################
# Debugging Commands
########################################################################
'''
cd $PROJ
sudo python spellit_download_log_overrides_mwonline.py
'''
