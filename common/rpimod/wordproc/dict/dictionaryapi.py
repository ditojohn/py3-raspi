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
import common.rpimod.stdio.output as coutput
import common.rpimod.stdio.fileio as cfile

# Set to True to turn debug messages on
#APP_DEBUG_MODE_ENABLED = True
APP_DEBUG_MODE_ENABLED = False

################################################################
# General Lexical Variables and Functions
################################################################

DICT_UNICODE_EMPTY_STR = ""
DICT_UNICODE_FALLBACK_STR = "<None>"


def format_txt(caption, element):
    if type(element) is not list:
        elementText = "{0}: {1}\n".format(caption, coutput.coalesce(element, DICT_UNICODE_FALLBACK_STR))
    else:
        if len(element) <= 0:
            elementText = "{0}: {1}\n".format(caption, DICT_UNICODE_FALLBACK_STR)
        else:
            elementText = "{0}:\n".format(caption)
            for line in element:
                elementText = elementText + "\t{0}\n".format(line)

    return elementText


def format_obj(caption, element):
    if type(element) is not list:
        if element is None:
            elementText = "{0}: {1}\n".format(caption, DICT_UNICODE_FALLBACK_STR)
        else:
            elementText = "{0}:\n".format(caption)
            for line in str(element).splitlines():
                elementText = elementText + "\t{0}\n".format(line)
    else:
        if len(element) <= 0:
            elementText = "{0}: {1}\n".format(caption, DICT_UNICODE_FALLBACK_STR)
        else:
            elementText = "{0}:\n".format(caption)
            for obj in element:
                for line in str(obj).splitlines():
                    elementText = elementText + "\t{0}\n".format(line)

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
        message = "'{0}' not found.".format(word)
        if suggestions:
            message = "{0} Try: {1}".format(message, ", ".join(suggestions))
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
        self.spelling = DICT_UNICODE_EMPTY_STR

    def __unicode__(self):
        objectText = ""
        objectText = objectText + format_txt('[Illustration URL]', self.illustration_url)
        objectText = objectText + format_txt('[Caption         ]', self.caption)
        objectText = objectText + format_txt('[Word Form       ]', self.form)
        objectText = objectText + format_txt('[Word Spelling   ]', self.spelling)
        return objectText

    def __str__(self):
        return str(self.__unicode__())

    def __repr__(self):
        return "WordIllustration({0})".format(self.__str__())

    def __iter__(self):
        yield self.illustration_url
        yield self.caption
        yield self.form
        yield self.spelling


class WordPronunciation(object):
    def __init__(self, pron_url):
        self.audio_url = pron_url
        self.word_pronunciation = DICT_UNICODE_EMPTY_STR
        self.form = DICT_UNICODE_EMPTY_STR
        self.spelling = DICT_UNICODE_EMPTY_STR
        self.audio_file = DICT_UNICODE_EMPTY_STR

    def __unicode__(self):
        objectText = ""
        objectText = objectText + format_txt('[Audio URL         ]', self.audio_url)
        objectText = objectText + format_txt('[Word Pronunciation]', self.word_pronunciation)
        objectText = objectText + format_txt('[Word Form         ]', self.form)
        objectText = objectText + format_txt('[Word Spelling     ]', self.spelling)
        objectText = objectText + format_txt('[Audio File        ]', self.audio_file)
        return objectText

    def __str__(self):
        return str(self.__unicode__())

    def __repr__(self):
        return "WordPronunciation({0})".format(self.__str__())

    def __iter__(self):
        yield self.audio_url
        yield self.word_pronunciation
        yield self.form
        yield self.spelling
        yield self.audio_file


class WordRespelling(object):
    def __init__(self, text, source):
        self.text = text
        self.source = source
        self.form = DICT_UNICODE_EMPTY_STR
        self.spelling = DICT_UNICODE_EMPTY_STR

    def __unicode__(self):
        objectText = ""
        objectText = objectText + format_txt('[Text         ]', self.text)
        objectText = objectText + format_txt('[Source       ]', self.source)
        objectText = objectText + format_txt('[Word Form    ]', self.form)
        objectText = objectText + format_txt('[Word Spelling]', self.spelling)
        return objectText

    def __str__(self):
        return str(self.__unicode__())

    def __repr__(self):
        return "WordRespelling({0})".format(self.__str__())

    def __iter__(self):
        yield self.text
        yield self.source
        yield self.form
        yield self.spelling
        

class WordInflection(object):
    def __init__(self, form):
        self.form = form
        self.spelling = DICT_UNICODE_EMPTY_STR
        self.functional_label = DICT_UNICODE_EMPTY_STR
        self.pronunciation = None
        self.respelling = None
        self.senses = []

    def __unicode__(self):
        objectText = ""
        objectText = objectText + format_txt('[Word Form    ]', self.form)
        objectText = objectText + "\t" + format_txt('[Word Spelling]', self.spelling)
        objectText = objectText + "\t" + format_txt('[Func. Label  ]', self.functional_label)
        objectText = objectText + "\t" + format_obj('[Pronunciation]', self.pronunciation)
        objectText = objectText + "\t" + format_obj('[Respelling   ]', self.respelling)
        objectText = objectText + "\t" + format_obj('[Senses       ]', self.senses)
        return objectText

    def __str__(self):
        return str(self.__unicode__())

    def __repr__(self):
        return "WordInflection({0})".format(self.__str__())

    def __iter__(self):
        yield self.form
        yield self.spelling
        yield self.functional_label
        yield self.pronunciation
        yield self.respelling
        yield self.senses


class WordSense(object):
    def __init__(self, definition):
        self.definition = definition
        self.date = DICT_UNICODE_EMPTY_STR
        self.examples = []


    def __unicode__(self):
        objectText = ""
        objectText = objectText + format_txt('[Definition]', self.definition)
        objectText = objectText + "\t" + format_txt('[Date      ]', self.date)
        objectText = objectText + "\t" + format_txt('[Examples  ]', self.examples)
        return objectText
        
    def __str__(self):
        return str(self.__unicode__())

    def __repr__(self):
        return "WordSense({0})".format(self.__str__())

    def __iter__(self):
        yield self.definition
        yield self.examples
        yield self.date


class WordEntry(object):
    def __init__(self, source, entry_word):
        self.source = source
        self.entry_word = entry_word
        self.head_word = DICT_UNICODE_EMPTY_STR
        self.functional_label = DICT_UNICODE_EMPTY_STR
        self.etymology = DICT_UNICODE_EMPTY_STR
        self.word_syllables = DICT_UNICODE_EMPTY_STR
        self.pronunciation = None
        self.respelling = None
        self.senses = []
        self.inflections = []
        self.illustrations = []
        

    def __unicode__(self):
        objectText = ""
        objectText = objectText + format_txt('[Source        ]', self.source)
        objectText = objectText + format_txt('[Entry Word    ]', self.entry_word)
        objectText = objectText + format_txt('[Head Word     ]', self.head_word)
        objectText = objectText + format_txt('[Func. Label   ]', self.functional_label)
        objectText = objectText + format_txt('[Etymology     ]', self.etymology)
        objectText = objectText + format_txt('[Word Syllables]', self.word_syllables)
        objectText = objectText + format_obj('[Pronunciation ]', self.pronunciation)
        objectText = objectText + format_obj('[Respelling    ]', self.respelling)
        objectText = objectText + format_obj('[Senses        ]', self.senses)
        objectText = objectText + format_obj('[Inflections   ]', self.inflections)
        objectText = objectText + format_obj('[Illustrations ]', self.illustrations)
        return objectText

    def __str__(self):
        return str(self.__unicode__())

    def __repr__(self):
        return "WordEntry({0})".format(self.__str__())


class SimplifiedWordEntry(object):
    def __init__(self, source, key_word, entry_word):
        self.source = source
        self.key_word = key_word
        self.entry_word = entry_word
        self.functional_label = DICT_UNICODE_EMPTY_STR
        self.etymology = DICT_UNICODE_EMPTY_STR
        self.pronunciation = None
        self.respelling = None
        self.definitions = []
        self.usage = []
        self.examples = DICT_UNICODE_EMPTY_STR

    def __unicode__(self):
        objectText = ""
        objectText = objectText + format_txt('[Source       ]', self.source)
        objectText = objectText + format_txt('[Key Word     ]', self.key_word)
        objectText = objectText + format_txt('[Entry Word   ]', self.entry_word)
        objectText = objectText + format_txt('[Func. Label  ]', self.functional_label)
        objectText = objectText + format_txt('[Etymology    ]', self.etymology)
        objectText = objectText + format_obj('[Pronunciation]', self.pronunciation)
        objectText = objectText + format_obj('[Respelling   ]', self.respelling)
        objectText = objectText + format_obj('[Definitions  ]', self.definitions)
        objectText = objectText + format_obj('[Usage        ]', self.usage)
        objectText = objectText + format_txt('[Examples     ]', self.examples)
        return objectText

    def __str__(self):
        return str(self.__unicode__())

    def __repr__(self):
        return "SimplifiedWordEntry({0})".format(self.__str__())

    def has_definitions(self):
        if len(self.definitions) == 0:
            return False
        else:
            return True

    def has_pronunciation(self):
        if self.pronunciation is None:
            return False
        else:
            return True

    def has_pronunciation_audio(self):
        if not self.has_pronunciation():
            return False
        elif self.pronunciation.audio_file == DICT_UNICODE_EMPTY_STR:
            return False
        else:
            return True

    def has_pronunciation_audio_url(self):
        if not self.has_pronunciation():
            return False
        elif self.pronunciation.audio_url == DICT_UNICODE_EMPTY_STR:
            return False
        else:
            return True

    def has_mispronunciation(self):

        if not self.has_pronunciation():
            return False      
        elif self.key_word == self.pronunciation.form:
            return False
        else:
            return True

    def has_respelling(self):
        if self.respelling is None:
            return False
        else:
            return True


    # Override entry
    def override_entry(self, source, entry_word, overrides):

        if len(overrides) > 0:
            self.entry_word = entry_word

            overrideInfo = {}
            overrideDefinitions = []
            for override in overrides:
                if override.startswith('#!'):
                    override_elements = override.split(':')
                    override_name = override_elements[0].strip()
                    override_value = re.sub('^#![a-zA-Z0-9]+: ', DICT_UNICODE_EMPTY_STR, override).strip()
                    
                    if override_value != DICT_UNICODE_EMPTY_STR:
                        overrideInfo[override_name] = override_value
                else:
                    if override != DICT_UNICODE_EMPTY_STR:
                        overrideDefinitions.append(override)

            # Process info lines
            for key in overrideInfo:
                if key == '#!Etymology':
                    self.etymology = overrideInfo[key]

                elif key == '#!AudioURL':
                    if self.pronunciation is None:
                        self.pronunciation = WordPronunciation(overrideInfo[key])
                    else:
                        self.pronunciation.audio_url = overrideInfo[key]

                    if '#!Word' in overrideInfo.keys():
                        self.pronunciation.form = overrideInfo['#!Word']
                        self.pronunciation.spelling = overrideInfo['#!Word']

                elif key == '#!Respelling':
                    if self.respelling is None:
                        self.respelling = WordRespelling(overrideInfo[key], overrideInfo['#!Source'])
                    else:
                        self.respelling.source = self.respelling.source + ';' + overrideInfo['#!Source']
                        self.respelling.text = overrideInfo[key]
                    
                    if '#!Word' in overrideInfo.keys():
                        self.respelling.form = overrideInfo['#!Word']
                        self.respelling.spelling = overrideInfo['#!Word']

                elif key == '#!Sentence':
                    self.usage = [overrideInfo[key]] + self.usage

                elif key == '#!Examples':
                    self.examples = overrideInfo[key]

                else:
                    self.definitions.append("{}: {}".format(key, overrideInfo[key]))

            # Process #!Source info lines
            if '#!Source' in overrideInfo.keys():
                altSource = overrideInfo['#!Source']
            else:
                altSource = source

            if self.source == DICT_UNICODE_EMPTY_STR:
                self.source = altSource
            else:
                self.source = self.source + ';' + altSource

            # Process definitions
            # Remove duplicate definitions
            for override in overrideDefinitions:
                
                # Handle overrides that are marked special by the application using a prefix e.g. *
                override_text = re.sub(r'(^[^\(a-zA-Z0-9]|[\. ]+$)', DICT_UNICODE_EMPTY_STR, override, flags=re.IGNORECASE)
                coutput.print_watcher('override')
                coutput.print_watcher('override_text')

                for definition in self.definitions:
                    definition_text = re.sub(r'(^[^\(a-zA-Z0-9]|[\. ]+$)', DICT_UNICODE_EMPTY_STR, definition, flags=re.IGNORECASE)
                    coutput.print_watcher('definition')
                    coutput.print_watcher('definition_text')
                    if definition_text == override_text:
                        self.definitions.remove(definition)
                        coutput.print_debug("Removed duplicate definition")
            
            # Override definitions
            self.definitions = overrideDefinitions + self.definitions


    def set_offline_pronunciation(self, pron_url, word_form, word_spelling, file_name):        
        default_url = "[Offline Dictionary Pronunciation]"
        assign_url = coutput.coalesce(pron_url, default_url)

        if self.pronunciation is None:
            self.pronunciation = WordPronunciation(assign_url)
            self.pronunciation.form = word_form
            self.pronunciation.spelling = word_spelling
        
        self.pronunciation.audio_file = file_name


    def override_pronunciation(self, word_form, word_spelling, file_name):
        default_url = "[Dictionary Pronunciation Override]"

        if self.pronunciation is None:
            self.pronunciation = WordPronunciation(default_url)
        else:
            #self.pronunciation.audio_url = default_url
            pass

        self.pronunciation.form = word_form
        self.pronunciation.spelling = word_spelling      
        self.pronunciation.audio_file = file_name


    def generate_override(self):
        """
        #!Source: <Name of source>
        #!Respelling: <Respelling>
        #!AudioURL: <URL of pronunciation audio>
        #!Etymology: <Language of origin>
        #!Sentence: <Sentence>
        #!Note: <Note>
        #!Meta: <Metadata>
        (<Part of speech>) <Definition>
        """

        override = []

        if self.source != DICT_UNICODE_EMPTY_STR:
            override.append("#!Source: " + self.source)
        if self.respelling is not None:
            override.append("#!Respelling: " + self.respelling.text)
        if self.pronunciation is not None:
            override.append("#!AudioURL: " + self.pronunciation.audio_url)
        if self.etymology != DICT_UNICODE_EMPTY_STR:
            override.append("#!Etymology: " + self.etymology)

        override = override + self.definitions

        return coutput.multiline_text(override)


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
        self.entry_extension = DICT_UNICODE_EMPTY_STR
        self.audio_extension = DICT_UNICODE_EMPTY_STR
        self.illustration_extension = DICT_UNICODE_EMPTY_STR
        self.api_key = DICT_UNICODE_EMPTY_STR
        self.parser = DICT_UNICODE_EMPTY_STR
        self.pronunciation_guide = []
        self.element_match_patterns = {}
        self.entry_match_patterns = {}


    def is_required_element(self, element):

        isRequiredElement = False
        
        # Search for element/tag name
        for elementName in list(self.element_match_patterns.keys()):
            if element.name == elementName:
                
                # Search for element/tag attribute
                for elementAttr in self.element_match_patterns[elementName]:
                    if element.has_attr(elementAttr):

                        # Search for element/tag value
                        elementValList = []
                        if isinstance(element[elementAttr], str):
                            elementValList.append(element[elementAttr])
                        elif type(element[elementAttr]) is list:
                            elementValList = elementValList + element[elementAttr]

                        for elementVal in elementValList:
                            if self.element_match_patterns[elementName][elementAttr].match(elementVal):
                                isRequiredElement = True
                                return isRequiredElement

        return isRequiredElement


    def is_entry_element(self, element):

        isEntryElement = False
        
        # Search for element/tag name
        for elementName in list(self.entry_match_patterns.keys()):
            if element.name == elementName:
                
                # Search for element/tag attribute
                for elementAttr in self.entry_match_patterns[elementName]:
                    if element.has_attr(elementAttr):

                        # Search for element/tag value
                        elementValList = []
                        if isinstance(element[elementAttr], str):
                            elementValList.append(element[elementAttr])
                        elif type(element[elementAttr]) is list:
                            elementValList = elementValList + element[elementAttr]

                        for elementVal in elementValList:
                            if self.entry_match_patterns[elementName][elementAttr].match(elementVal):
                                isEntryElement = True
                                return isEntryElement

        return isEntryElement


    def build_entry_url(self, key_word):

        return self.entry_url_format.format(WORD=coutput.normalize(key_word)).replace(" ", "%20")


    def build_pronunciation_guide(self):

        pronunciation_guide = []
        if self.pronunciation_guide_file != DICT_UNICODE_EMPTY_STR:
            guideFile = pkg_resources.resource_filename( __name__, self.pronunciation_guide_file)
            pronunciation_guide = cfile.read(guideFile).splitlines()

        return pronunciation_guide


    def pronunciation_key(self, respelling):

        pronunciation_key = []
        if respelling != DICT_UNICODE_EMPTY_STR:
            
            isLegend = False
            for guideEntry in self.pronunciation_guide:
                if guideEntry == DICT_UNICODE_EMPTY_STR:
                    isLegend = True

                if isLegend == False:
                    phoneme = re.search(r"\\(.*)\\", guideEntry).group(1)
                    if phoneme is not None and phoneme in respelling:
                        pronunciation_key.append(guideEntry)
                else:
                    pronunciation_key.append(guideEntry)

        return pronunciation_key


class DictionaryEntry(object):
    def __init__(self, dict_config, key_word, entry_raw_text):

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
        return url_fragment


    def build_illustration_url(self, url_fragment):
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
                    if self.key_word == infl.spelling:
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
        coutput.print_watcher('matchEntryFound')
        coutput.print_watcher('matchType')

        # If matching entry is found, populate pronunciation attributes
        if matchEntryFound:
        
            if matchType == "inflection":
                simplifiedWordEntry = SimplifiedWordEntry(matchEntries[0].source, self.key_word, matchInflection.spelling)
                simplifiedWordEntry.functional_label = coutput.coalesce(matchInflection.functional_label, matchEntries[0].functional_label)

                if matchInflection.pronunciation is not None:
                    coutput.print_watcher('matchInflection.pronunciation.audio_url')
                    simplifiedWordEntry.pronunciation = WordPronunciation(matchInflection.pronunciation.audio_url)
                    simplifiedWordEntry.pronunciation.word_pronunciation = matchInflection.pronunciation.word_pronunciation
                    simplifiedWordEntry.pronunciation.form = matchInflection.pronunciation.form
                    simplifiedWordEntry.pronunciation.spelling = matchInflection.pronunciation.spelling

                    coutput.print_watcher('simplifiedWordEntry.pronunciation.word_pronunciation')
                    coutput.print_watcher('simplifiedWordEntry.pronunciation.form')
                    coutput.print_watcher('simplifiedWordEntry.pronunciation.spelling')

                if matchInflection.respelling is not None:
                    simplifiedWordEntry.respelling = WordRespelling(matchInflection.respelling.text, matchInflection.respelling.source)
                    simplifiedWordEntry.respelling.form = matchInflection.respelling.form
                    simplifiedWordEntry.respelling.spelling = matchInflection.respelling.spelling

            else:
                simplifiedWordEntry = SimplifiedWordEntry(matchEntries[0].source, self.key_word, matchEntries[0].entry_word)
                simplifiedWordEntry.functional_label = matchEntries[0].functional_label

                coutput.print_watcher('matchEntries[0].pronunciation')
                simplifiedWordEntry.pronunciation = copy.deepcopy(matchEntries[0].pronunciation)

                simplifiedWordEntry.respelling = copy.deepcopy(matchEntries[0].respelling)
               
            # Consolidate etymology and senses (definitions and examples)           
            etymologies = []
            definitions = []

            for we in matchEntries:
                
                coutput.print_watcher('we')

                if we.etymology != DICT_UNICODE_EMPTY_STR and we.etymology not in etymologies:
                    etymologies.append(we.etymology)

                flText = DICT_UNICODE_EMPTY_STR
                if we.functional_label != DICT_UNICODE_EMPTY_STR:
                    flText = "({0}) ".format(we.functional_label)

                for sense in we.senses:
                    defnText = flText + str(sense.definition)
                    if defnText not in definitions:
                        definitions.append(defnText)

                # Handle inflections within matching entries
                for infl in we.inflections:

                    flText = DICT_UNICODE_EMPTY_STR
                    if infl.functional_label != DICT_UNICODE_EMPTY_STR:
                        flText = "({0}) ".format(infl.functional_label)

                    for sense in infl.senses:
                        defnText = flText + str(sense.definition)
                        if defnText not in definitions:
                            definitions.append(defnText)
            
            simplifiedWordEntry.etymology = "; ".join(et for et in etymologies)
            simplifiedWordEntry.definitions = definitions[:]

        # Else if no matching entry is found, create a skeleton entry
        else:
            simplifiedWordEntry = SimplifiedWordEntry(DICT_UNICODE_EMPTY_STR, self.key_word, DICT_UNICODE_EMPTY_STR)

        # Set conformed entry
        self.simplified_word_entry = simplifiedWordEntry

        coutput.print_watcher('simplifiedWordEntry')


class DictionaryAssistant(object):
    def __init__(self, dict_config):

        # Set configuration attributes
        self.config = dict_config

        # Set part of speech regex patterns
        self.posRules = [
            {'form': 'plural', 'pattern': '-s', 'regexPattern': re.compile("^.*s$")},
            {'form': 'negative', 'pattern': 'non-/un-', 'regexPattern': re.compile("^(non|un).*$")},
            {'form': 'noun suffix', 'pattern': '-ness', 'regexPattern': re.compile("^.*ness$")},
            {'form': 'adjective', 'pattern': '-able/-al', 'regexPattern': re.compile("^.*(able|al)$")},
            {'form': 'adverb', 'pattern': '-ly', 'regexPattern': re.compile("^.*ly$")},
            {'form': 'past tense/adjective', 'pattern': '-ed', 'regexPattern': re.compile("^.*ed$")},
            {'form': 'progressive/participle', 'pattern': '-ing', 'regexPattern': re.compile("^.*ing$")},
            {'form': 'superlative', 'pattern': '-est', 'regexPattern': re.compile("^.*est$")},
            {'form': 'agent noun/comparative', 'pattern': '-er', 'regexPattern': re.compile("^.*er$")},
            {'form': 'agent noun', 'pattern': '-or', 'regexPattern': re.compile("^.*or$")}
        ]


    def __del__(self):
        pass


    def download_entry(self, connection_pool, key_word):

        connectionResponse = connection_pool.request('GET', self.config.build_entry_url(key_word))

        coutput.print_watcher("key_word")
        coutput.print_watcher("self.config.build_entry_url(key_word)")
        coutput.print_watcher("connectionResponse")

        # Perform unicode conversion
        coutput.print_watcher("connectionResponse.data")
        entryData = connectionResponse.data.decode('utf8')
        coutput.print_watcher("entryData")

        return entryData


    def compare_word_form(self, key_word, entry_word):

        keyWordToken = coutput.tokenize(key_word)
        entryWordToken = coutput.tokenize(entry_word)

        coutput.print_watcher('keyWordToken')
        coutput.print_watcher('entryWordToken')

        if keyWordToken != entryWordToken:
            coutput.print_warn("A different form of the word is being pronounced.")

            for posPattern in self.posRules:
                coutput.print_watcher("posPattern['form']")

                if posPattern['regexPattern'].match(keyWordToken):
                    coutput.print_tip("The {0} form ({1}) of the word is to be spelled.".format(posPattern['form'], posPattern['pattern']))
                    break;
