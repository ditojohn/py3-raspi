#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : google.py
# Description : Dictionary lookup functions sourcing from Google
# Author      : Dito Manavalan
# Date        : 2016/02/20
#--------------------------------------------------------------------------------------------------

import sys
import re
from xml.dom import minidom

sys.path.insert(0, "/home/pi/projects/raspi")
import common.rpimod.stdio.output as coutput

# Set to True to turn debug messages on
ERR_DEBUG = False

################################################################
# Dictionary Configuration Variables
################################################################

# Sample dictionary API URL - http://www.dictionaryapi.com/api/v1/references/collegiate/xml/test?key=cbbd4001-c94d-493a-ac94-7268a7e41f6f
DICT_ENTRY_URL = unicode("http://www.dictionaryapi.com/api/v1/references/collegiate/xml/{WORD}?key={KEY}", 'utf-8')
DICT_AUDIO_URL = unicode("http://media.merriam-webster.com/soundc11/{FOLDER}/{CLIP}", 'utf-8')
DICT_KEY = unicode("cbbd4001-c94d-493a-ac94-7268a7e41f6f", 'utf-8')

DICT_ASCII_EMPTY_STR = ""
DICT_UNICODE_EMPTY_STR = unicode("", 'utf-8')

import urllib3

from bs4 import BeautifulSoup

connectionPool = urllib3.PoolManager()
htmlResponse = connectionPool.request('GET', 'http://www.google.com/search?q=define%3Acloud')
#print htmlResponse.data
connectionPool.clear()

soup = BeautifulSoup(htmlResponse.data, 'html.parser')
#print soup.prettify()

divElements = soup.find(class_="vk_ans")
for element in divElements:
    print "found keyword"
    print element



