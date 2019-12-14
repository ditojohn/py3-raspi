#!/usr/bin/env python
# -*- encoding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : mwonlineapi.py
# Description : Merriam Webster Online Dictionary API implementation
# Author      : Dito Manavalan
# Date        : 2019/03/02
#--------------------------------------------------------------------------------------------------

import sys
import re

from bs4 import BeautifulSoup

sys.path.insert(0, "..")
import common.rpimod.stdio.output as coutput
import dictionaryapi as cdict
import mwcollegiateapi as cparentdict

# Set to True to turn debug messages on
#MOD_ERR_DEBUG = True
MOD_ERR_DEBUG = False

################################################################
# Merriam Webster Online Dictionary
################################################################

class DictionaryConfig(cparentdict.DictionaryConfig):
    def __init__(self):

        # Configuration Attributes
        self.name = u"Merriam-Webster's Online Dictionary"
        self.pronunciation_guide_file = u"data/mwcollegiatepronguide.txt"
        self.entry_url_format = u"http://www.merriam-webster.com/dictionary/{WORD}"
        self.audio_url_format = u"http://media.merriam-webster.com/soundc11/{FOLDER}/{CLIP}"
        self.illustration_url_format = u"https://www.merriam-webster.com/art/dict/{CLIP}.htm"
        self.entry_extension = u".html"
        self.audio_extension = u".wav"
        self.illustration_extension = u".bmp"
        self.api_key = cdict.DICT_UNICODE_EMPTY_STR
        self.parser = u"html.parser"
        self.pronunciation_guide = self.build_pronunciation_guide()

        """
        Dictionary Entry (container): <div id="dictionary-entry-1"> or <div id="medical-entry-1"> or <div id="legal-entry-1">
        -- maps to wordEntry

            Head Word: <h1 class="hword"> or <p class="hword">
            -- maps to wordEntry.entry_word

            Functional Label: <span class="fl"> or <span class='lb'>
            -- maps to wordEntry.functional_label

            Etymology: <p class="et">
            -- maps to wordEntry.etymology

            Word Syllables: <span class="word-syllables">
            -- maps to wordEntry.word_syllables

            Pronunciation: <a class="play-pron">
            -- maps to wordEntry.pronunciation

            Respelling: <span class="prs">
            -- maps to wordEntry.respelling

            Senses (container): <div class="vg">

            Inflection: <span class="vg-ins">
            -- maps to wordEntry.inflections

                Inflection Form: <span class="if">
                -- maps to wordEntry.inflections.form

                Inflection Functional Label: <span class="il">
                -- maps to wordEntry.inflections.functional_label
        """
        self.element_match_patterns = {
            
            u'div' : {
                u'class' : re.compile(ur'(entry-header|entry-attr)'),
                u'id' : re.compile(ur'dictionary-entry-.*|medical-entry-.*|legal-entry-.*|etymology-anchor|first-known-anchor')
            }
        }

        self.entry_match_patterns = {
            
            u'div' : {
                u'id' : re.compile(ur'dictionary-entry-.*|medical-entry-.*|legal-entry-.*')
            }
        }


class DictionaryEntry(cparentdict.DictionaryEntry):

    def build_pronunciation(self, element, word_form):
        # Accepts <a class="play-pron"> element as input
        _FUNC_NAME_ = "DictionaryEntry.build_pronunciation"
        
        url_fragment = element['data-file'].strip()
        url_fragment = self.build_audio_url(url_fragment)

        pronunciation = cdict.WordPronunciation(url_fragment)
        pronunciation.form = word_form
        pronunciation.spelling = word_form.replace(u'·​', u'')

        return pronunciation


    def build_respelling(self, element, word_form):
        # Accepts <span class="prs"> element as input
        _FUNC_NAME_ = "DictionaryEntry.build_respelling"

        elementText = element.get_text().strip().replace('\n','').replace(' ','')
        
        prsPattern = re.compile(ur'\\.*\\')
        prsElements = prsPattern.findall(elementText)

        if prsElements is not None and len(prsElements) > 0:
            prsElementText = prsElements[0]
            prsElementText = prsElementText.strip()

            respelling = cdict.WordRespelling(prsElementText, self.config.name)
            respelling.form = word_form
            respelling.spelling = word_form.replace(u'·​', u'')
        else:
            respelling = None

        return respelling


    def build_senses(self, element, dateText):
        _FUNC_NAME_ = "DictionaryEntry.build_senses"

        # Accepts <div class="vg"> element as input
        """
        Senses (container): <div class="vg">

            Sense (container): <div class="sense">
            -- maps to wordEntry.senses

                Definition (container): <span class="dt ">
                    -- maps to wordEntry.senses.definition

                    Examples: <span class="ex-sent sents">
                    -- maps to wordEntry.senses.examples
        """
        
        senses = []
        
        for sense in element.find_all('div', class_="sense"):
            slElementText = cdict.DICT_UNICODE_EMPTY_STR
            dtElementText = cdict.DICT_UNICODE_EMPTY_STR
            exElementText = cdict.DICT_UNICODE_EMPTY_STR

            for subElement in sense.find_all('span', class_="sl"):
                subElementText = subElement.get_text().strip()

                slElementText = subElementText

            # Process <span class="dt"> elements
            # This includes <span class="dtText"> and <span class="un"> elements
            for subElement in sense.find_all('span', class_="dt"):
                # Hold example sentences for later
                examples = subElement.find_all('span', class_="ex-sent") 
                [x.extract() for x in subElement.find_all('span', class_="ex-sent")]

                subElementText = subElement.get_text().strip()
                subElementText = re.sub(ur'called also', u'- called also', subElementText, flags=re.UNICODE)
                subElementText = re.sub(ur'[ ]+—[ ]+(compare).*', u'', subElementText, flags=re.UNICODE)
                subElementText = re.sub(ur'^[ ]*:[ ]*', u'', subElementText, flags=re.UNICODE)
                subElementText = re.sub(ur'[ ]*:[ ]*', u'; ', subElementText, flags=re.UNICODE)
                subElementText = re.sub(ur'[\n ]+', u' ', subElementText, flags=re.UNICODE)
                if slElementText != cdict.DICT_UNICODE_EMPTY_STR:
                    subElementText = slElementText + u': ' + subElementText

                dtElementText = subElementText
                ws = cdict.WordSense(dtElementText)
                ws.date = dateText

            for subElement in examples:
                # Remove author and source references
                [x.extract() for x in subElement.find_all('span', class_="auth")]
                [x.extract() for x in subElement.find_all('span', class_="source")]

                subElementText = subElement.get_text().strip()
                subElementText = re.sub(ur'[\n ]+', u' ', subElementText, flags=re.UNICODE)

                exElementText = subElementText
                if exElementText != cdict.DICT_UNICODE_EMPTY_STR:
                    ws.examples.append(exElementText)

            senses.append(ws)

        return senses


    def set_word_entries(self):
        _FUNC_NAME_ = "DictionaryEntry.set_word_entries"

        soup = BeautifulSoup(self.entry_raw_text, self.config.parser)
        currEntryWord = cdict.DICT_UNICODE_EMPTY_STR
        currFuncLabel = cdict.DICT_UNICODE_EMPTY_STR
        currEtymology = cdict.DICT_UNICODE_EMPTY_STR
        currOrigin = cdict.DICT_UNICODE_EMPTY_STR
        currWordSyllables = cdict.DICT_UNICODE_EMPTY_STR
        currPronunciation = None
        currRespelling = None

        for entry in soup.find_all(self.config.is_required_element):
            #coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'entry')

            if entry.name == u'div' and entry.has_attr(u'id') and re.compile(ur'etymology-anchor').match(entry.attrs[u'id']):

                # Process etymology: <p class="function-label"> and <p class="et">
                currEtymology = cdict.DICT_UNICODE_EMPTY_STR
                for element in entry.find_all(u'p', class_=re.compile(ur'function-label|et')):
                    if u'function-label' in element['class']:
                        elementText = element.get_text().strip()
                        elementText = re.sub(ur'[ ]*\([0-9]+\)[ ]*', u'', elementText, flags=re.UNICODE)
                        elementText = u'(' + elementText.strip() + u') '

                        if currEtymology == cdict.DICT_UNICODE_EMPTY_STR:
                            currEtymology = elementText
                        else:
                            currEtymology = currEtymology + u'; ' + elementText

                    elif u'et' in element['class']:
                        elementText = element.get_text().strip()

                        if currEtymology == cdict.DICT_UNICODE_EMPTY_STR:
                            currEtymology = elementText
                        else:
                            currEtymology = currEtymology + elementText

            elif entry.name == u'div' and entry.has_attr(u'id') and re.compile(ur'first-known-anchor').match(entry.attrs[u'id']):

                # Process origin: <p class="function-label"> and <p class="ety-sl">
                currEtymology = cdict.DICT_UNICODE_EMPTY_STR
                for element in entry.find_all(u'p', class_=re.compile(ur'function-label|ety-sl')):
                    if u'function-label' in element['class']:
                        elementText = element.get_text().strip()
                        elementText = re.sub(ur'[ ]*\([0-9]+\)[ ]*', u'', elementText, flags=re.UNICODE)
                        elementText = u'(' + elementText.strip() + u') '

                        if currOrigin == cdict.DICT_UNICODE_EMPTY_STR:
                            currOrigin = elementText
                        else:
                            currOrigin = currOrigin + u'; ' + elementText

                    elif u'ety-sl' in element['class']:
                        elementText = element.get_text().strip()

                        if currOrigin == cdict.DICT_UNICODE_EMPTY_STR:
                            currOrigin = elementText
                        else:
                            currOrigin = currOrigin + elementText


        for entry in soup.find_all(self.config.is_required_element):

            if entry.name == u'div' and entry.has_attr(u'class') and any(re.compile(ur'entry-.*').match(x) for x in entry.attrs[u'class']):
                coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'entry')

                # Process head word: <h1 class="hword"> or <p class="hword">
                for element in entry.find_all(class_="hword"):
                    elementText = element.get_text().strip()
                    currEntryWord = elementText
                    #coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'currEntryWord')

                # Process functional label: <span class="fl">
                for element in entry.find_all('span', class_="fl"):
                    elementText = element.get_text().strip()
                    elementText = re.sub(ur'[ ]*\(.*$', u'', elementText, flags=re.UNICODE)
                    currFuncLabel = elementText
                    #coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'currFuncLabel')

                # Process functional label: <span class="lb">
                for element in entry.find_all('span', class_="lb"):
                    coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'element')
                    elementText = element.get_text().strip()
                    elementText = currFuncLabel + u', ' + elementText
                    currFuncLabel = elementText.strip()
                    #coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'currFuncLabel')

                # Process word syllables: <span class="word-syllables">
                for element in entry.find_all('span', class_="word-syllables"):
                    elementText = element.get_text().strip()
                    currWordSyllables = elementText
                    #coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'currWordSyllables')

                # Process pronunciation: <a class="play-pron">
                for element in entry.find_all('a', class_="play-pron"):
                    currPronunciation = self.build_pronunciation(element, coutput.coalesce(currWordSyllables, currEntryWord))
                    #coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'currPronunciation')

                # Process respellings: <span class="prs">
                for element in entry.find_all('span', class_="prs"):
                    currRespelling = self.build_respelling(element, coutput.coalesce(currWordSyllables, currEntryWord))
                    #coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'currRespelling')
            
            # Process dictionary entry (container): <div id="dictionary-entry-1"> or <div id="medical-entry-1"> or <div id="legal-entry-1">
            elif self.config.is_entry_element(entry):
                coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'entry')

                wordEntry = cdict.WordEntry(self.config.name, self.key_word)
                wordEntry.entry_word = currEntryWord
                wordEntry.functional_label = currFuncLabel
                wordEntry.etymology = currEtymology
                wordEntry.word_syllables = currWordSyllables
                wordEntry.pronunciation = currPronunciation
                wordEntry.respelling = currRespelling

                # Process word senses: <div class="vg">
                for element in entry.find_all('div', class_="vg"):
                    wordEntry.senses.extend(self.build_senses(element, currOrigin))

                self.word_entries.append(wordEntry)

        coutput.print_watcher(MOD_ERR_DEBUG, _FUNC_NAME_, 'self.word_entries')
        return

        #TBD
        #for entry in soup.find_all('div', {'class':"headword-row"}):
            #print entry.get_text()

        #for entry in soup.find_all('div', {'id':"other-words-anchor"}):
            #print entry.get_text()
