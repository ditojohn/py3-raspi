#!/usr/bin/ksh

################################################################
# Syntax :	ksh spelling_bee.ksh contestYear mode chapterNum|wordRange
# where		contestYear is the year of the contest in YYYY format
#			mode is chapter or word.
#				In chapter mode, the next argument is the chapter number
#					chapterNum is the chapter of the word list to be practiced.
#					Default chapter size is 50 words.
#				In word mode, the next argument is the word range
#					wordRange is the range of words in the word list to be practiced.
# Example:	ksh spelling_bee.ksh 2016 chapter 7
# 			ksh spelling_bee.ksh 2016 word 10-15
################################################################

################################################################
####    Korn Shell function to read one character from
####    standard input (STDIN) without requiring a carriage
####    return.  This function would typically be used in a
####    shell script to detect a key press.
####
####    Load this file into your current environment as follows:
####
####    . ./getch
####
####    Thats "dot-space-dot-slash-getch-dot-sh"
####
####    You will then be able to issue the command "getch"
####    from your current environment to retrieve one character.
####
####    SYNTAX: getch [-q]
####
####                   -q = quiet mode, no output
####
####    AUTHOR: Dana French (dfrench@mtxia.com)
####
####    See http://www.mtxia.com/js/Downloads/Scripts/Korn/Functions/visualSelect/index.shtml
####    visualSelect menu system for a full implementation of "getch" 
####    capturing function keys, arrow keys, and other cursor movement keys.
#### 
################################################################
function getch {
    typeset TMP_GETCH
    typeset STAT_GETCH="0"
    stty raw
    TMP_GETCH=`dd bs=1 count=1 2> /dev/null`
    STAT_GETCH="${?}"
    stty -raw

    if [[ "_${1}" != "_-q" ]]
    then
        print -r -- "${TMP_GETCH}"
    fi
    return ${STAT_GETCH}
}

getXMLValues()
{
	xmlString="$1"
	xmlElement="$2"
	xmlTopN="$3"

	xmlString="$(echo "${xmlString}" | sed "s/<${xmlElement}>/\n<${xmlElement}>/g" | grep -i "<${xmlElement}>")"
	echo "${xmlString}" | while read -r line
	do
		echo "${line}" | sed -n "/${xmlElement}/{s/.*<${xmlElement}>\(.*\)<\/${xmlElement}>.*/\1/;p}" | cut -d ':' -f 2 | sed "s/^/• /g" | sed "s/<[/a-zA-Z_]*>//g"
	done | head -n ${xmlTopN}
}

lookupWord()
{
	word="$1"

	#Sample dictionary API URL - http://www.dictionaryapi.com/api/v1/references/collegiate/xml/test?key=cbbd4001-c94d-493a-ac94-7268a7e41f6f
	dictURL="http://www.dictionaryapi.com/api/v1/references/collegiate/xml"
	dictKey="key=cbbd4001-c94d-493a-ac94-7268a7e41f6f"
	clipBase="http://media.merriam-webster.com/soundc11"

	# Get dictionary entry
	dictXMLEntry=$(wget -qO- "${dictURL}/${word}?${dictKey}")

	#wordClip=$(echo ${dictXMLEntry} | sed -n 's:.*<wav>\(.*\)</wav>.*:\1:p')	# Pick default (last) sound clip reference
	wordClip=$(getXMLValues "${dictXMLEntry}" "wav" "1")						# Pick first sound clip reference
	wordClipFolder=$(echo ${wordClip} | cut -c 1 )
	wordClipURL=$(echo ${clipBase}/${wordClipFolder}/${wordClip})

	# Pronounce dictionary entry
	wget -qO- ${wordClipURL} | aplay -q;

	# Lookup dictionary entry
	wordMeaning=$(getXMLValues "${dictXMLEntry}" "dt" "3")						# Pick top three meanings
	echo "${wordMeaning}"
}

displayWord()
{
	echo ""
	echo "Word #${wordIndex} means"
	#print -n " [${word}]"
	lookupWord "${word}"
}

displayWordList()
{
	echo ""
	echo "Review Chapter [${chapterNum}/${chapterCount}] Words [${wordListStart}-${wordListEnd}]"
	head -n ${wordListEnd} ${wordList} | tail -n ${activeWordCount} | column -x
}

displayAbout()
{
	echo ""
	echo "Spelling Bee ${contestYear}"
	echo "Word Count [${wordCount}] Chapter [${chapterNum}/${chapterCount}] Words [${wordListStart}-${wordListEnd}]"
	echo "Keyboard Menu: ${keyboardMenu}"
}

captureUserInput()
{
	echo ""
	print -n "> "
	read userInput </dev/tty
	#echo "User input: ${userInput}"
}

# Main program
chapterSize=50
keyboardMenu="[N]ext [R]epeat Re[v]iew [H]elp E[x]it"

contestYear=$1
mode=$2

wordList=$DATA/spelling_bee_${contestYear}.txt
wordCount=$(wc -l ${wordList} | awk '{print $1}')
chapterCount=$((($wordCount+$chapterSize-1)/$chapterSize))		# Find number of chapters by computing the ceiling

if [[ ${mode} == "chapter" ]]; then
	chapterNum=$3
	wordListStart=$((($chapterNum-1)*$chapterSize+1))
	wordListEnd=$(($wordListStart+$chapterSize-1))
	if [[ ${wordListEnd} -gt ${wordCount} ]]; then
		wordListEnd=wordCount
	fi
else
	chapterNum="-"
	wordListStart=$(echo $3 | cut -d "-" -f 1)
	wordListEnd=$(echo $3 | cut -d "-" -f 2)
	if [[ ${wordListEnd} -gt ${wordCount} ]]; then
		wordListEnd=wordCount
	fi
fi
activeWordCount=$(($wordListEnd-$wordListStart+1))

displayAbout
echo ""
print -n "Ready to practice? Press enter when ready ... "
#read userInput </dev/tty
getch -q
echo ""

wordIndex=0
while read word
do
	wordIndex=$((wordIndex+1))
	if [[ ${wordIndex} -lt ${wordListStart} ]]; then
		continue
	elif [[ ${wordIndex} -gt ${wordListEnd} ]]; then
		break
	fi

	displayWord
	captureUserInput

	while true
	do
		if [[ ${userInput} = [nN] ]]; then
			break
		elif [[ ${userInput} = [rR] ]]; then
			displayWord
			captureUserInput
		elif [[ ${userInput} = [vV] ]]; then
			displayWordList
			captureUserInput
		elif [[ ${userInput} = [hH] ]]; then
			displayAbout
			captureUserInput
		elif [[ ${userInput} = [xX] ]]; then
			echo ""
			echo "Thank you for practicing for Spelling Bee."
			echo ""
			exit
		else
			echo ""
			echo "Invalid response."
			displayAbout
			captureUserInput
		fi
	done
done < ${wordList}

echo ""
echo "Thank you for practicing for Spelling Bee."
echo ""