#!/usr/bin/env python

#-----------------------------------------------------------
# File name   : pilot_thread_io.py
# Description : Input/Output program to read input and
#               display output using different threads
# Author      : Dito
# E-mail      : 
# Website     : 
# Date        : 2015/11/24
#-----------------------------------------------------------

import threading
import time

exitFlag = 0

inProcessFlag = True
responseDelay = 3
userResponse = "Start"

class inputThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        print "Starting " + self.name
        capture_input(self.name, self.counter)
        print "Exiting " + self.name

def capture_input(threadName, counter):
    global inProcessFlag
    global responseDelay
    global userResponse
    while counter:
        if exitFlag:
            threadName.exit()
        print "Current user response: ", userResponse
        userResponse = raw_input("Enter your response: ")
        print "New user response: %s\n\n" % (userResponse)
        counter -= 1
    time.sleep(responseDelay + 1)
    inProcessFlag = False

class outputThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        print "Starting " + self.name
        display_output(self.name)
        print "Exiting " + self.name

def display_output(threadName):
    global inProcessFlag
    global responseDelay
    global userResponse
    while inProcessFlag:
    	time.sleep(responseDelay)
        if exitFlag:
            threadName.exit()
        print "Write thread: User response %s" % (userResponse)

# Create new threads
threadRead = inputThread(1, "Thread-Read", 3)
threadWrite = outputThread(2, "Thread-Write")

# Start new Threads
threadRead.start()
threadWrite.start()

print "Exiting Main Thread"
