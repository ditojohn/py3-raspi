#!/usr/bin/env python
# -*- encoding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : mwcollegiateapi.py
# Description : Merriam Webster Collegiate Dictionary API implementation
# Author      : Dito Manavalan
# Date        : 2018/01/11
#--------------------------------------------------------------------------------------------------

import sys
import re

from bs4 import BeautifulSoup

sys.path.insert(0, "..")
import common.rpimod.stdio.output as coutput
import dictionaryapi as cdict


# Set to True to turn debug messages on
#MOD_ERR_DEBUG = True
MOD_ERR_DEBUG = False

################################################################
# Merriam Webster Collegiate Dictionary
################################################################

class DictionaryConfig(cdict.DictionaryConfig):
    def __init__(self):

        # Configuration Attributes
        self.name = u"Merriam-Webster's Collegiate Dictionary"
        self.pronunciation_guide_file = u"data/mwcollegiatepronguide.txt"
        self.entry_url_format = u"http://www.dictionaryapi.com/api/v1/references/collegiate/xml/{WORD}?key={KEY}"
        self.audio_url_format = u"http://media.merriam-webster.com/soundc11/{FOLDER}/{CLIP}"
        self.illustration_url_format = u"https://www.merriam-webster.com/art/dict/{CLIP}.htm"
        self.entry_extension = u".xml"
        self.audio_extension = u".wav"
        self.illustration_extension = u".bmp"
        self.api_key = u"cbbd4001-c94d-493a-ac94-7268a7e41f6f"
        self.parser = u"lxml"
        self.pronunciation_guide = self.build_pronunciation_guide()
        self.element_match_patterns = {}


    def build_entry_url(self, key_word):
        _FUNC_NAME_ = "DictionaryConfig.build_entry_url"

        coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'key_word')
        coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'coutput.normalize(key_word)')

        #return self.entry_url_format.format(WORD=key_word, KEY=self.api_key).replace(u" ", u"%20")
        return self.entry_url_format.format(WORD=coutput.normalize(key_word), KEY=self.api_key).replace(u" ", u"%20")


class DictionaryEntry(cdict.DictionaryEntry):

    def build_audio_url(self, url_fragment):
        _FUNC_NAME_ = "DictionaryEntry.build_audio_url"

        if url_fragment == cdict.DICT_UNICODE_EMPTY_STR:
            return url_fragment
        else:
            number_prefix_match = re.search(ur'^([0-9]+)', url_fragment)
            special_prefix_match = re.search(ur'^(gg|bix)', url_fragment)
            if number_prefix_match:
                prefix = u"number"
            elif special_prefix_match:
                prefix = special_prefix_match.group(1)
            else:
                prefix = url_fragment[0]

            # Check for missing extension in audio file name
            if not url_fragment.endswith(self.config.audio_extension):
                url_fragment = url_fragment + self.config.audio_extension
            
            return self.config.audio_url_format.format(FOLDER=prefix, CLIP=url_fragment)


    def build_illustration_url(self, url_fragment):
        _FUNC_NAME_ = "DictionaryEntry.build_illustration_url"

        if url_fragment == cdict.DICT_UNICODE_EMPTY_STR:
            return url_fragment
        else:
            # Check for extension in illustration
            if url_fragment.endswith(self.config.illustration_extension):
                url_fragment = url_fragment[:-1*len(self.config.illustration_extension)]

            return self.config.illustration_url_format.format(CLIP=url_fragment)


    def build_pronunciation(self, element, word_form):
        # Accepts <sound> element as input
        _FUNC_NAME_ = "DictionaryEntry.build_pronunciation"
        
        pronunciation = None

        wavElementText = cdict.DICT_UNICODE_EMPTY_STR
        wprElementText = cdict.DICT_UNICODE_EMPTY_STR

        subElements = element.find_all(['wav', 'wpr'])
        for subElement in subElements:
            subElementText = subElement.get_text().strip()

            if subElement.name == 'wav':
                subElementText = self.build_audio_url(subElementText)
                wavElementText = subElementText
                coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'wavElementText')

            elif subElement.name == 'wpr':
                wprElementText = subElementText
                coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'wprElementText')

        if wavElementText != cdict.DICT_UNICODE_EMPTY_STR:
            pronunciation = cdict.WordPronunciation(wavElementText)        
            
            if wprElementText != cdict.DICT_UNICODE_EMPTY_STR:
                pronunciation.word_pronunciation = wprElementText
            
            pronunciation.form = word_form
            pronunciation.spelling = word_form.replace('*', '')

        return pronunciation


    def build_respelling(self, element, word_form):
        # Accepts <pr> element as input
        
        elementText = element.get_text().strip()
        elementText = u"\\{0}\\".format(elementText)
        respelling = cdict.WordRespelling(elementText, self.config.name)
        respelling.form = word_form
        respelling.spelling = word_form.replace('*', '')

        return respelling


    def build_illustrations(self, element, entry_word):
        # Accepts <art> element as input
        
        illustrations = []

        bmpElementText = cdict.DICT_UNICODE_EMPTY_STR
        capElementText = cdict.DICT_UNICODE_EMPTY_STR

        subElements = element.find_all(['bmp', 'cap'])
        for subElement in subElements:
            subElementText = subElement.get_text().strip()

            if subElement.name == 'bmp':
                subElementText = self.build_illustration_url(subElementText)
                bmpElementText = subElementText

            elif subElement.name == 'cap':
                capElementText = subElementText

        if bmpElementText != cdict.DICT_UNICODE_EMPTY_STR:
            il = cdict.WordIllustration(bmpElementText)
            il.caption = capElementText
            il.form = entry_word
            il.spelling = entry_word.replace('*', '')
            illustrations.append(il)

        return illustrations


    def build_senses(self, element):
        # Accepts <def> or <ct> elements as input
        _FUNC_NAME_ = "DictionaryEntry.build_senses"

        """
        <!ELEMENT def (vt?, date?, sl*, sense, ss?, us?)+ >
        <!ELEMENT sense (sn?,
                        (sp, sp_alt?, sp_ipa?, sp_wod?, sound?)?,
                        svr?, sin*, slb*, set?, ssl*, dt*,
                        (sd, sin?,
                          (sp, sp_alt?, sp_ipa?, sp_wod?, sound?)?,
                        slb*, ssl*, dt+)?)>
        """
        
        senses = []
        
        if element.name == 'def':
            dateElementText = cdict.DICT_UNICODE_EMPTY_STR
            dtElementText = cdict.DICT_UNICODE_EMPTY_STR

            # Filter and exclude unwanted subelements from main element
            [x.extract() for x in element.findAll(['vi', 'wsgram', 'dx', 'snote', 'sxn'])]

            for subElement in element.find_all(['date']):
                dateElementText = subElement.get_text().strip()

            subElements = element.find_all(['dt'])
            for subElement in subElements:
                subElementText = subElement.get_text().strip()

                subElementText = re.sub(ur'called also', u'- called also', subElementText, flags=re.UNICODE)
                subElementText = re.sub(ur'[ ]+—[ ]+(compare).*', u'', subElementText, flags=re.UNICODE)
                subElementText = re.sub(ur'^[ ]*:[ ]*', u'', subElementText, flags=re.UNICODE)
                subElementText = re.sub(ur'[ ]*:[ ]*', u'; ', subElementText, flags=re.UNICODE)
                subElementText = re.sub(ur'[\n ]+', u' ', subElementText, flags=re.UNICODE)
                dtElementText = subElementText

                if dtElementText != cdict.DICT_UNICODE_EMPTY_STR:
                    ws = cdict.WordSense(dtElementText)
                    ws.date = dateElementText
                    senses.append(ws)
        
        elif element.name == 'ct':
            ws = cdict.WordSense(element.get_text().strip())
            senses.append(ws)

        return senses


    def build_cross_entries(self, element, entry_word):
        # Accepts <cx> element as input and returns an inflection
        _FUNC_NAME_ = "DictionaryEntry.build_cross_entries"
        
        wordInfl = cdict.WordInflection(entry_word)
        wordInfl.spelling = entry_word.replace('*', '')

        for subelement in element.find_all(['cl', 'ct']):
            
            if subelement.name == 'cl':
                subElementText = subelement.get_text().strip()
                subElementText = re.sub(ur' of$', u'', subElementText, flags=re.UNICODE)
                wordInfl.functional_label = subElementText
            elif subelement.name == 'ct':
                wordInfl.senses.extend(self.build_senses(subelement))
        
        coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'wordInfl')
        return wordInfl


    def set_word_entries(self):
        _FUNC_NAME_ = "DictionaryEntry.set_word_entries"

        soup = BeautifulSoup(self.entry_raw_text, self.config.parser)
        nameFilter = re.compile(ur'(hw|fl|pr|et|sound|def|cx|art)')

        for entry in soup.find_all('entry'):
            """
            <!ELEMENT entry
              (((subj?, art?, formula?, table?),
                    hw,
                    (pr?, pr_alt?, pr_ipa?, pr_wod?, sound?)*,
                    (ahw, (pr, pr_alt?, pr_ipa?, pr_wod?, sound?)?)*,
                    vr?),
                 (fl?, in*, lb*, ((cx, (ss | us)*) | et)*, sl*),
                 (dx | def)*,
                 (list? |
                   (uro*, dro*, ((pl, pt, sa?) |
                                  (note) |
                                  quote+)*)))>
            """

            # Capture and exclude miscellaneous entries from main entry:
            # * inflections <in>
            # * defined run-on entries <dro>
            # * undefined run-on entries <uro>
            # * variants <vr>

            miscElements = entry.find_all(['in', 'dro', 'uro', 'vr']) 
            [x.extract() for x in entry.findAll(['in', 'dro', 'uro', 'vr'])]

            coutput.print_debug(MOD_ERR_DEBUG, _FUNC_NAME_, "Process all <ew> elements")
            for element in entry.find_all('ew'):
                
                elementText = element.get_text().strip()
                wordEntry = cdict.WordEntry(self.config.name, elementText)

            for element in entry.find_all(nameFilter):

                elementText = element.get_text().strip()
                coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'element.name')
                coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'elementText')

                if element.name == 'hw':
                    coutput.print_debug(MOD_ERR_DEBUG, _FUNC_NAME_, "Process <hw> element")
                    wordEntry.head_word = elementText

                elif element.name == 'fl':
                    coutput.print_debug(MOD_ERR_DEBUG, _FUNC_NAME_, "Process <fl> element")
                    wordEntry.functional_label = elementText

                elif element.name == 'et':
                    coutput.print_debug(MOD_ERR_DEBUG, _FUNC_NAME_, "Process <et> element")
                    wordEntry.etymology = elementText

                elif element.name == 'pr':
                    wordEntry.respelling = self.build_respelling(element, wordEntry.entry_word)

                elif element.name == 'sound':
                    wordEntry.pronunciation = self.build_pronunciation(element, wordEntry.entry_word)

                elif element.name == 'art':
                    wordEntry.illustrations.extend(self.build_illustrations(element, wordEntry.entry_word))

                elif element.name == 'def':
                    coutput.print_debug(MOD_ERR_DEBUG, _FUNC_NAME_, "Process <def> element")
                    wordEntry.senses.extend(self.build_senses(element))

                elif element.name == 'cx':
                    # Process cross-entry <cx> elements as inflections
                    wordEntry.inflections.append(self.build_cross_entries(element, wordEntry.entry_word))


            # Process previously captured misc. elements from main entry as inflections
            for miscElement in miscElements:

                for element in miscElement.find_all(['if', 'ure', 'drp', 'va']):

                    elementText = element.get_text().strip()
                    winf = cdict.WordInflection(elementText)
                    winf.spelling = elementText.replace('*', '')

                    if element.name == 'ure':
                        winf.functional_label = u"undefined run-on entry"
                    elif element.name == 'drp':
                        winf.functional_label = u"defined run-on phrase"
                    elif element.name == 'va':
                        winf.functional_label = u"variant form"

                for element in miscElement.find_all(['il', 'sound', 'pr', 'def']):

                    DEBUG_VAR = u"element.name"
                    coutput.print_debug(MOD_ERR_DEBUG, _FUNC_NAME_, u"{0} :: {1}".format(DEBUG_VAR, eval(DEBUG_VAR)))

                    elementText = element.get_text().strip()
                    DEBUG_VAR = u"elementText"
                    coutput.print_debug(MOD_ERR_DEBUG, _FUNC_NAME_, u"{0} :: {1}".format(DEBUG_VAR, eval(DEBUG_VAR)))

                    if element.name == 'il':
                        winf.functional_label = elementText

                    elif element.name == 'pr':
                        winf.respelling = self.build_respelling(element, winf.form)

                    elif element.name == 'sound':
                        winf.pronunciation = self.build_pronunciation(element, winf.form)

                    elif element.name == 'def':
                        winf.senses.extend(self.build_senses(element))

                wordEntry.inflections.append(winf)

            coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'wordEntry')
            self.word_entries.append(wordEntry)
