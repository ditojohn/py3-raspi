#!/usr/bin/ksh
. ./project_setup.cfg

wordlist=$PROJ/spellit_get_words_list.dat

sourceURL="http://www.oxforddictionaries.com/us/definition/american_english/@word@?searchDictCode=all"

while read word;
do

    wordSearchURL=$(echo ${sourceURL} | sed "s/@word@/${word}/g")
    wordSearchResult=$(wget -qO- "${wordSearchURL}")

    audioFound=$(echo ${wordSearchResult} | grep "data-src-mp3=" | wc -l)

    if [[ ${audioFound} -gt 0 ]]
    then
        echo "Downloading audio for word: ${word}"
        wordClipURL=$(echo ${wordSearchResult} | sed "s/.*data-src-mp3=\"\([^ \"]*\)\".*/\1/g")
        wget -qO- "${wordClipURL}" > $PROJ/sb_${word}.mp3
        echo "Touching definition file for word: ${word}"
        touch $PROJ/sb_${word}.dat
    else
        echo "No audio located for word: ${word}"
    fi

done < ${wordlist}
