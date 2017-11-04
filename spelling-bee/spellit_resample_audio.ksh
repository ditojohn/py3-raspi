#!/usr/bin/ksh
# Reference: https://libav.org/documentation/avconv.html#Video-and-Audio-file-format-conversion

. ./project_setup.cfg
rc=0

srcDir=$DATA/download

tgtSampleRate=44100
tgtDir=$DATA/download/audio/resampled
tgtArchDir=$DATA/download/audio/original

# Scan for downloaded wav files
for srcFile in ${srcDir}/*.wav
do
    fileName=$(basename ${srcFile} .wav)

    print "\n--------------------------"
    print "Converting ${fileName}.wav ..."
    avconv -i ${srcDir}/${fileName}.wav -ar ${tgtSampleRate} ${tgtDir}/${fileName}.mp3
    rc=$?
    if [[ ${rc} -eq 0 ]]
    then
        echo ">> Conversion complete for ${fileName}.wav"
        mv ${srcDir}/${fileName}.wav ${tgtArchDir}/${fileName}.wav
        echo ">> Archived ${fileName}.wav"
    else
        echo ">> Conversion failed for ${fileName}"
    fi

done

# Scan for downloaded mp3 files
for srcFile in ${srcDir}/*.mp3
do
    fileName=$(basename ${srcFile})

    print "\n--------------------------"
    print "Resampling ${fileName} ..."
    avconv -i ${srcDir}/${fileName} -ar ${tgtSampleRate} ${tgtDir}/${fileName}
    rc=$?
    if [[ ${rc} -eq 0 ]]
    then
        echo ">> Resampling complete for ${fileName}"
        mv ${srcDir}/${fileName} ${tgtArchDir}/${fileName}
        echo ">> Archived ${fileName}"
    else
        echo ">> Resampling failed for ${fileName}"
    fi

done
