#!/usr/bin/ksh
. ./project_setup.cfg

wordlist=$PROJ/spellit_get_words_list.dat

sourceURL="http://dictionary.reference.com/browse/@word@"

while read word;
do

    wordSearchURL=$(echo ${sourceURL} | sed "s/@word@/${word}/g")
    wordSearchResult=$(wget -qO- "${wordSearchURL}")

    audioFound=$(echo ${wordSearchResult} | grep "audio/mpeg" | wc -l)

    if [[ ${audioFound} -gt 0 ]]
    then
        echo "Downloading audio for word: ${word}"
        wordClipURL=$(echo ${wordSearchResult} | sed "s/.*<source src=\"\([^ \"]*\)\" type=\"audio\/mpeg.*/\1/g")
        wget -qO- "${wordClipURL}" > $PROJ/sb_${word}.mp3
        echo "Touching definition file for word: ${word}"
        touch $PROJ/sb_${word}.dat
    else
        echo "No audio located for word: ${word}"
    fi

done < ${wordlist}
