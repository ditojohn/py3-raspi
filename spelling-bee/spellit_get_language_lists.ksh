#!/usr/bin/ksh
. ./project_setup.cfg

year=2016

for lang in \
"Latin" \
"Arabic" \
"Asian Languages" \
"French" \
"Eponyms" \
"German" \
"Slavic Languages" \
"Dutch" \
"Old English" \
"New World Languages" \
"Japanese" \
"Greek" \
"Italian" \
"Spanish"
do
    listType=$(echo ${lang} | tr [A-Z] [a-z] | tr ' ' '_')

    listURL="http://myspellit.com/print_${listType}.html"
    listOutType="${year}-$(echo ${listType} | tr '_' '-')"

    echo "Downloading ${listOutType} list..."
    listHTML=$(wget -qO- "${listURL}")

    # Study Words
    echo "${listHTML}" | awk '/section word study/,/<\/div>/ {print $0}' | grep "<li>" | sed 's/^.*<li>//g' | sed 's/<\/li>.*$//g' | sed 's/ <span.*\/span>.*$//g' > data/spelling_bee_${listOutType}.txt

    # Challenge Words
    echo "${listHTML}" | awk '/section word challenge/,/<\/div>/ {print $0}' | grep "<li>" | sed 's/^.*<li>//g' | sed 's/<\/li>.*$//g' | sed 's/ <span.*\/span>.*$//g' > data/spelling_bee_${listOutType}-challenge.txt
done