#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################
# Syntax :   sudo python spellit_download_overrides.py
# Example:    sudo python spellit_download_overrides.py
################################################################

import sys
import urllib3

sys.path.insert(0, "..")
import common.rpimod.stdio.output as coutput
import common.rpimod.stdio.fileio as cfile
import common.rpimod.wordproc.dict.dictionary as cdict

SDO_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}

SDO_CONF_FILE = "conf/spellit_get_words_list.dat"
SDO_OVERRIDE_DEFN_FILE = "data/download/sb_{WORD}.dat"
SDO_OVERRIDE_PRON_FILE = "data/download/sb_{WORD}.mp3"

################################################################
# Main Program
################################################################

connectionPool = urllib3.PoolManager(10, headers=SDO_USER_AGENT)

wordList = cfile.read(SDO_CONF_FILE).splitlines()

print u"Downloading overrides ..."
for word in wordList:
    print u"Word: " + word
    wordEntry = cdict.fetch_dictionary_entry(connectionPool, word)
    
    if len(wordEntry[1]) > 0:
        cfile.write(SDO_OVERRIDE_DEFN_FILE.format(WORD=word), coutput.multiline_text(wordEntry[1]))
    else:
        coutput.print_color('yellow', "WARNING: Definition override not available")
    if wordEntry[4] != "":
        cfile.download(connectionPool, wordEntry[4], SDO_OVERRIDE_PRON_FILE.format(WORD=word))
    else:
        coutput.print_color('yellow', "WARNING: Pronunciation override not available")


connectionPool.clear()


########################################################################
# Debugging Commands
########################################################################
'''
cd $PROJ
sudo python spellit_download_overrides.py
'''
