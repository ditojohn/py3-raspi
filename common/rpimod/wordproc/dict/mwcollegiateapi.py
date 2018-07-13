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
import common.rpimod.stdio.output as cout
import dictionaryapi as cdict


# Set to True to turn debug messages on
SB_ERR_DEBUG = False

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
        self.api_key = u"cbbd4001-c94d-493a-ac94-7268a7e41f6f"
        self.parser = u"lxml"
        self.pronunciation_guide = self.build_pronunciation_guide()


    def build_entry_url(self, key_word):
        _FUNC_NAME_ = "DictionaryConfig.build_entry_url"

        return self.entry_url_format.format(WORD=key_word, KEY=self.api_key).replace(u" ", u"%20")


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
            
            return self.config.audio_url_format.format(FOLDER=prefix, CLIP=url_fragment)


    def build_illustration_url(self, url_fragment):
        _FUNC_NAME_ = "DictionaryEntry.build_illustration_url"

        if url_fragment == cdict.DICT_UNICODE_EMPTY_STR:
            return url_fragment
        else:
            urlFragment = re.sub(ur'\.(bmp)', '', url_fragment)
            return self.config.illustration_url_format.format(CLIP=urlFragment)


    def build_pronunciation(self, element, entry_word):
        # Accepts <sound> element as input
        
        pronunciation = None

        wavElementText = cdict.DICT_UNICODE_EMPTY_STR
        wprElementText = cdict.DICT_UNICODE_EMPTY_STR

        subElements = element.find_all(['wav', 'wpr'])
        for subElement in subElements:
            subElementText = subElement.get_text().strip()

            if subElement.name == 'wav':
                subElementText = self.build_audio_url(subElementText)
                wavElementText = subElementText

            elif subElement.name == 'wpr':
                wprElementText = subElementText

        if wavElementText != cdict.DICT_UNICODE_EMPTY_STR:
            pronunciation = cdict.WordPronunciation(wavElementText)
            pronunciation.word_pronunciation = subElementText
            pronunciation.form = entry_word

        return pronunciation


    def build_respelling(self, element, entry_word):
        # Accepts <pr> element as input
        
        elementText = element.get_text().strip()
        elementText = u"\\{0}\\".format(elementText)
        respelling = cdict.WordRespelling(elementText, self.config.name)
        respelling.form = entry_word

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
                subElementText = re.sub(ur"\.bmp", ur"", subElementText)
                subElementText = self.build_illustration_url(subElementText)
                bmpElementText = subElementText

            elif subElement.name == 'cap':
                capElementText = subElementText

        if bmpElementText != cdict.DICT_UNICODE_EMPTY_STR:
            il = cdict.WordIllustration(bmpElementText)
            il.caption = capElementText
            il.form = entry_word
            illustrations.append(il)

        return illustrations


    def build_senses(self, element):
        # Accepts <def> element as input
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
        dateElementText = cdict.DICT_UNICODE_EMPTY_STR
        dtElementText = cdict.DICT_UNICODE_EMPTY_STR

        # Filter and exclude unwanted subelements from main element
        [x.extract() for x in element.findAll(['vi', 'wsgram', 'dx', 'snote', 'un', 'sxn'])]

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

        return senses


    def set_word_entries(self):
        _FUNC_NAME_ = "DictionaryEntry.set_word_entries"

        soup = BeautifulSoup(self.entry_raw_text, self.config.parser)
        nameFilter = re.compile(ur'(hw|fl|pr|et|sound|def|art)')

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

            miscElements = entry.find_all(['in', 'dro', 'uro']) 
            [x.extract() for x in entry.findAll(['in', 'dro', 'uro'])]

            for element in entry.find_all('ew'):
                
                elementText = element.get_text().strip()
                wordEntry = cdict.WordEntry(self.config.name, elementText)

            for element in entry.find_all(nameFilter):

                DEBUG_VAR = u"element.name"
                cout.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, u"{0} :: {1}".format(DEBUG_VAR, eval(DEBUG_VAR)))

                elementText = element.get_text().strip()
                DEBUG_VAR = u"elementText"
                cout.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, u"{0} :: {1}".format(DEBUG_VAR, eval(DEBUG_VAR)))

                if element.name == 'hw':
                    wordEntry.head_word = elementText

                elif element.name == 'fl':
                    wordEntry.functional_label = elementText

                elif element.name == 'et':
                    wordEntry.etymology = elementText

                elif element.name == 'pr':
                    wordEntry.respelling = self.build_respelling(element, wordEntry.entry_word)

                elif element.name == 'sound':
                    wordEntry.pronunciation = self.build_pronunciation(element, wordEntry.entry_word)

                elif element.name == 'art':
                    wordEntry.illustrations.extend(self.build_illustrations(element, wordEntry.entry_word))

                elif element.name == 'def':
                    wordEntry.senses.extend(self.build_senses(element))


            # Process previously captured misc. elements from main entry as inflections
            for miscElement in miscElements:

                for element in miscElement.find_all(['if', 'ure', 'drp']):

                    elementText = element.get_text().strip()
                    winf = cdict.WordInflection(elementText)

                    if element.name == 'ure':
                        winf.functional_label = u"undefined run-on entry"
                    elif element.name == 'drp':
                        winf.functional_label = u"defined run-on phrase"

                for element in miscElement.find_all(['il', 'sound', 'pr', 'def']):

                    DEBUG_VAR = u"element.name"
                    cout.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, u"{0} :: {1}".format(DEBUG_VAR, eval(DEBUG_VAR)))

                    elementText = element.get_text().strip()
                    DEBUG_VAR = u"elementText"
                    cout.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, u"{0} :: {1}".format(DEBUG_VAR, eval(DEBUG_VAR)))

                    if element.name == 'il':
                        winf.functional_label = elementText

                    elif element.name == 'pr':
                        winf.respelling = self.build_respelling(element, winf.form)

                    elif element.name == 'sound':
                        winf.pronunciation = self.build_pronunciation(element, winf.form)

                    elif element.name == 'def':
                        winf.senses.extend(self.build_senses(element))

                wordEntry.inflections.append(winf)

            self.word_entries.append(wordEntry)
