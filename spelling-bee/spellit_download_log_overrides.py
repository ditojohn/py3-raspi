#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################
# Syntax :   sudo python spellit_download_log_overrides.py
# Example:    sudo python spellit_download_log_overrides.py
################################################################

import sys
import re
import urllib3

sys.path.insert(0, "..")
import common.rpimod.stdio.output as coutput
import common.rpimod.stdio.fileio as cfile
import common.rpimod.wordproc.dict.dictionary as cdict

SDO_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}

SDO_LIST_FILE = unicode("data/log/spelling_bee_errors.log", 'utf-8')
SDO_OVERRIDE_DEFN_FILE = unicode("data/download/sb_{WORD}.dat", 'utf-8')
SDO_OVERRIDE_PRON_FILE = unicode("data/download/sb_{WORD}.mp3", 'utf-8')
SDO_LOG_FILE = unicode("data/log/spellit_download_log_overrides.log", 'utf-8')

SDO_ERR_DEFN_REGEX_PATTERN = re.compile(".*Definition Missing.*")
SDO_ERR_AUDIO_REGEX_PATTERN = re.compile(".*Audio (Missing|Mismatch).*")
SDO_ERR_DEFN_MISSING = False
SDO_ERR_CLIP_MISSING = False

################################################################
# Main Program
################################################################

connectionPool = urllib3.PoolManager(10, headers=SDO_USER_AGENT)

logEntries = cfile.read(SDO_LIST_FILE).splitlines()

print "Downloading overrides ..."

for entry in logEntries:
    logValues = entry.split(':')
    
    word = logValues[1]
    wordEntry = cdict.fetch_dictionary_entry(connectionPool, word)
    SDO_ERR_DEFN_MISSING = False
    SDO_ERR_CLIP_MISSING = False

    print unicode("Word: {0}\t{1}", 'utf-8').format(word, logValues[2])

    if SDO_ERR_DEFN_REGEX_PATTERN.match(logValues[2]):
        if len(wordEntry[1]) > 0:
            print ">> Downloaded definition override"
            cfile.write(SDO_OVERRIDE_DEFN_FILE.format(WORD=word), coutput.multiline_text(wordEntry[1]))
        else:
            SDO_ERR_DEFN_MISSING = True
            coutput.print_color('yellow', "WARNING: Definition override not available")
 
    if SDO_ERR_AUDIO_REGEX_PATTERN.match(logValues[2]):
        if wordEntry[4] != "":
            print ">> Downloaded pronunciation override"
            cfile.download(connectionPool, wordEntry[4], SDO_OVERRIDE_PRON_FILE.format(WORD=word))
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
sudo python spellit_download_log_overrides.py
'''
