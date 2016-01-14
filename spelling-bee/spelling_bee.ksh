#!/usr/bin/ksh
. ./project_setup.cfg

################################################################
# Syntax :    ksh spelling_bee.ksh runMode contestYear mode selection
# where        runMode is practice or test.
#            contestYear is the year of the contest in YYYY format
#            mode is chapter, count or word.
#                In chapter mode, the next argument is the chapter number
#                    selection is the chapter number of the word list to be practiced.
#                    Default chapter size is 50 words.
#                In count mode, the next argument is the word range
#                    selection is the index range of words in the word list to be practiced.
#                In word mode, the next argument is the word range
#                    selection is the range of words in the word list to be practiced.
# Example:    ksh spelling_bee.ksh practice 2016 chapter 7
#             ksh spelling_bee.ksh test 2016 count 10-15
#             ksh spelling_bee.ksh practice 2016 word lary-frees
################################################################

################################################################
# Configuration variables
################################################################
SB_CHAPTER_SIZE=50
SB_MEANING_COUNT=3
SB_REPEAT_COUNT=2
SB_REPEAT_DELAY=1.5

################################################################
# Internal variables
################################################################
SB_LIST_BULLET='•'
SB_RIGHT_SYMBOL='√'
SB_WRONG_SYMBOL='X'
SB_PRACTICE_KEYBOARD_MENU="[N]ext [P]revious [R]epeat Re[v]iew [S]how [L]ookup [H]elp E[x]it"
SB_TEST_KEYBOARD_MENU="E[x]it"

SB_WORD_LIST_URL="$DATA/spelling_bee_@YEAR@.txt"
SB_TMP_WORD_ENTRY="${DATA}/sbtmpentry.xml"
SB_TMP_WORD_CLIP="${DATA}/sbtmpclip.wav"
SB_TMP_TEST_RESULTS="${DATA}/sbtmptest.dat"

#Sample dictionary API URL - http://www.dictionaryapi.com/api/v1/references/collegiate/xml/test?key=cbbd4001-c94d-493a-ac94-7268a7e41f6f
SB_DICT_MW_KEY="cbbd4001-c94d-493a-ac94-7268a7e41f6f"
SB_DICT_MW_ENTRY_URL="http://www.dictionaryapi.com/api/v1/references/collegiate/xml/@WORD@?key=${SB_DICT_MW_KEY}"
SB_DICT_MW_CLIP_URL="http://media.merriam-webster.com/soundc11/@FOLDER@/@CLIP@"

SB_DICT_MW_ENTRY_ERR=0
SB_DICT_MW_CLIP_ERR=0

################################################################
# Debug Configuration
################################################################
_DEBUG="off"

DEBUG()
{
    [ "$_DEBUG" == "on" ] &&  print -n "DEBUG: " && $@
}

WATCH()
{
    varName="$@"
    varValue=$(eval echo "\$${varName}")
    [ "$_DEBUG" == "on" ] &&  print -n "DEBUG: " && echo "\$${varName} = ${varValue}"
}

################################################################
# Function Definitions
################################################################

getXMLValues()
{
    xmlString="$1"
    xmlElement="$2"
    xmlTopN="$3"

    xmlString="$(echo "${xmlString}" | sed "s/<${xmlElement}>/\n<${xmlElement}>/g" | grep -i "<${xmlElement}>")"
    echo "${xmlString}" | while read -r line
    do
        echo "${line}" | sed -n "/${xmlElement}/{s/.*<${xmlElement}>\(.*\)<\/${xmlElement}>.*/\1/;p}" | cut -d ':' -f 2 | sed "s/<[/a-zA-Z_]*>//g"
    done | head -n ${xmlTopN}
}

displayAsList()
{
    inputString="$1"
    bullet="$2"

    echo "${inputString}" | while read -r line
    do
        echo "${line}" | sed "s/^/${bullet} /g"
    done
}

lookupWord()
{
    word="$1"

    # Determine dictionary entry URL
    dictEntryURL="$(echo "${SB_DICT_MW_ENTRY_URL}" | sed "s/@WORD@/${word}/g")"
    WATCH dictEntryURL
    
    # Download dictionary entry
    wget -qO- "${dictEntryURL}" > ${SB_TMP_WORD_ENTRY}
    dictXMLEntry="$(cat ${SB_TMP_WORD_ENTRY})"
    WATCH dictXMLEntry

    # Retrieve meaning from dictionary entry
    dictXMLEntry="$(cat ${SB_TMP_WORD_ENTRY})"
    wordMeaning=$(getXMLValues "${dictXMLEntry}" "dt" "${SB_MEANING_COUNT}")    # Pick top n meanings
    if [[ "${wordMeaning}" == "" ]]; then
        SB_DICT_MW_ENTRY_ERR=1
          # Clear retrieved dictionary entry
        rm -f ${SB_TMP_WORD_ENTRY}
    else
        SB_DICT_MW_ENTRY_ERR=0
    fi

    # Retrieve pronunciation audio clip filename
    wordClip=$(getXMLValues "${dictXMLEntry}" "wav" "1")                        # Pick first sound clip reference
    WATCH wordClip

    if [[ "${wordClip}" == "" ]]; then
        SB_DICT_MW_CLIP_ERR=1
        # Clear previously retrieved audio clip
        rm -f ${SB_TMP_WORD_CLIP}
    else
        SB_DICT_MW_CLIP_ERR=0
        # Determine audio clip folder
        # Reference: http://www.dictionaryapi.com/info/faq-audio-image.htm
        if [[ "${wordClip}" =~ ^bix.* ]]; then
            wordClipFolder="bix"
        elif [[ "${wordClip}" =~ ^gg.* ]]; then
            wordClipFolder="gg"
        elif [[ "${wordClip}" =~ ^[0-9].* ]]; then
            wordClipFolder="number"
        else
            wordClipFolder=$(echo ${wordClip} | cut -c 1 )
        fi
        wordClipURL="$(echo "${SB_DICT_MW_CLIP_URL}" | sed "s/@FOLDER@/${wordClipFolder}/g" | sed "s/@CLIP@/${wordClip}/g")"
        WATCH wordClipURL
        
        # Download audio clip
        wget -qO- ${wordClipURL} > ${SB_TMP_WORD_CLIP}
    fi
}

getWordIndex()
{
    token="$1"
    echo "${wordList}" | grep -i -n -e "^${token}" | head -n 1 | awk -F":" '{print $1}'
}

lookupWordByIndex()
{
    word=$(echo "${wordList}" | head -n ${wordIndex} | tail -1)
    lookupWord "${word}"
}

displayMeaning()
{
    if [[ "${SB_DICT_MW_ENTRY_ERR}" == "0" ]]; then
        # Retrieve meaning from dictionary entry
        dictXMLEntry="$(cat ${SB_TMP_WORD_ENTRY})"
        wordMeaning=$(getXMLValues "${dictXMLEntry}" "dt" "${SB_MEANING_COUNT}")                        # Pick top n meanings

        displayAsList "${wordMeaning}" "${SB_LIST_BULLET}"
    else
        print "ERROR: Unable to lookup dictionary definition"
    fi
}

pronounceWord()
{
    if [[ "${SB_DICT_MW_CLIP_ERR}" == "0" ]]; then
        # Play and repeat dictionary entry pronounciation
        for i in {1..${SB_REPEAT_COUNT}}
        do
            aplay -q ${SB_TMP_WORD_CLIP}
            DEBUG echo "Pronunciation #${i}"
            sleep ${SB_REPEAT_DELAY}
        done
    else
        print "ERROR: Unable to lookup audio pronunciation"
    fi
}

displayWord()
{
    displayTitle="$1"
    
    echo ""
    echo "${displayTitle}"
    displayMeaning
    pronounceWord
}

displayWordList()
{
    echo ""
    echo "Review Chapter [${chapterNum}/${chapterCount}] Words [${wordListStart}-${wordListEnd}]"
    echo "${wordList}" | head -n ${wordListEnd} | tail -n ${activeWordCount} | column -x
}

displayAbout()
{
    echo ""
    echo "Spelling Bee ${contestYear}"
    echo "Word Count [${wordCount}] Chapter [${chapterNum}/${chapterCount}] Words [${wordListStart}-${wordListEnd}]"
    if [[ ${runMode} == "practice" ]]; then
        echo "Practice Keyboard Menu: ${SB_PRACTICE_KEYBOARD_MENU}"
    else
        echo "Test Keyboard Menu: ${SB_TEST_KEYBOARD_MENU}"
    fi
}

captureUserInput()
{
    echo ""
    print -n "> "
    read -n1 userInput </dev/tty
    WATCH userInput 
}

initWordList()
{
    wordListFile="$(echo "${SB_WORD_LIST_URL}" | sed "s/@YEAR@/${contestYear}/g")"
    wordCount=$(wc -l ${wordListFile} | awk '{print $1}')
    chapterCount=$((($wordCount+$SB_CHAPTER_SIZE-1)/$SB_CHAPTER_SIZE))        # Find number of chapters by computing the ceiling
    wordList="$(cat ${wordListFile})"

    if [[ ${mode} == "chapter" ]]; then
        chapterNum=${selection}

        wordListStart=$((($chapterNum-1)*$SB_CHAPTER_SIZE+1))

        wordListEnd=$(($wordListStart+$SB_CHAPTER_SIZE-1))
        if [[ ${wordListEnd} -gt ${wordCount} ]]; then
            wordListEnd=$wordCount
        fi
    elif [[ ${mode} == "count" ]]; then
        chapterNum="-"

        wordListStart=$(echo ${selection} | awk -F"-" '{print $1}')
        WATCH wordListStart

        wordListEnd=$(echo ${selection} | awk -F"-" '{print $2}')
        WATCH wordListEnd
        if [[ "${wordListEnd}" == "" || ${wordListEnd} -gt ${wordCount} ]]; then
            wordListEnd=$wordCount
        fi
        WATCH wordListEnd
    else
        chapterNum="-"
        
        wordStart=$(echo ${selection} | awk -F"-" '{print $1}')
        WATCH wordStart
        wordListStart=$(getWordIndex "${wordStart}")

        wordEnd=$(echo ${selection} | awk -F"-" '{print $2}')
        WATCH wordEnd
        if [[ "${wordEnd}" == "" ]]; then
            wordListEnd=$wordCount
        else
            wordListEnd=$(getWordIndex "${wordEnd}")
        fi
    fi
    activeWordCount=$(($wordListEnd-$wordListStart+1))
}

runPractice()
{
    echo ""
    print -n "Ready to practice? Press any key when ready ... "
    stty -echo
    read -n1 userInput </dev/tty
    stty echo
    echo ""

    wordIndex=${wordListStart}
    WATCH wordIndex

    while true
    do
        if [[ ${wordIndex} -lt ${wordListStart} ]]; then
            break
        elif [[ ${wordIndex} -gt ${wordListEnd} ]]; then
            break
        fi

        lookupWordByIndex
        displayWord "Word #${wordIndex} means"
        captureUserInput
        echo ""

        while true
        do
            # Move to [n]ext word
            if [[ ${userInput} = [nN] ]]; then
                wordIndex=$((wordIndex+1))
                break
            # Move to [p]revious word
            elif [[ ${userInput} = [pP] ]]; then
                wordIndex=$((wordIndex-1))
                break
            # [R]epeat current word
            elif [[ ${userInput} = [rR] ]]; then
                displayWord "Word #${wordIndex} means"
                captureUserInput
                echo ""
            # Re[v]iew active word list
            elif [[ ${userInput} = [vV] ]]; then
                displayWordList
                captureUserInput
                echo ""
            # [S]how current word spelling
            elif [[ ${userInput} = [sS] ]]; then
                echo ""
                echo "Word #${wordIndex} is ${word}"
                captureUserInput
                echo ""
            # [L]ookup word meaning and pronunciation
            elif [[ ${userInput} = [lL] ]]; then
                userWord=""
                print -n "Enter word to be looked up: "
                read userWord </dev/tty
                lookupWord "${userWord}"
                displayWord  "${userWord} means"
                # Reset to current word
                lookupWordByIndex
                captureUserInput
                echo ""
            # Display [h]elp and statistics
            elif [[ ${userInput} = [hH] ]]; then
                displayAbout
                captureUserInput
                echo ""
            # E[x]it application
            elif [[ ${userInput} = [xX] ]]; then
                exitApp
            else
                echo ""
                echo "Invalid response."
                displayAbout
                captureUserInput
                echo ""
            fi
        done
    done
}

displayTestResults()
{
    echo ""
    echo "The test is now complete. Displaying results..."
    displayAbout | grep -v "Keyboard Menu"
    echo "Date [${testDate}]"
    echo ""
    echo "Answer Sheet: Score [${testCorrectCount}/${testTotalCount}]"
    cat ${SB_TMP_TEST_RESULTS} | awk -F: -v rsym="${SB_RIGHT_SYMBOL}" -v wsym="${SB_WRONG_SYMBOL}" '$1 ~ rsym {print $1 " " $2} $1 ~ wsym {print $1 " " $2 " (" $3 ")"}' | column -x
    echo ""
    echo "Practice Words:"
    cat ${SB_TMP_TEST_RESULTS} | grep -e "^${SB_WRONG_SYMBOL}" | awk -F: '{print $3}' | column -x
}

runTest()
{
    echo ""
    print -n "Ready for the test? Press any key when ready ... "
    stty -echo
    read -n1 userInput </dev/tty
    stty echo
    echo ""

    testDate=$(date)
    testTotalCount=${activeWordCount}
    testCorrectCount=0

    userResponse=""
    testValuation=""
    rm -f ${SB_TMP_TEST_RESULTS}

    wordIndex=${wordListStart}
    WATCH wordIndex

    while true
    do
        if [[ ${wordIndex} -lt ${wordListStart} ]]; then
            break
        elif [[ ${wordIndex} -gt ${wordListEnd} ]]; then
            break
        fi

        lookupWordByIndex
        echo ""
        echo "Reading out word #${wordIndex}..."
        pronounceWord
        print -n "Enter spelling: "
        read userResponse

        if [[ "${userResponse}" = [xX] ]]; then
            break
        elif [[ "${userResponse}" == "${word}" ]]; then
            testValuation="${SB_RIGHT_SYMBOL}:${userResponse}:${word}"
            testCorrectCount=$((testCorrectCount+1))
            echo "${testValuation}" | awk -F: '{print $1 " " $2}'
            echo "${testValuation}" >> ${SB_TMP_TEST_RESULTS}
        else
            testValuation="${SB_WRONG_SYMBOL}:${userResponse}:${word}"
            echo "${testValuation}" | awk -F: '{print $1 " " $2 " (" $3 ")"}'
            echo "${testValuation}" >> ${SB_TMP_TEST_RESULTS}
        fi

        wordIndex=$((wordIndex+1))
    done

    displayTestResults
}

initApp()
{
    # clear screen
    clear
    # switch audio output to 3.5 mm jack
    amixer -q cset numid=3 1
}

exitApp()
{
    # Switch audio output back to auto
    amixer -q cset numid=3 0

    # Cleanup temp files
    rm -f ${SB_TMP_WORD_ENTRY}
    rm -f ${SB_TMP_WORD_CLIP}
    rm -f ${SB_TMP_TEST_RESULTS}

    echo ""
    echo "Thank you for practicing for Spelling Bee."
    echo ""
    exit
}

################################################################
# Main Program
################################################################

runMode=$1
contestYear=$2
mode=$3
selection=$4

initApp

initWordList
displayAbout

if [[ ${runMode} == "practice" ]]; then
    runPractice
else
    runTest
fi

exitApp
