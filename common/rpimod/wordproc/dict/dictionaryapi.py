#!/usr/bin/env python
# -*- encoding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : dictionaryapi.py
# Description : Standardized dictionary API implementation
# Author      : Dito Manavalan
# Date        : 2018/01/11
#--------------------------------------------------------------------------------------------------

################################################################
# Source: Merriam-Webster's Collegiate Dictionary
# Sample Search URL: http://www.merriam-webster.com/dictionary/test
# Sample API URL: http://www.dictionaryapi.com/api/v1/references/collegiate/xml/test?key=cbbd4001-c94d-493a-ac94-7268a7e41f6f
# Sample Pronunciation URL: http://media.merriam-webster.com/soundc11/t/test0001.wav
# References:
# Source Project: https://github.com/pfeyz/merriam-webster-api
# XML Specification for Merriam-Webster's Collegiate Dictionary: http://www.dictionaryapi.com/content/products/documentation/collegiate-tag-description.txt
################################################################

import sys
import re
import urllib3
import copy
import pkg_resources

#from abc import ABCMeta, abstractmethod, abstractproperty
from bs4 import BeautifulSoup

sys.path.insert(0, "..")
import common.rpimod.stdio.output as cout
import common.rpimod.stdio.fileio as cfile

# Set to True to turn debug messages on
SB_ERR_DEBUG = True

################################################################
# General Lexical Variables and Functions
################################################################

DICT_UNICODE_EMPTY_STR = unicode("", 'utf-8')
DICT_UNICODE_FALLBACK_STR = unicode("<None>", 'utf-8')

DICT_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}


def format_txt(caption, element):
    if type(element) is not list:
        elementText = u"{0}: {1}\n".format(caption, cout.coalesce(element, DICT_UNICODE_FALLBACK_STR))
    else:
        if len(element) <= 0:
            elementText = u"{0}: {1}\n".format(caption, DICT_UNICODE_FALLBACK_STR)
        else:
            elementText = u"{0}:\n".format(caption)
            for line in element:
                elementText = elementText + u"\t{0}\n".format(line)

    return elementText


def format_obj(caption, element):
    if type(element) is not list:
        if element is None:
            elementText = u"{0}: {1}\n".format(caption, DICT_UNICODE_FALLBACK_STR)
        else:
            elementText = u"{0}:\n".format(caption)
            for line in unicode(element).splitlines():
                elementText = elementText + u"\t{0}\n".format(line)
    else:
        if len(element) <= 0:
            elementText = u"{0}: {1}\n".format(caption, DICT_UNICODE_FALLBACK_STR)
        else:
            elementText = u"{0}:\n".format(caption)
            for obj in element:
                for line in unicode(obj).splitlines():
                    elementText = elementText + u"\t{0}\n".format(line)

    return elementText


################################################################
# Exception Classes
################################################################

class WordNotFoundException(KeyError):
    def __init__(self, word, suggestions=None, *args, **kwargs):
        self.word = word
        if suggestions is None:
            suggestions = []
        self.suggestions = suggestions
        message = unicode("'{0}' not found.", 'utf-8').format(word)
        if suggestions:
            message = unicode("{0} Try: {1}", 'utf-8').format(message, ", ".join(suggestions))
        KeyError.__init__(self, message, *args, **kwargs)

class InvalidResponseException(WordNotFoundException):
    def __init__(self, word, *args, **kwargs):
        self.word = word
        self.suggestions = []
        message = "{0} not found. (Malformed XML from server).".format(word)
        KeyError.__init__(self, message, *args, **kwargs)

class InvalidAPIKeyException(Exception):
    pass

################################################################
# General Dictionary Structure Classes
################################################################

class WordIllustration(object):
    def __init__(self, illustration_url):
        self.illustration_url = illustration_url
        self.caption = DICT_UNICODE_EMPTY_STR
        self.form = DICT_UNICODE_EMPTY_STR

    def __unicode__(self):
        objectText = u""
        objectText = objectText + format_txt(u'[Illustration URL]', self.illustration_url)
        objectText = objectText + format_txt(u'[Caption         ]', self.caption)
        objectText = objectText + format_txt(u'[Word Form       ]', self.form)
        return objectText

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return "WordIllustration({0})".format(self.__str__())

    def __iter__(self):
        yield self.illustration_url
        yield self.caption
        yield self.form


class WordPronunciation(object):
    def __init__(self, pron_url):
        self.audio_url = pron_url
        self.word_pronunciation = DICT_UNICODE_EMPTY_STR
        self.form = DICT_UNICODE_EMPTY_STR

    def __unicode__(self):
        objectText = u""
        objectText = objectText + format_txt(u'[Audio URL         ]', self.audio_url)
        objectText = objectText + format_txt(u'[Word Pronunciation]', self.word_pronunciation)
        objectText = objectText + format_txt(u'[Word Form         ]', self.form)
        return objectText

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return "WordPronunciation({0})".format(self.__str__())

    def __iter__(self):
        yield self.audio_url
        yield self.word_pronunciation
        yield self.form


class WordRespelling(object):
    def __init__(self, text, source):
        self.text = text
        self.source = source
        self.form = DICT_UNICODE_EMPTY_STR

    def __unicode__(self):
        objectText = u""
        objectText = objectText + format_txt(u'[Text     ]', self.text)
        objectText = objectText + format_txt(u'[Source   ]', self.source)
        objectText = objectText + format_txt(u'[Word Form]', self.form)
        return objectText

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return "WordRespelling({0})".format(self.__str__())

    def __iter__(self):
        yield self.text
        yield self.source
        yield self.form
        

class WordInflection(object):
    def __init__(self, form):
        self.form = form
        self.functional_label = DICT_UNICODE_EMPTY_STR
        self.pronunciation = None
        self.respelling = None
        self.senses = []

    def __unicode__(self):
        objectText = u""
        objectText = objectText + format_txt(u'[Word Form    ]', self.form)
        objectText = objectText + format_txt(u'[Func. Label  ]', self.functional_label)
        objectText = objectText + format_obj(u'[Pronunciation]', self.pronunciation)
        objectText = objectText + format_obj(u'[Respelling   ]', self.respelling)
        objectText = objectText + format_obj(u'[Senses       ]', self.senses)
        return objectText

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return "WordInflection({0})".format(self.__str__())

    def __iter__(self):
        yield self.functional_label
        yield self.form


class WordSense(object):
    def __init__(self, definition):
        self.definition = definition
        self.examples = []
        self.date = DICT_UNICODE_EMPTY_STR

    def __unicode__(self):
        objectText = u""
        objectText = objectText + format_txt(u'[Definition]', self.definition)
        objectText = objectText + format_txt(u'[Date      ]', self.date)
        objectText = objectText + format_txt(u'[Examples  ]', self.examples)
        return objectText
        
    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return "WordSense({0})".format(self.__str__())

    def __iter__(self):
        yield self.date
        yield self.definition
        yield self.examples


class WordEntry(object):
    def __init__(self, source, entry_word):
        self.source = source
        self.entry_word = entry_word
        self.head_word = DICT_UNICODE_EMPTY_STR
        self.functional_label = DICT_UNICODE_EMPTY_STR
        self.word_syllables = DICT_UNICODE_EMPTY_STR
        self.pronunciation = None
        self.respelling = None
        self.etymology = DICT_UNICODE_EMPTY_STR
        self.senses = []
        self.inflections = []
        self.illustrations = []
        

    def __unicode__(self):
        objectText = u""
        objectText = objectText + format_txt(u'[Source        ]', self.source)
        objectText = objectText + format_txt(u'[Entry Word    ]', self.entry_word)
        objectText = objectText + format_txt(u'[Head Word     ]', self.head_word)
        objectText = objectText + format_txt(u'[Func. Label   ]', self.functional_label)
        objectText = objectText + format_txt(u'[Etymology     ]', self.etymology)
        objectText = objectText + format_txt(u'[Word Syllables]', self.word_syllables)
        objectText = objectText + format_obj(u'[Pronunciation ]', self.pronunciation)
        objectText = objectText + format_obj(u'[Respelling    ]', self.respelling)
        objectText = objectText + format_obj(u'[Senses        ]', self.senses)
        objectText = objectText + format_obj(u'[Inflections   ]', self.inflections)
        objectText = objectText + format_obj(u'[Illustrations ]', self.illustrations)
        return objectText

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return "WordEntry({0})".format(self.__str__())


class SimplifiedWordEntry(object):
    def __init__(self, source, key_word, entry_word):
        self.source = source
        self.key_word = key_word
        self.entry_word = entry_word
        self.functional_label = DICT_UNICODE_EMPTY_STR
        self.pronunciation = None
        self.respelling = None
        self.etymology = DICT_UNICODE_EMPTY_STR
        self.definitions = []

    def __unicode__(self):
        objectText = u""
        objectText = objectText + format_txt(u'[Key Word     ]', self.key_word)
        objectText = objectText + format_txt(u'[Entry Word   ]', self.entry_word)
        objectText = objectText + format_txt(u'[Func. Label  ]', self.functional_label)
        objectText = objectText + format_txt(u'[Etymology    ]', self.etymology)
        objectText = objectText + format_obj(u'[Pronunciation]', self.pronunciation)
        objectText = objectText + format_obj(u'[Respelling   ]', self.respelling)
        objectText = objectText + format_obj(u'[Definitions  ]', self.definitions)
        return objectText

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return "SimplifiedWordEntry({0})".format(self.__str__())

################################################################
# Base Dictionary
################################################################

class DictionaryConfig(object):
    def __init__(self):

        # Configuration Attributes
        self.name = DICT_UNICODE_EMPTY_STR
        self.pronunciation_guide_file = DICT_UNICODE_EMPTY_STR
        self.entry_url_format = DICT_UNICODE_EMPTY_STR
        self.audio_url_format = DICT_UNICODE_EMPTY_STR
        self.illustration_url_format = DICT_UNICODE_EMPTY_STR
        self.api_key = DICT_UNICODE_EMPTY_STR
        self.parser = DICT_UNICODE_EMPTY_STR
        self.pronunciation_guide = []


    def build_entry_url(self, key_word):
        _FUNC_NAME_ = "DictionaryConfig.build_entry_url"

        return self.entry_url_format.format(WORD=key_word).replace(u" ", u"%20")


    def build_pronunciation_guide(self):
        _FUNC_NAME_ = "DictionaryConfig.build_pronunciation_guide"

        pronunciation_guide = []
        if self.pronunciation_guide_file != DICT_UNICODE_EMPTY_STR:
            guideFile = pkg_resources.resource_filename( __name__, self.pronunciation_guide_file)
            pronunciation_guide = cfile.read(guideFile).splitlines()

        return pronunciation_guide


    def pronunciation_key(self, respelling):
        _FUNC_NAME_ = "DictionaryConfig.pronunciation_key"

        pronunciation_key = []
        if respelling != DICT_UNICODE_EMPTY_STR:
            
            isLegend = False
            for guideEntry in self.pronunciation_guide:
                if guideEntry == DICT_UNICODE_EMPTY_STR:
                    isLegend = True

                if isLegend == False:
                    phoneme = re.search(ur"\\(.*)\\", guideEntry).group(1)
                    if phoneme is not None and phoneme in respelling:
                        pronunciation_key.append(guideEntry)
                else:
                    pronunciation_key.append(guideEntry)

        return pronunciation_key


class DictionaryEntry(object):
    def __init__(self, dict_config, key_word, entry_raw_text):
        _FUNC_NAME_ = "DictionaryEntry.__init__"

        # Configuration Attributes
        self.config = dict_config

        # Lexical Attributes
        self.key_word = key_word
        self.entry_raw_text = entry_raw_text
        self.word_entries = []
        self.simplified_word_entry = None

        self.set_word_entries()
        self.set_simplified_word_entry()


    def build_audio_url(self, url_fragment):
        _FUNC_NAME_ = "DictionaryEntry.build_audio_url"
        return url_fragment


    def build_illustration_url(self, url_fragment):
        _FUNC_NAME_ = "DictionaryEntry.build_illustration_url"
        return url_fragment


    def set_word_entries(self):
        pass

    
    def set_simplified_word_entry(self):
                
        simplifiedWordEntry = None

        matchEntries = []
        matchInflection = None
        matchType = "none"
        matchEntryFound = False
        
        # Identify matching entry
        
        # Pass #1: Find matching entry word
        if not matchEntryFound:
            for we in self.word_entries:
                if self.key_word == we.entry_word:
                    matchEntries.append(we)
                    matchEntryFound = True
                    matchType = "entryword"

        # Pass #2: Find matching inflection
        if not matchEntryFound:
            for we in self.word_entries:
                for infl in we.inflections:
                    if self.key_word == infl.form:
                        matchEntries.append(we)
                        matchInflection = infl
                        matchEntryFound = True
                        matchType = "inflection"
                        break

                if matchEntryFound:
                    break

        # Pass #3: Default as first entry, if no match found
        if not matchEntryFound:
            for we in self.word_entries:
                matchEntries.append(we)
                matchEntryFound = True
                matchType = "default"
                break

        # Populate conformed entry attributes
        if matchEntryFound:
            simplifiedWordEntry = SimplifiedWordEntry(matchEntries[0].source, self.key_word, matchEntries[0].entry_word)
        
            # Populate pronunciation attributes
            if matchType == "inflection":
                simplifiedWordEntry.functional_label = cout.coalesce(matchInflection.functional_label, matchEntries[0].functional_label)

                elementText = cout.coalesce(matchInflection.pronunciation.audio_url, matchEntries[0].pronunciation.audio_url)
                simplifiedWordEntry.pronunciation = WordPronunciation(elementText)
                simplifiedWordEntry.pronunciation.word_pronunciation = cout.coalesce(matchInflection.pronunciation.word_pronunciation, matchEntries[0].pronunciation.word_pronunciation)
                simplifiedWordEntry.pronunciation.form = cout.coalesce(matchInflection.pronunciation.form, matchEntries[0].pronunciation.form)

                elementText = cout.coalesce(matchInflection.respelling.text, matchEntries[0].respelling.text)
                sourceText = cout.coalesce(matchInflection.respelling.source, matchEntries[0].respelling.source)
                simplifiedWordEntry.respelling = WordRespelling(elementText, sourceText)
                simplifiedWordEntry.respelling.form = cout.coalesce(matchInflection.respelling.form, matchEntries[0].respelling.form)

            else:
                simplifiedWordEntry.functional_label = matchEntries[0].functional_label
                simplifiedWordEntry.pronunciation = copy.deepcopy(matchEntries[0].pronunciation)
                simplifiedWordEntry.respelling = copy.deepcopy(matchEntries[0].respelling)
               
            # Consolidate etymology and senses (definitions and examples)           
            etymologies = []
            definitions = []

            for we in matchEntries:
                
                if we.etymology != DICT_UNICODE_EMPTY_STR and we.etymology not in etymologies:
                    etymologies.append(we.etymology)

                flText = DICT_UNICODE_EMPTY_STR
                if we.functional_label != DICT_UNICODE_EMPTY_STR:
                    flText = u"({0}) ".format(we.functional_label)

                for sense in we.senses:
                    defnText = flText + unicode(sense.definition)
                    if defnText not in definitions:
                        definitions.append(defnText)
            
            simplifiedWordEntry.etymology = u"; ".join(et for et in etymologies)
            simplifiedWordEntry.definitions = definitions[:]

            # Set conformed entry
            self.simplified_word_entry = simplifiedWordEntry


class DictionaryAssistant(object):
    def __init__(self, dict_config):
        _FUNC_NAME_ = "DictionaryAssistant.__init__"

        # Set configuration attributes
        self.config = dict_config
        # Open connection pool
        self.connectionPool = urllib3.PoolManager(10, headers=DICT_USER_AGENT)


    def __del__(self):
        self.connectionPool.clear()


    def download_entry(self, key_word):
        _FUNC_NAME_ = "DictionaryAssistant.download_entry"

        connectionResponse = self.connectionPool.request('GET', self.config.build_entry_url(key_word))
        return connectionResponse.data
