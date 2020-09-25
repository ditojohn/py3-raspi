#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import re
import urllib3
from bs4 import BeautifulSoup
import traceback

sys.path.insert(0, "..")
import common.rpimod.stdio.input as cinput
import common.rpimod.stdio.output as coutput
import common.rpimod.stdio.fileio as cfile

# Set to True to turn debug messages on
#APP_DEBUG_MODE_ENABLED = True
APP_DEBUG_MODE_ENABLED = False

################################################################
# Configuration variables
################################################################

APP_SOURCE_ID = "spell-pundit"
APP_SOURCE_DESC = "SpellPundit"
APP_SOURCE_URL = "https://www.spellpundit.com/spell/index.php"
APP_DATA_DIR = "data/download/spellpundit/"

# Vocabulary
APP_MODULE_ID = "004"
APP_MODULE_TYPE = "vocab" # Set to module type: "roots", "spelling", "vocab"
APP_NAVIGATE_MENU = "Vocab>Main Vocabulary Modules>Infrequent Phrased and Hyphenated Vocab words"
APP_MODULE_NM = "vocab-phrased-infrequent" #"vocab-01-easy-intermed"

# Spelling
APP_MODULE_ID = "003"
APP_MODULE_TYPE = "spelling" # Set to module type: "roots", "spelling", "vocab"
APP_NAVIGATE_MENU = "Spelling>North South Foundation (NSF) Spelling Modules>Past NSF SSB Spelling Words"
APP_MODULE_NM = "spelling-contest-nsf-ssb" #"vocab-01-easy-intermed"

# Contests
APP_MODULE_ID = "004"
APP_MODULE_TYPE = "vocab" # Set to module type: "roots", "spelling", "vocab"
APP_NAVIGATE_MENU = "Custom Spelling and Vocabulary Modules>Popular School, District/County, and Regional Vocabulary Words"
APP_MODULE_NM = "vocab-custom-popular-regional" #"vocab-01-easy-intermed"

# Contests
APP_MODULE_ID = "004"
APP_MODULE_TYPE = "vocab" # Set to module type: "roots", "spelling", "vocab"
APP_NAVIGATE_MENU = "Vocab>WishWin Vocabulary Modules>2019 WishWin Senior Vocabulary List Words Module"
APP_MODULE_NM = "vocab-contest-wishwin-2019-senior" #"vocab-01-easy-intermed"


# Set to empty list as default to select all sets
APP_SELECT_SET_LIST = []
# Set to name of first list as default to select all sets
APP_START_SET_NM = "" #"set-09"
# Set to empty string as default to select all sets
APP_STOP_SET_NM = ""

# ToDo : Support for lists of modules
APP_MODULE_LIST = [
    {   
        "id": "",
        "type": "",
        "name": "spelling-contest-spandana-2019-junior",
        "menu": "Spelling>Spandana Spelling Bee Modules>2019 Spandana Junior Spelling List Words Module",
        "selectList": [],
        "startSet": "",
        "stopSet": ""
    }
]

# Fast
APP_INIT_WAIT_DELAY = 4
APP_TIMEOUT_WAIT_DELAY = 6
APP_WAIT_DELAY = 1
APP_SLEEP_DELAY = 1

# Medium
APP_INIT_WAIT_DELAY = 4.5
APP_TIMEOUT_WAIT_DELAY = 8
APP_WAIT_DELAY = 1.5
APP_SLEEP_DELAY = 2

# Slow
APP_INIT_WAIT_DELAY = 5
APP_TIMEOUT_WAIT_DELAY = 10
APP_WAIT_DELAY = 3
APP_SLEEP_DELAY = 4

################################################################
# Application Directories
################################################################

APP_LIST_DIR = APP_DATA_DIR + "list/"
APP_DICT_DIR = APP_DATA_DIR + "dict/"

################################################################
# Application Files
################################################################

APP_LIST = "spelling_bee_{SOURCE}-{MODULE_ID}-{MODULE_NM}-{SET_ID}.txt"
APP_LIST_ERROR = "spelling_bee_{SOURCE}-{MODULE_ID}-{MODULE_NM}-{SET_ID}.err"
APP_DICT_ENTR = "sb_{WORD}.dat"
APP_DICT_CLIP = "sb_{WORD}.mp3"

################################################################
# Internal Variables
################################################################

APP_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}

APP_NEWLINE = "\n"
APP_EMPTY_STRING = ""
APP_WORD_DELIMITER = ";"

################################################################
# Configure Selenium Chrome Webdriver
# Reference:
# https://www.quora.com/How-do-I-install-Selenium-in-Python-on-a-Linux-environment
# https://christopher.su/2015/selenium-chromedriver-ubuntu/
# https://stackoverflow.com/questions/50642308/webdriverexception-unknown-error-devtoolsactiveport-file-doesnt-exist-while-t
# https://stackoverflow.com/questions/59186984/selenium-common-exceptions-sessionnotcreatedexception-message-session-not-crea
################################################################

from selenium import webdriver

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()
#chrome_options.add_argument("start-maximized") # open Browser in maximized mode
chrome_options.add_argument("disable-infobars") # disabling infobars
chrome_options.add_argument("--disable-extensions") # disabling extensions
chrome_options.add_argument("--disable-gpu") # applicable to windows os only
chrome_options.add_argument("--disable-dev-shm-usage") # overcome limited resource problems
chrome_options.add_argument("--no-sandbox") # bypass OS security model -- Addresses unknown error: DevToolsActivePort file doesn't exist

chrome_options.add_argument('--headless') # run in headless mode -- in case of chromedriver compatibility issues
chrome_options.add_argument('window-size=1920x1480')
chrome_options.add_argument("--mute-audio") # mute audio

browser = webdriver.Chrome(chrome_options=chrome_options)

################################################################
# Configure Connection Pool
################################################################

connectionPool = urllib3.PoolManager(5, headers=APP_USER_AGENT)

################################################################
# Application
################################################################

def exit_app(exitCode=0):
    # Close browser session
    browser.close()
    # Resume input from stdin
    cinput.set_term_input(True)
    # Exit
    exit(exitCode)


# Open new session in browser
while True:
    try:
        wait = WebDriverWait(browser, APP_INIT_WAIT_DELAY)
        browser.get(APP_SOURCE_URL)
        #browser.save_screenshot('download_spellpundit_module-output-001.png')

        userBox = wait.until(EC.presence_of_element_located((By.NAME, 'user')))
        print("Sending Username...")
        userBox.send_keys("dito.john@gmail.com")
        time.sleep(APP_WAIT_DELAY)

        passBox = wait.until(EC.presence_of_element_located((By.NAME, 'passwd')))
        print("Sending Password...")
        passBox.send_keys("karukutty")
        time.sleep(APP_WAIT_DELAY)

        print("Logging in...")
        browser.find_element_by_xpath("//button[text()='Sign in']").click()
        time.sleep(APP_SLEEP_DELAY)
        print("\nHome URL: " + browser.current_url)

        print("Navigating to menu for module {SOURCE}/{MODULE_ID}-{MODULE_NM}...".format(SOURCE=APP_SOURCE_ID, MODULE_ID=APP_MODULE_ID, MODULE_NM=APP_MODULE_NM))
        for menuItem in APP_NAVIGATE_MENU.split('>'):
            print("Navigating to menu item: {}".format(menuItem))
            browser.find_element_by_link_text(menuItem).click()
            time.sleep(APP_WAIT_DELAY)

        print("\nFetching module meta-info ...")
        print("Module URL: " + browser.current_url)
        moduleTitle = browser.find_element_by_xpath("//div[@class='panel-heading']").text
        moduleTableElement = browser.find_element_by_xpath("//div[@class='table-responsive']")

        # Break loop if try is successful
        break

    except Exception as e:
        # Displays the trace for the error
        coutput.print_err(traceback.format_exc())

        exceptionName = type(e).__name__
        if exceptionName == "TimeoutException":
            coutput.print_warn("Connection timeout. Waiting for {}s ...".format(APP_TIMEOUT_WAIT_DELAY))
            time.sleep(APP_TIMEOUT_WAIT_DELAY)
        else:
            exit_app(1)

# Retrieve sets from module
setRowElements = moduleTableElement.find_elements_by_xpath("//table/tbody/tr")

setCounter = 0
setEntries = []
processFlag = False

for setRowElement in setRowElements:
    setCounter = setCounter + 1

    setColElement = setRowElement.find_element_by_xpath(".//td")
    setName = setColElement.text.strip().lower().replace(" ", "-")
    setID = "{:03d}-".format(setCounter) + setName
    setURL = setRowElement.find_element_by_xpath(".//a[contains(@href,'&bt=r') and not(contains(@href,'_test_'))]").get_property("href")

    print("Checking set {}.".format(setName))
    coutput.print_watcher("setID")
    coutput.print_watcher("setURL")

    if len(APP_SELECT_SET_LIST) > 0:
        if setName in APP_SELECT_SET_LIST:
            processFlag = True
        else:
            processFlag = False
    else:
        if APP_START_SET_NM == APP_EMPTY_STRING:
            processFlag = True
        elif setName == APP_START_SET_NM:
            processFlag = True

        if setName == APP_STOP_SET_NM:
            processFlag = False

    if processFlag is False:
        print("Set {} marked for exclusion. Skipping.".format(setName))
    else:
        print("Set {} marked for processing.".format(setName))
        setEntries.append({"id" : setID, "name" : setName, "url" : setURL})

print("\nModule Label: " + moduleTitle)
print("Module Name: {SOURCE}/{MODULE_ID}-{MODULE_NM}".format(SOURCE=APP_SOURCE_ID, MODULE_ID=APP_MODULE_ID, MODULE_NM=APP_MODULE_NM))
print("Sets marked for processing:")
for setEntry in setEntries:
    print(setEntry)

userInput = cinput.get_keypress("\nPlease review sets and press any key when ready ... ")

# Iterate through sets from module
for setEntry in setEntries:
    print("\nSet URL: " + setEntry["url"])

    while True:
        try:
            browser.get(setEntry["url"])

            print("\nInitializing list and error files ...")
            
            APP_LIST_FILE = APP_LIST_DIR + cfile.cleanse_filename(APP_LIST.format(SOURCE=APP_SOURCE_ID, MODULE_ID=APP_MODULE_ID, MODULE_NM=APP_MODULE_NM, SET_ID=setEntry["id"]))
            print("Word List: " + APP_LIST.format(SOURCE=APP_SOURCE_ID, MODULE_ID=APP_MODULE_ID, MODULE_NM=APP_MODULE_NM, SET_ID=setEntry["id"]))
            if os.path.isfile(APP_LIST_FILE) and os.path.getsize(APP_LIST_FILE) > 0:
                print("List file {} exists. Deleting...".format(APP_LIST_FILE))
                cfile.delete(APP_LIST_FILE)

            APP_LIST_ERROR_FILE = APP_LIST_DIR + cfile.cleanse_filename(APP_LIST_ERROR.format(SOURCE=APP_SOURCE_ID, MODULE_ID=APP_MODULE_ID, MODULE_NM=APP_MODULE_NM, SET_ID=setEntry["id"]))
            if os.path.isfile(APP_LIST_ERROR_FILE) and os.path.getsize(APP_LIST_ERROR_FILE) > 0:
                print("List error file {} exists. Deleting...".format(APP_LIST_ERROR_FILE))
                cfile.delete(APP_LIST_ERROR_FILE)

            # Break loop if try is successful
            break

        except Exception as e:
            # Displays the trace for the error
            coutput.print_err(traceback.format_exc())

            exceptionName = type(e).__name__
            if exceptionName == "TimeoutException":
                coutput.print_warn("Connection timeout. Waiting for {}s ...".format(APP_TIMEOUT_WAIT_DELAY))
                time.sleep(APP_TIMEOUT_WAIT_DELAY)
            else:
                exit_app(1)

    while True:
        try:
            print("\nFetching word meta-info ...")
            
            headInfoElement = browser.find_element_by_css_selector(".col-sm-9.col-md-9").find_element_by_css_selector(".panel-heading")
            moduleName = headInfoElement.find_element_by_tag_name("a").text

            wordInfoElement = browser.find_element_by_xpath("//form[contains(@name,'moduleform')]")
            moduleID = wordInfoElement.find_element_by_id("module_id").get_property("value")
            wordID = wordInfoElement.find_element_by_xpath("//*[contains(@id,'_id')]").get_property("value")

            bodyInfoElement = wordInfoElement.find_element_by_xpath("//div[@class='table-responsive']/table/thead")
            reMatch = re.search("(.*)[ ]+(?:Root|Word|Vocabulary Word|Homonym)[ ]+(\d+)[ ]+of[ ]+(\d+).*", bodyInfoElement.text, flags=re.M)
            wordIndex = reMatch.group(2).strip() + "/" + reMatch.group(3).strip()

            reMatch = re.search("https://.*/\?mode=(\w+).*", setEntry["url"], flags=re.M)
            mode = reMatch.group(1).strip()

            print("\n>>>>>>>>>> {} Fetching entry rows ...".format(wordIndex))

            entryRows = browser.find_elements_by_xpath("//div[@class='table-responsive']/table/tbody/tr")

            displayWord = ''
            listWord = ''
            keyWord = ''

            wordRespelling = ''
            wordAudioURL = ''
            wordFuncLabel = ''
            wordEtymology = ''
            wordDefinition = ''
            wordExamples = ''
            wordNote = ''       
            wordSentence = ''
            wordRelated = ''

            wordEntry = ''

            for row in entryRows:
                entryCols = row.find_elements_by_tag_name("td")

                entryRowName = entryCols[0].text.strip()
                entryRowValue = entryCols[1].text.strip()

                if entryRowName in ["Root", "Word", "Vocab"]:
                    displayWord = entryRowValue

                    #listWord = re.sub('[ ;,]+or[ ;,]+', APP_WORD_DELIMITER, displayWord, flags=re.IGNORECASE)
                    #listWord = re.sub('[ ;,]+also[ ;,]+', APP_WORD_DELIMITER, listWord, flags=re.IGNORECASE)
                    #listWord = re.sub('[ ;,]+oe[ ;,]+', APP_WORD_DELIMITER, listWord, flags=re.IGNORECASE)
                    #listWord = re.sub('[ ;,]+plural[ ;,]+', APP_WORD_DELIMITER, listWord, flags=re.IGNORECASE)
                    #listWord = re.sub('[ ]*[;,]+[ ]*', APP_WORD_DELIMITER, listWord, flags=re.IGNORECASE)

                    #Search pattern: /([;, ]+(also|or|oe|plural)[;, ]+|,[; ]+)/
                    #Replace pattern: /;/

                    #Search pattern: /-(also|or|oe|plural)[, ]+/
                    #Replace pattern: /-;/

                    listWord = re.sub('[ ;,]+(also|or|oe|plural)[ ;,]+', APP_WORD_DELIMITER, displayWord, flags=re.IGNORECASE)
                    listWord = re.sub('-(also|or|oe|plural)[, ]+', '-' + APP_WORD_DELIMITER, listWord, flags=re.IGNORECASE)
                    listWord = re.sub(',[; ]+', APP_WORD_DELIMITER, listWord, flags=re.IGNORECASE)
                    listWord = listWord.strip()

                    keyWord = re.sub(';.*', APP_EMPTY_STRING, listWord, flags=re.IGNORECASE).replace(" ", "_").lower().strip()
                    wordMeta = 'Mode={};ModuleName={};ModuleID={};SetName={};SetID={};WordIndex={};WordID={};KeyWord={};DisplayWord={}'.format(mode,moduleName,moduleID,setEntry["name"],setEntry["id"],wordIndex,wordID,keyWord,displayWord)

                elif entryRowName == "Pronunciation":
                    wordRespelling = entryRowValue
                    wordRespelling = "\\{}\\".format(wordRespelling)
                elif entryRowName == "Part of Speech":
                    wordFuncLabel = entryRowValue
                elif entryRowName == "Lang. of Origin":
                    wordEtymology = entryRowValue
                elif entryRowName == "Definition":
                    wordDefinition = entryRowValue
                elif entryRowName == "Examples":
                    wordExamples = entryRowValue
                    wordExamples = re.sub('[ ]*,[ ]*', APP_WORD_DELIMITER, wordExamples, flags=re.IGNORECASE)
                elif entryRowName == "Addl. Info":
                    wordNote = entryRowValue
                elif entryRowName == "Sentence":
                    wordSentence = entryRowValue
                elif entryRowName == "Related Words":
                    wordRelated = entryRowValue
                    wordRelated = re.sub('[ ]*,[ ]*', APP_WORD_DELIMITER, wordRelated, flags=re.IGNORECASE)
                elif entryRowName != APP_EMPTY_STRING:
                    cfile.append(APP_LIST_ERROR_FILE, "{};{}".format(displayWord, entryRowName))


            audioElement = browser.find_element_by_xpath("//audio[@id='audio1']")
            if audioElement is not None:
                wordAudioURL = audioElement.get_property("src")

            wordEntry = "#!Source: " + APP_SOURCE_DESC
            wordEntry = wordEntry + APP_NEWLINE + "#!Word: " + listWord
            wordEntry = wordEntry + APP_NEWLINE + "#!Respelling: " + wordRespelling
            wordEntry = wordEntry + APP_NEWLINE + "#!AudioURL: " + wordAudioURL
            wordEntry = wordEntry + APP_NEWLINE + "#!Etymology: " + wordEtymology
            wordEntry = wordEntry + APP_NEWLINE + "#!Sentence: " + wordSentence
            wordEntry = wordEntry + APP_NEWLINE + "#!Note: " + wordNote
            wordEntry = wordEntry + APP_NEWLINE + "#!Meta: " + wordMeta
            wordEntry = wordEntry + APP_NEWLINE + "#!Examples: " + wordExamples
            wordEntry = wordEntry + APP_NEWLINE + "#!Related: " + wordRelated
            wordEntry = wordEntry + APP_NEWLINE + "({}) {}".format(wordFuncLabel, wordDefinition)

            print("\nEntry for {}: ".format(displayWord))
            print(wordEntry)

            print("\nAdding to word list file: " + APP_LIST_FILE)
            cfile.append(APP_LIST_FILE, listWord)

            APP_DICT_ENTR_FILE = APP_DICT_DIR + cfile.cleanse_filename(APP_DICT_ENTR.format(WORD=listWord))
            if os.path.isfile(APP_DICT_ENTR_FILE) and os.path.getsize(APP_DICT_ENTR_FILE) > 100:
                print("Definition file {} exists. Skipping.".format(APP_DICT_ENTR_FILE))
            else:
                print("Creating definition file: " + APP_DICT_ENTR_FILE)
                cfile.write(APP_DICT_ENTR_FILE, wordEntry)

            APP_DICT_CLIP_FILE = APP_DICT_DIR + cfile.cleanse_filename(APP_DICT_CLIP.format(WORD=listWord))
            if os.path.isfile(APP_DICT_CLIP_FILE) and os.path.getsize(APP_DICT_CLIP_FILE) > 100:
                print("Pronunciation file {} exists. Skipping.".format(APP_DICT_CLIP_FILE))
            else:
                print("Creating pronunciation file: " + APP_DICT_CLIP_FILE)
                cfile.download(connectionPool, wordAudioURL, APP_DICT_CLIP_FILE)

            while True:

                nextButton = browser.find_element_by_id("nextButton")
                nextButton.click()
                print("Clicked Next button")
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".col-sm-9.col-md-9")))
                time.sleep(APP_WAIT_DELAY)

                nextWordInfoElement = browser.find_element_by_xpath("//form[contains(@name,'moduleform')]")
                nextWordID = nextWordInfoElement.find_element_by_xpath("//*[contains(@id,'_id')]").get_property("value")

                if nextWordID == wordID:
                    coutput.print_err("Page not refreshed. Retrying in {}s ...".format(APP_TIMEOUT_WAIT_DELAY))
                    time.sleep(APP_TIMEOUT_WAIT_DELAY)
                else:
                    break

        except Exception as e:
            exceptionName = type(e).__name__
            if exceptionName == "UnexpectedAlertPresentException":
                coutput.print_warn("Last page of set reached. Moving to next set ...")
                break
            else:
                # Displays the trace for the error
                coutput.print_err(traceback.format_exc())
                #coutput.print_err("Exception: " + str(e))

                # Accept alert
                #time.sleep(1)
                #alert = browser.switch_to.alert
                #alert.accept()

                coutput.print_err("Unhandled exception [{}] occurred. Exiting ...".format(exceptionName))
                exit_app(1)


# Resume input and exit
coutput.print_warn("Processing complete. Exiting ...")
exit_app()
