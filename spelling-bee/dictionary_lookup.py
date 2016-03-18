#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################
# Syntax :   sudo python dictionary_lookup.py searchWord
# where      searchWord is the word whose definition is to be looked up.
# Example:    sudo python dictionary_lookup.py hopeful
################################################################

import sys
import argparse
import urllib3

sys.path.insert(0, "..")
import common.rpimod.wordproc.dict.dictionary as cdict

DICT_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}

DICT_AUDIO_OUTPUT = 'Speaker'
DICT_REPEAT_COUNT = 1
DICT_REPEAT_DELAY = 1.5

################################################################
# Main Program
################################################################

# Process command line arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("searchWord", type=str, help="is the word whose definition is to be looked up")
argParser.add_argument("dictionary", type=str, nargs='?', help="is the dictionary source")
args = argParser.parse_args()

connectionPool = urllib3.PoolManager(10, headers=DICT_USER_AGENT)

if args.dictionary is None:
    cdict.lookup_word(connectionPool, DICT_AUDIO_OUTPUT, DICT_REPEAT_COUNT, DICT_REPEAT_DELAY, args.searchWord)
else:
    cdict.lookup_word(connectionPool, DICT_AUDIO_OUTPUT, DICT_REPEAT_COUNT, DICT_REPEAT_DELAY, args.searchWord, args.dictionary)

connectionPool.clear()
