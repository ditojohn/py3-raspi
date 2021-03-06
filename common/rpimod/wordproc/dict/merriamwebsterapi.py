#!/usr/bin/env python
# -*- encoding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : merriamwebsterapi.py
# Description : Dictionary lookup functions sourcing from Merriam Webster Collegiate Dictionary
# Author      : Dito Manavalan
# Date        : 2017/06/06
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
import xml.etree.cElementTree as ElementTree

from abc import ABCMeta, abstractmethod, abstractproperty
from urllib import quote, quote_plus
from urllib2 import urlopen

sys.path.insert(0, "..")
import common.rpimod.stdio.output as coutput

# Set to True to turn debug messages on
SB_ERR_DEBUG = False

################################################################
# Dictionary Configuration Variables
################################################################

DICT_SOURCE_NAME = unicode("Merriam-Webster's Collegiate Dictionary", 'utf-8')
DICT_ENTRY_URL = unicode("http://www.dictionaryapi.com/api/v1/references/collegiate/xml/{WORD}?key={KEY}", 'utf-8')
DICT_AUDIO_URL = unicode("http://media.merriam-webster.com/soundc11/{FOLDER}/{CLIP}", 'utf-8')
DICT_KEY = unicode("cbbd4001-c94d-493a-ac94-7268a7e41f6f", 'utf-8')

DICT_UNICODE_EMPTY_STR = unicode("", 'utf-8')

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
# API Wrapper Class
################################################################

class MWApiWrapper:
    """ Defines an interface for wrappers to Merriam Webster web APIs. """

    __metaclass__ = ABCMeta

    def __init__(self, key=None, urlopen=urlopen):
        """ key is the API key string to use for requests. urlopen is a function
        that accepts a url string and returns a file-like object of the results
        of fetching the url. defaults to urllib2.urlopen, and should throw """
        self.key = key
        self.urlopen = urlopen

    @abstractproperty
    def base_url():
        """ The api endpoint url without trailing slash or format (/xml).
        """
        pass

    @abstractmethod
    def parse_xml(root, word):
        pass

    def request_url(self, word):
        """ Returns the target url for an API GET request (w/ API key).
        >>> class MWDict(MWApiWrapper):
        ...     base_url = "mw.com/my-api-endpoint"
        ...     def parse_xml(): pass
        >>> MWDict("API-KEY").request_url("word")
        'mw.com/my-api-endpoint/xml/word?key=API-KEY'
        Override this method if you need something else.
        """

        if self.key is None:
            raise InvalidAPIKeyException("API key not set")
        qstring = "{0}?key={1}".format(quote(word), quote_plus(self.key))
        return ("{0}/xml/{1}").format(self.base_url, qstring)

    #def lookup(self, word):
    def lookup(self, word, entryXML):
        #response = self.urlopen(self.request_url(word))
        #data = response.read()
        data = entryXML

        try:
            root = ElementTree.fromstring(data)
        except ElementTree.ParseError:
            if re.search("Invalid API key", data):
                raise InvalidAPIKeyException()
            data = re.sub(r'&(?!amp;)', '&amp;', data)
            try:
                root = ElementTree.fromstring(data)
            except ElementTree.ParseError:
                raise InvalidResponseException(word)

        suggestions = root.findall("suggestion")
        if suggestions:
            suggestions = [s.text for s in suggestions]
            raise WordNotFoundException(word, suggestions)

        return self.parse_xml(root, word)

    def _flatten_tree(self, root, exclude=None):
        """ Returns a list containing the (non-None) .text and .tail for all
        nodes in root.
        exclude is a list of tag names whose text attributes should be
        excluded. their tails will still be included.
        """

        parts = [root.text] if root.text else []
        for node in root:
            targets = [node.tail]
            if not exclude or node.tag not in exclude:
                targets.insert(0, node.text)
            for p in targets:
                if p:
                    parts.append(p)
        return parts

    def _stringify_tree(self, *args, **kwargs):
        " Returns a string of the concatenated results from _flatten_tree "
        return ''.join(self._flatten_tree(*args, **kwargs))


################################################################
# Dictionary Structure Classes
################################################################

class Inflection(object):
    def __init__(self, label, forms, spellings, sound_fragments, sound_urls, pronunciations):
        self.label = label
        self.forms = forms
        self.spellings = spellings
        self.sound_fragments = sound_fragments
        self.sound_urls = sound_urls
        self.pronunciations = pronunciations

class WordSense(object):
    def __init__(self, definition, examples):
        self.definition = definition
        self.examples = examples

    def __str__(self):
        return "{0}, ex: [{1}]".format(self.definition[:30], ", ".join(i[:15] for i in self.examples))

    def __repr__(self):
        return "WordSense({0})".format(self.__str__())

    def __iter__(self):
        yield self.definition
        yield self.examples

class MWDictionaryEntry(object):
    def build_sound_url(self, fragment):
        _FUNC_NAME_ = "build_sound_url"

        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'fragment')

        base_url = "http://media.merriam-webster.com/soundc11"
        number_prefix_match = re.search(r'^([0-9]+)', fragment)
        special_prefix_match = re.search(r'^(gg|bix)', fragment)
        if number_prefix_match:
            prefix = "number"
        elif special_prefix_match:
            prefix = special_prefix_match.group(1)
        else:
            prefix = fragment[0]
        return "{0}/{1}/{2}".format(base_url, prefix, fragment)


################################################################
# MW Learners Dictionary
################################################################

class LearnersDictionaryEntry(MWDictionaryEntry):
    def __init__(self, word, attrs):
        # word,  pronounce, sound_url, art_url, inflection, pos

        self.word = word
        self.headword = attrs.get("headword")
        self.alternate_headwords = attrs.get("alternate_headwords")
        self.pronunciations = attrs.get("pronunciations")
        self.function = attrs.get("functional_label")
        self.inflections = attrs.get("inflections") # (form, [pr], note,)
        self.senses = attrs.get("senses")  # list of ("def text", ["examples"]
        self.audio = [self.build_sound_url(f) for f in
                      attrs.get("sound_fragments")]
        self.illustrations = [self.build_illustration_url(f) for f in
                              attrs.get("illustration_fragments")]

    def build_illustration_url(self, fragment):
        base_url = "www.learnersdictionary.com/art/ld"
        fragment = re.sub(r'\.(tif|eps)', '.gif', fragment)
        return "{0}/{1}".format(base_url, fragment)


class LearnersDictionary(MWApiWrapper):

    base_url = "http://www.dictionaryapi.com/api/v1/references/learners"

    def parse_xml(self, root, word):
        entries = root.findall("entry")
        for num, entry in enumerate(entries):
            args = {}
            args['illustration_fragments'] = [e.get('id') for e in
                                     entry.findall("art/artref")
                                     if e.get('id')]
            args['headword'] = entry.find("hw").text
            args['pronunciations'] = self._get_pronunciations(entry)
            sound = entry.find("sound")
            args['sound_fragments'] = []
            if sound:
                args['sound_fragments'] = [s.text for s in sound]
            args['functional_label'] = getattr(entry.find('fl'), 'text', None)
            args['inflections'] = self._get_inflections(entry)
            args['senses'] = self._get_senses(entry)
            yield LearnersDictionaryEntry(
                re.sub(r'(?:\[\d+\])?\s*', '', entry.get('id')),
                       args)

    def _get_inflections(self, root):
        """ Returns a generator of Inflections found in root.
        inflection nodes that have <il>also</il> will have their inflected form
        added to the previous inflection entry.
        """
        for node in root.findall("in"):
            label, forms = None, []
            for child in node:
                if child.tag == 'il':
                    if child.text == 'also':
                        pass  # next form will be added to prev inflection-list
                    else:
                        if label is not None or forms != []:
                            yield Inflection(label, forms)
                        label, forms = child.text, []
                if child.tag == 'if':
                    forms.append(child.text)
            if label is not None or forms != []:
                yield Inflection(label, forms)

        for node in root.findall("uro"):
            label, forms = None, []
            for child in node:
                if child.tag == 'ure':
                    forms.append(child.text)
            if label is not None or forms != []:
                yield Inflection(label, forms)

    def _get_pronunciations(self, root):
        """ Returns list of IPA for regular and 'alternative' pronunciation. """
        _FUNC_NAME_ = "LearnersDictionary._get_pronunciations"

        prons = root.find("./pr")
        pron_list = []
        if prons is not None:
            ps = self._flatten_tree(prons, exclude=['it'])
            pron_list.extend(ps)
        prons = root.find("./altpr")
        if prons is not None:
            ps = self._flatten_tree(prons, exclude=['it'])
            pron_list.extend(ps)
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, '<ReplaceText>') 
        return [p.strip(', ') for p in pron_list]

    def _get_senses(self, root):
        """ Returns a generator yielding tuples of definitions and example
        sentences: (definition_string, list_of_usage_example_strings). Each
        tuple should represent a different sense of the word.
        """
        for definition in root.findall('./def/dt'):
            # could add support for phrasal verbs here by looking for
            # <gram>phrasal verb</gram> and then looking for the phrase
            # itself in <dre>phrase</dre> in the def node or its parent.
            dstring = self._stringify_tree(definition,
                                          exclude=['vi', 'wsgram',
                                                   'ca', 'dx', 'snote',
                                                   'un'])
            dstring = re.sub("^:", "", dstring)
            dstring = re.sub(r'(\s*):', r';\1', dstring).strip()
            if not dstring:  # use usage note instead
                un = definition.find('un')
                if un is not None:
                    dstring = self._stringify_tree(un, exclude=['vi'])
            usage = [self._vi_to_text(u).strip()
                     for u in definition.findall('.//vi')]
            yield WordSense(dstring, usage)

    def _vi_to_text(self, root):
        example = self._stringify_tree(root)
        return re.sub(r'\s*\[=.*?\]', '', example)


################################################################
# MW Collegiate Dictionary
################################################################

class CollegiateDictionaryEntry(MWDictionaryEntry):
    
    def __init__(self, word, attrs):
        _FUNC_NAME_ = "CollegiateDictionaryEntry.__init__"

        self.word = word
        self.headword = attrs.get('headword')
        self.spelling = attrs.get('spelling')
        self.function = attrs.get('functional_label')
        
        self.pronunciation = attrs.get("pronunciation")
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, "self.pronunciation")

        #self.pronunciations = attrs.get("pronunciations")     
        self.inflections = attrs.get("inflections")
        self.senses = attrs.get("senses")
        self.audio = [self.build_sound_url(f) for f in
                      attrs.get("sound_fragments")]
        self.illustrations = [self.build_illustration_url(f) for f in
                              attrs.get("illustration_fragments")]


    def build_illustration_url(self, fragment):
        base_url = 'http://www.merriam-webster.com/art/dict'
        fragment = re.sub(r'\.(bmp)', '.htm', fragment)
        return "{0}/{1}".format(base_url, fragment)

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

class CollegiateDictionary(MWApiWrapper):
    base_url = "http://www.dictionaryapi.com/api/v1/references/collegiate"

    def parse_xml(self, root, word):
        _FUNC_NAME_ = "CollegiateDictionary.parse_xml"
        for entry in root.findall('entry'):
            args = {}
            args['headword'] = entry.find('hw').text
            args['spelling'] = re.sub("\*", "", entry.find('hw').text)
            args['functional_label'] = getattr(entry.find('fl'), 'text', DICT_UNICODE_EMPTY_STR)
            
            args['pronunciation'] = getattr(entry.find('pr'), 'text', DICT_UNICODE_EMPTY_STR)
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, "args['pronunciation']") 
            #args['pronunciations'] = self._get_pronunciations(entry)
            
            args['inflections'] = self._get_inflections(entry)
            args['senses'] = self._get_senses(entry)
            
            args['sound_fragments'] = [e.text for e in
                                              entry.findall("sound/wav")
                                              if e.text]
            coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, "args['sound_fragments']")

            args['illustration_fragments'] = [e.text for e in
                                              entry.findall("art/bmp")
                                              if e.text]

            yield CollegiateDictionaryEntry(word, args)

    def _get_pronunciations(self, root):
        """ Returns list of IPA for regular and 'alternative' pronunciation. """
        _FUNC_NAME_ = "CollegiateDictionary._get_pronunciations"

        prons = root.find("./pr")
        pron_list = []
        if prons is not None:
            ps = self._flatten_tree(prons, exclude=['it'])
            pron_list.extend(ps)
        
        coutput.print_watcher(SB_ERR_DEBUG, _FUNC_NAME_, 'pron_list')
        return pron_list

    def _get_inflections(self, root):
        """ Returns a generator of Inflections found in root.
        inflection nodes that have <il>also</il> will have their inflected form
        added to the previous inflection entry.
        """
        _FUNC_NAME_ = "CollegiateDictionary._get_inflections"

        dict_helper = MWDictionaryEntry()

        for node in root.findall("in"):
            label, forms, spellings, sound_fragments, sound_urls, pronunciations = None, [], [], [], [], []
            for child in node:
                coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format("child.tag", child.tag))
                if child.tag == 'il':
                    if child.text in ['also', 'or']:
                        pass  # next form will be added to prev inflection-list
                    else:
                        if label is not None or forms != []:
                            yield Inflection(label, forms, spellings, sound_fragments, sound_urls, pronunciations)
                        label, forms, spellings, sound_fragments, sound_urls, pronunciations = child.text, [], [], [], [], []
                if child.tag == 'if':
                    forms.append(child.text)
                    spellings.append(re.sub("\*", "", child.text))
                if child.tag == 'sound':

                    coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format("child.find(\"wav\").text", child.find("wav").text))

                    sound_fragments.append(child.find("wav").text)
                    sound_urls.append(dict_helper.build_sound_url(child.find("wav").text))
                if child.tag == 'pr':
                    pronunciations.append(child.text)
            if label is not None or forms != []:
                yield Inflection(label, forms, spellings, sound_fragments, sound_urls, pronunciations)

        for node in root.findall("uro"):
            label, forms, spellings, sound_fragments, sound_urls, pronunciations = None, [], [], [], [], []
            for child in node:
                if child.tag == 'ure':
                    forms.append(child.text)
                    spellings.append(re.sub("\*", "", child.text))
                if child.tag == 'sound':
                    
                    coutput.print_debug(SB_ERR_DEBUG, _FUNC_NAME_, "{0} :: {1}".format("child.find(\"wav\").text", child.find("wav").text))

                    sound_fragments.append(child.find("wav").text)
                    sound_urls.append(dict_helper.build_sound_url(child.find("wav").text))
                if child.tag == 'pr':
                    pronunciations.append(child.text)
            if label is not None or forms != []:
                yield Inflection(label, forms, spellings, sound_fragments, sound_urls, pronunciations)

    """
    <!ELEMENT def (vt?, date?, sl*, sense, ss?, us?)+ >
    <!ELEMENT sense (sn?,
                    (sp, sp_alt?, sp_ipa?, sp_wod?, sound?)?,
                    svr?, sin*, slb*, set?, ssl*, dt*,
                    (sd, sin?,
                      (sp, sp_alt?, sp_ipa?, sp_wod?, sound?)?,
                    slb*, ssl*, dt+)?)>
    """

    def _get_senses(self, root):
        """ Returns a generator yielding tuples of definitions and example
        sentences: (definition_string, list_of_usage_example_strings). Each
        tuple should represent a different sense of the word.
        """
        for definition in root.findall('./def/dt'):
            # could add support for phrasal verbs here by looking for
            # <gram>phrasal verb</gram> and then looking for the phrase
            # itself in <dre>phrase</dre> in the def node or its parent.
            dstring = self._stringify_tree(definition,
                                          exclude=['vi', 'wsgram',
                                                   'ca', 'dx', 'snote',
                                                   'un'])
            dstring = re.sub("^:", "", dstring)
            dstring = re.sub(r'(\s*):', r';\1', dstring).strip()
            if not dstring:  # use usage note instead
                un = definition.find('un')
                if un is not None:
                    dstring = self._stringify_tree(un, exclude=['vi'])
            usage = [self._vi_to_text(u).strip()
                     for u in definition.findall('.//vi')]
            yield WordSense(dstring, usage)

    def _vi_to_text(self, root):
        example = self._stringify_tree(root)
        return re.sub(r'\s*\[=.*?\]', '', example)
