#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : fileio.py
# Description : Generic file handling library
# Author      : Dito Manavalan
# Date        : 2016/03/17
#--------------------------------------------------------------------------------------------------

import os, errno
import uuid
import time
import glob
import codecs
import pygame


def download(connectionPool, sourceURL, targetFileName):
    fileData = connectionPool.request('GET', sourceURL).data
    targetFile = open(targetFileName, "wb")
    targetFile.write(fileData)
    targetFile.close()


def read(inputFileName):
    inputFile = codecs.open(inputFileName, mode='r', encoding='utf-8')
    fileText = inputFile.read()
    inputFile.close()
    return fileText


def write(outputFileName, outputText):
    outputFile = codecs.open(outputFileName, mode='w', encoding='utf-8')
    outputFile.write(outputText)
    outputFile.close()


def append(outputFileName, outputText):
    outputFile = codecs.open(outputFileName, mode='a', encoding='utf-8')
    outputFile.write(outputText)
    outputFile.close()


def set_audio_output(audioOutput):
    if audioOutput.lower() == 'hdmi':
        os.system("amixer -q cset numid=3 2")
    elif audioOutput.lower() == 'speaker':
        os.system("amixer -q cset numid=3 1")
    elif audioOutput.lower() == 'auto':
        os.system("amixer -q cset numid=3 0")


def play(fileName, audioOutput, loopCount, loopDelaySec):
    set_audio_output(audioOutput)

    for loopIndex in range (0, loopCount):
        pygame.mixer.init()
        pygame.mixer.music.load(fileName)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy() == True:
            continue
        pygame.mixer.stop()
        pygame.mixer.quit()

        if loopIndex != (loopCount - 1):
            time.sleep(loopDelaySec)

    set_audio_output('auto')


def delete(fileName):
    try:
        os.remove(fileName)
    except OSError as e:            # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise                   # re-raise exception if a different error occured


def delete_temp():
    for tempFileName in glob.glob("dlfile_ts*_rnd*.tmp"):
        delete(tempFileName)


def play_url(connectionPool, sourceURL, audioOutput, loopCount, loopDelay):
    tempFileName = "dlfile_ts{TIMESTAMP}_rnd{RAND}.tmp".format(TIMESTAMP=time.strftime("%Y%m%d%H%M%S"), RAND=str(uuid.uuid4()))
    download(connectionPool, sourceURL, tempFileName)
    play(tempFileName, audioOutput, loopCount, loopDelay)
    delete_temp()


def stream_wav(sourceURL, audioOutput):
    # Reference:
    # http://people.csail.mit.edu/hubert/pyaudio/#examples
    # http://stackoverflow.com/questions/33320218/get-an-audio-file-with-http-get-and-then-play-it-in-python-3-tts-in-python-3

    from urllib import urlopen
    import wave
    import pyaudio

    WAV_CHUNK_SIZE = 4096

    set_audio_output(audioOutput)

    r = urlopen(sourceURL)
    wf = wave.open(r, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    data = wf.readframes(WAV_CHUNK_SIZE)

    while data != '':
        stream.write(data)
        data = wf.readframes(WAV_CHUNK_SIZE)

    stream.stop_stream()
    stream.close()
    p.terminate()

    set_audio_output('auto')


########################################################################
# Sample application to test the python module
########################################################################

'''
cd ~/projects/raspi/common/rpimod/stdio
sudo python fileio.py
'''

'''
import urllib3

DICT_USER_AGENT = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}
connectionPool = urllib3.PoolManager(10, headers=DICT_USER_AGENT)

SAMPLE_MP3_URL = "http://ssl.gstatic.com/dictionary/static/sounds/de/0/cloud.mp3"
SAMPLE_WAV_URL = "http://media.merriam-webster.com/soundc11/c/cloud001.wav"

#play_url(connectionPool, SAMPLE_MP3_URL, 'Speaker', 1, 1)
#play_url(connectionPool, SAMPLE_WAV_URL, 'Speaker', 1, 1)

stream_wav(SAMPLE_WAV_URL, 'Speaker')

connectionPool.clear()
'''
