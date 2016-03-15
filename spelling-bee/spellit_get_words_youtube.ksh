#!/usr/bin/ksh
. ./project_setup.cfg

html_select_tag ()
{
    tag="$1"
    code="$2"

    escTag=$(echo "${tag}" | sed 's/\"/\\\"/g')

    # Split all occurrences of the tag as separate lines
    splitCode=$(echo "${code}" | sed "s/${escTag}/\n${escTag}/g" | grep "${escTag}")

    echo "$splitCode"
}

wordlist=$DATA/spellit_get_words_list.dat

searchAgent="Mozilla/6.0 (Macintosh; I; Intel Mac OS X 11_7_9; de-LI; rv:1.9b4) Gecko/2012010317 Firefox/10.0a4"
searchURL="http://www.google.com/search?hl=en&q=YouTube+Pronunciation+Guide+How+to+Pronounce+@word@"

#while read word;
echo "Buckwagon" | while read word;
do
    echo ""
    echo "Searching for word: ${word}"

    wordSearchURL=$(echo ${searchURL} | sed "s/@word@/${word}/g")
    echo "Search URL: ${wordSearchURL}"
    
    wordSearchHTML=$(wget -qO- -U "${searchAgent}" "${wordSearchURL}")
    filteredHTML=$(html_select_tag "<div class=\"g\">" "${wordSearchHTML}")
    selectedHTML=$(echo "${filteredHTML}" | grep "Uploaded by Pronunciation Guide" | grep -i "This video shows you <em>how to pronounce ${word}")

    videoURL=$(echo "${selectedHTML}" | perl -pe 's|.*(<a href="(.*?)" data-ved).*|\2|' | head -1)
    echo "Video URL: ${videoURL}"

    #echo "Sleeping ..."
    #sleep 5

#done < ${wordlist}
done
