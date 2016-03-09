#!/usr/bin/ksh
. ./project_setup.cfg

wordlist=$PROJ/spellit_get_words_list.dat

sourceURL="http://www.thefreedictionary.com/@word@"

while read word;
do

    wordSearchURL=$(echo ${sourceURL} | sed "s/@word@/${word}/g")
    wordSearchResult=$(wget -qO- "${wordSearchURL}")

    audioFound=$(echo ${wordSearchResult} | grep "data-snd=\"en\/US" | wc -l)

    if [[ ${audioFound} -gt 0 ]]
    then
        echo "Downloading audio for word: ${word}"
        wordClipID=$(echo ${wordSearchResult} | sed "s/.*data-snd=\"en\/US\/\([^ \"]*\)\".*/\1/g")
        wordClipURL="http://img2.tfd.com/pron/mp3/en/US/${wordClipID}.mp3"
        echo ${wordClipURL}

        #wget -qO- "${wordClipURL}" > $PROJ/sb_${word}.mp3
        #echo "Touching definition file for word: ${word}"
        #touch $PROJ/sb_${word}.dat
    else
        echo "No audio located for word: ${word}"
    fi

done < ${wordlist}
