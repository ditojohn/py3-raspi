#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : fileio.py
# Description : Generic file handling library
# Author      : Dito Manavalan
# Date        : 2016/03/17
#--------------------------------------------------------------------------------------------------

import os, errno
import sys
import uuid
import time
import glob
import re
import logging
from datetime import datetime
from pathlib import Path
import platform

sys.path.insert(0, "../../..")
import common.rpimod.stdio.output as coutput

import codecs
from pydub.utils import mediainfo
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


# Set to True to turn debug messages on
#APP_DEBUG_MODE_ENABLED = True
APP_DEBUG_MODE_ENABLED = False


################################################################
# Configuration
################################################################

alsaAudioOutputConfig = {
    'JMQuad' : { 'speaker': 'plughw:0,0', 'hdmi': 'plughw:0,7', 'auto': ''},
    'RaspberryPi' : { 'speaker': '', 'hdmi': '', 'auto': ''}
}


################################################################
# File handlers
################################################################


def cleanse_filename(fileName):
    cleanFileName = re.sub('[ /]', ' ', fileName.lower(), flags=re.IGNORECASE)
    cleanFileName = cleanFileName.replace("\\", " ")
    cleanFileName = re.sub('[ ]+', ' ', cleanFileName)
    cleanFileName = cleanFileName.strip().replace(" ", "_")
    return cleanFileName


def make_directory(directoryList):
    for directory in directoryList:
        Path(directory).mkdir(parents=True, exist_ok=True)


def find_file(fileName, directoryList, sizeLimit=0):
    fullFileName = None
    for directory in directoryList:
        checkFileName = directory + fileName
        if os.path.isfile(checkFileName) and os.path.getsize(checkFileName) > sizeLimit:
            fullFileName = checkFileName
            break
    return fullFileName


def download(connectionPool, sourceURL, targetFileName):
    coutput.print_watcher("sourceURL")

    fileData = connectionPool.request('GET', sourceURL).data
    targetFile = open(targetFileName, "wb")
    targetFile.write(fileData)
    targetFile.close()


def delete(fileName):
    try:
        os.remove(fileName)
    except OSError as e:            # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise                   # re-raise exception if a different error occured


def read(inputFileName):
    inputFile = codecs.open(inputFileName, mode='r', encoding='utf-8')
    fileText = inputFile.read()
    inputFile.close()
    return fileText


def write(outputFileName, outputText):
    outputFile = codecs.open(outputFileName, mode='w', encoding='utf-8')
    print(outputText, file=outputFile)
    outputFile.close()


def append(outputFileName, outputText):
    outputFile = codecs.open(outputFileName, mode='a', encoding='utf-8')
    print(outputText, file=outputFile)
    outputFile.close()


def log(outputFileName, outputEntry, outputText=None):
    outputFile = codecs.open(outputFileName, mode='a', encoding='utf-8')
    logText="{}: {}".format(datetime.now(), outputEntry)
    print(logText, file=outputFile)
    if outputText is not None:
        print(outputText, file=outputFile)
    outputFile.close()


# Print to stdout and write to file simultaneously
def display_write(outputFileName, outputText):
    outputFile = codecs.open(outputFileName, mode='w', encoding='utf-8')
    print(outputText)
    print(outputText, file=outputFile)
    outputFile.close()


# Print to stdout and append to file simultaneously
def display_append(outputFileName, outputText):
    outputFile = codecs.open(outputFileName, mode='a', encoding='utf-8')
    print(outputText)
    print(outputText, file=outputFile)
    outputFile.close()


# Print to stdout and write to file handle simultaneously
def display_write_file(outputFile, outputText):
    print(outputText)
    print(outputText, file=outputFile)


################################################################
# Multimedia handlers
################################################################

def set_audio_output(audioOutput):
    # Reference:
    # https://wiki.archlinux.org/index.php/Advanced_Linux_Sound_Architecture/Troubleshooting#HDMI_Output_does_not_work

    '''
    if audioOutput.lower() == 'hdmi':
        os.system("amixer -q cset numid=3 2")
    elif audioOutput.lower() == 'speaker':
        os.system("amixer -q cset numid=3 1")
    elif audioOutput.lower() == 'auto':
        os.system("amixer -q cset numid=3 0")
    '''

    pass

def get_audio_output(audioOutput):
    # Reference:
    # https://wiki.archlinux.org/index.php/Advanced_Linux_Sound_Architecture/Troubleshooting#HDMI_Output_does_not_work

    coutput.print_watcher("alsaAudioOutputConfig")
    coutput.print_watcher("platform.node()")
    coutput.print_watcher("audioOutput.lower()")
    coutput.print_watcher("alsaAudioOutputConfig[platform.node()][audioOutput.lower()]")
    return alsaAudioOutputConfig[platform.node()][audioOutput.lower()]


def play_legacy(fileName, audioOutput, loopCount, loopDelaySec):
    # Reference:
    # https://www.pygame.org/docs/ref/mixer.html#pygame.mixer.init
    # http://techqa.info/programming/question/27745134/how-can-i-extract-the-metadata-and-bitrate-info-from-a-audio/video-file-in-python

    try:
        #Enable for RaspberryPi
        coutput.print_debug("Executing set_audio_output")
        set_audio_output(audioOutput)

        coutput.print_debug("Executing mediainfo")
        fileInfo = mediainfo(fileName)
        
        coutput.print_watcher("fileName")
        coutput.print_watcher("fileInfo['sample_rate']")
        coutput.print_watcher("fileInfo['bits_per_sample']")
        coutput.print_watcher("fileInfo['channels']")

        for loopIndex in range (0, loopCount):
            # Syntax: init(frequency=22050, size=-16, channels=2, buffer=4096)
            pygame.mixer.init()
            #pygame.mixer.init(frequency=long(float(fileInfo['sample_rate'])), channels=int(fileInfo['channels']))

            coutput.print_debug("Executing pygame.mixer.music.load")
            pygame.mixer.music.load(fileName)

            coutput.print_debug("Executing pygame.mixer.music.play")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() == True:
                continue
            time.sleep(0.06)            # introduce delay to ensure that the end of the audio is not clipped during playback
            
            coutput.print_debug("Executing pygame.mixer.stop")
            pygame.mixer.stop()
            coutput.print_debug("Executing pygame.mixer.quit")
            pygame.mixer.quit()

            if loopIndex != (loopCount - 1):
                time.sleep(loopDelaySec)

        set_audio_output('auto')
    except:
        coutput.print_err("Unable to play audio from " + fileName)
        coutput.print_watcher("sys.exc_info()")


def play(fileName, audioOutput, loopCount, loopDelaySec):
    # Reference:
    # https://realpython.com/playing-and-recording-sound-python/#playing-audio-files
    # https://askubuntu.com/questions/115369/how-to-play-mp3-files-from-the-command-line
    # https://www.ffmpeg.org/ffplay.html
    # https://www.ffmpeg.org/ffmpeg-devices.html#Examples-8
    # Use aplay -L to find audio output device. e.g. HDMI is plughw

    playCommand = "ffmpeg -f alsa {outputdevice} -loglevel quiet -i {filename} 2>/dev/null".format(outputdevice=get_audio_output(audioOutput), filename=fileName)

    try:

        coutput.print_watcher("fileName")

        for loopIndex in range (0, loopCount):
            coutput.print_debug("Executing play")
            coutput.print_watcher("playCommand")
            os.system(playCommand)

            if loopIndex != (loopCount - 1):
                time.sleep(loopDelaySec)

    except:
        coutput.print_err("Unable to play audio from " + fileName)
        coutput.print_watcher("sys.exc_info()")


def play_url(connectionPool, sourceURL, audioOutput, loopCount, loopDelay):

    try:
        coutput.print_debug("Executing set_audio_output")
        set_audio_output(audioOutput)

        if '.mp3' in sourceURL or '.wav' in sourceURL:
            tempFileName = "dlfile_ts{TIMESTAMP}_rnd{RAND}.tmp".format(TIMESTAMP=time.strftime("%Y%m%d%H%M%S"), RAND=str(uuid.uuid4()))
            download(connectionPool, sourceURL, tempFileName)
            play(tempFileName, audioOutput, loopCount, loopDelay)
            delete(tempFileName)
        else:
            coutput.print_err("Unable to play audio from " + sourceURL)

        set_audio_output('auto')
    except:
        coutput.print_err("Unable to play audio from " + sourceURL)


def stream_wav(sourceURL, audioOutput):
    # Reference:
    # http://people.csail.mit.edu/hubert/pyaudio/#examples
    # http://stackoverflow.com/questions/33320218/get-an-audio-file-with-http-get-and-then-play-it-in-python-3-tts-in-python-3

    from urllib.request import urlopen
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


################################################################
# Log handlers
#
# References:
# https://docs.python-guide.org/writing/logging/
# https://www.loggly.com/ultimate-guide/python-logging-basics/
# https://realpython.com/python-logging/
# https://docs.python.org/3/library/logging.html
# https://docs.python.org/3/library/logging.html#logrecord-attributes
#
# Usage:
# logger = setup_logger('first_logger', 'first_logfile.log')
# logger.info('This is just info message')
################################################################

#logFormatter = logging.Formatter('%(levelname)s:%(asctime)s [%(module)s:%(funcname)s:%(processName)s] %(message)s')
logFormatter = logging.Formatter('%(levelname)s:%(asctime)s [%(module)s:%(processName)s] %(message)s')

def setup_logger(logName, logFile, logLevel=logging.INFO):

    logHandler = logging.FileHandler(logFile)        
    logHandler.setFormatter(logFormatter)

    logger = logging.getLogger(logName)
    logger.setLevel(logLevel)
    logger.addHandler(logHandler)

    return logger


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
