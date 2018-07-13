#!/usr/bin/env python
# -*- encoding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : mwonlineapi.py
# Description : Merriam Webster Online Dictionary API implementation
# Author      : Dito Manavalan
# Date        : 2018/01/11
#--------------------------------------------------------------------------------------------------

import sys
import re

from bs4 import BeautifulSoup

sys.path.insert(0, "..")
import common.rpimod.stdio.output as cout
import dictionaryapi as cdict
import mwcollegiateapi as mwdict

# Set to True to turn debug messages on
SB_ERR_DEBUG = False

################################################################
# Merriam Webster Online Dictionary
################################################################

class DictionaryConfig(mwdict.DictionaryConfig):
    def __init__(self):

        # Configuration Attributes
        self.name = u"Merriam-Webster's Online Dictionary"
        self.pronunciation_key_file = u"data/pronunciation_key_merriam-webster.txt"
        self.entry_url_format = u"https://www.merriam-webster.com/dictionary/{WORD}"
        self.audio_url_format = u"http://media.merriam-webster.com/soundc11/{FOLDER}/{CLIP}.wav"
        self.illustration_url_format = u"https://www.merriam-webster.com/art/dict/{CLIP}.htm"
        self.api_key = cdict.DICT_UNICODE_EMPTY_STR
        self.parser = u"html.parser"


    def build_entry_url(self, key_word):
        _FUNC_NAME_ = "DictionaryConfig.build_entry_url"

        return self.entry_url_format.format(WORD=key_word).replace(u" ", u"%20")


class DictionaryEntry(mwdict.DictionaryEntry):

    def set_word_entries(self):
        _FUNC_NAME_ = "DictionaryEntry.set_word_entries"

        wordEntryInitialized = False

        soup = BeautifulSoup(self.entry_raw_text, self.config.parser)
        nameFilter = re.compile(ur'(h1|h2|span|a|div)')
        classAttrFilter = re.compile(ur'(hword|fl|prs|dt|play-pron|et|in)')

        for entry in soup.find_all(nameFilter, {'class':['hword', 'fl', 'word-syllables', 'prs', 'dt', 'play-pron', 'et', 'in']}, recursive=True):
        #for entry in soup.find_all(nameFilter, classAttrFilter, recursive=True):

            DEBUG_VAR="entry.name"
            cout.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, DEBUG_VAR + " :: " + eval(DEBUG_VAR))

            DEBUG_VAR="entry['class'][0]"
            cout.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, DEBUG_VAR + " :: " + eval(DEBUG_VAR))

            cout.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, entry.get_text())

            if entry.name in ['h1', 'h2']:
                if wordEntryInitialized:
                    DEBUG_VAR="wordEntry"
                    cout.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, DEBUG_VAR + " :: " + str(eval(DEBUG_VAR)))

                    self.word_entries.append(wordEntry)
                    wordEntryInitialized = False

                elementText = entry.get_text().strip()
                wordEntry = cdict.WordEntry(self.config.name, self.key_word)
                wordEntry.entry_word = elementText
                wordEntryInitialized = True

            elif entry.name == 'span' and entry['class'][0] == 'fl':
                elementText = entry.get_text().strip()
                wordEntry.functional_label = elementText

            elif entry.name == 'span' and entry['class'][0] == 'word-syllables':
                elementText = entry.get_text().strip()
                wordEntry.word_syllables = elementText

            elif entry.name == 'a' and 'play-pron' in entry['class'] and 'hw-play-pron' in entry['class']:
                elementText = entry['data-file']
                if wordEntry.pronunciation.audio_url == cdict.DICT_UNICODE_EMPTY_STR:
                    wordEntry.pronunciation.audio_url = self.build_audio_url(elementText)
                    wordEntry.pronunciation.form = wordEntry.head_word

            elif entry.name == 'span' and entry['class'][0] == 'prs':
                elementText = entry.get_text().strip().replace('\n','').replace(' ','')
                prsPattern = re.compile(ur'\\.*\\')
                elementText = prsPattern.findall(elementText)[0]
                if wordEntry.respelling.text == cdict.DICT_UNICODE_EMPTY_STR:
                    wordEntry.respelling.text = elementText

            elif entry.name == 'div' and entry['class'][0] == 'et':
                originText = entry.get_text().strip()
                elementText = re.sub(ur'[ ]+—[ ]+more.*', u'', originText, flags=re.UNICODE)
                wordEntry.etymology = elementText

            elif entry.name == 'span' and entry['class'][0] == 'dt':

                examples = entry.find_all('ul') 
                [x.extract() for x in entry.findAll(['ul'])]

                elementText = entry.get_text().strip()
                elementText = re.sub(ur'[ ]+—[ ]+(compare).*', u'', elementText, flags=re.UNICODE)
                elementText = re.sub(ur'^[ ]*:[ ]*', u'', elementText, flags=re.UNICODE)
                elementText = re.sub(ur'[ ]*:[ ]*', u'; ', elementText, flags=re.UNICODE)
                elementText = re.sub(ur'[\n ]+', u' ', elementText, flags=re.UNICODE)
                wordSense = cdict.WordSense(elementText)

                for ul in examples:
                    elementText = ul.get_text().strip()
                    wordSense.examples.append(elementText)

                DEBUG_VAR="wordSense"
                cout.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, DEBUG_VAR + " :: " + str(eval(DEBUG_VAR)))

                wordEntry.senses.append(wordSense)
                wordSense = None

            elif entry.name == 'span' and entry['class'][0] == 'in':

                ilElementText = cdict.DICT_UNICODE_EMPTY_STR
                ifElementText = cdict.DICT_UNICODE_EMPTY_STR
                prElementText = cdict.DICT_UNICODE_EMPTY_STR
                prsElementText = cdict.DICT_UNICODE_EMPTY_STR

                for inflection in entry.find_all('span', {'class':['il', 'if', 'prs', 'pr']}, recursive=True):
                    if inflection['class'][0] == 'il':
                        ilElementText = inflection.get_text().strip()

                    elif inflection['class'][0] == 'if':
                        ifElementText = inflection.get_text().strip()
                        
                    elif inflection['class'][0] == 'prs':

                        for pr in inflection.find_all('a', {'class':['play-pron']}, recursive=True, limit=1):
                            prElementText = pr['data-file']

                        elementText = inflection.get_text().strip()
                        prsPattern = re.compile(ur'\\.*\\')
                        elementText = prsPattern.findall(elementText)[0]
                        if prsElementText == cdict.DICT_UNICODE_EMPTY_STR:
                            prsElementText = elementText

                wordInflection = cdict.WordInflection(ilElementText)
                wordInflection.form = ifElementText
                wordInflection.pronunciation_audio_url = self.build_audio_url(prElementText)
                wordInflection.pronunciation_respelling = prsElementText
                wordEntry.inflections.append(wordInflection)

        if wordEntryInitialized:
            DEBUG_VAR="wordEntry"
            cout.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, DEBUG_VAR + " :: " + str(eval(DEBUG_VAR)))

            self.word_entries.append(wordEntry)

