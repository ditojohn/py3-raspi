#!/usr/bin/env python
# -*- coding: utf-8 -*-

#--------------------------------------------------------------------------------------------------
# File name   : output.py
# Description : Generic output handling library
# Author      : Dito Manavalan
# Date        : 2016/01/28
#--------------------------------------------------------------------------------------------------

import math

# Display a list as evenly spaced columns
OUT_MARGIN_WIDTH = 4                                    # set margin width to 4 characters

def columnize(list, numCols):
    elementCount = len(list)
    colCount = numCols
    rowCount = int(math.ceil(float(elementCount)/float(colCount)))

    elementMargin = OUT_MARGIN_WIDTH                               

    if len(list) > 0:
        elementMaxLength = max([len(unicode(element, 'utf-8')) for element in list])

        for rowIndex in range(0, rowCount):
            elementIndex = rowIndex
            for colIndex in range(0, colCount):
                if elementIndex < elementCount:
                    print unicode(list[elementIndex], 'utf-8').ljust(elementMaxLength + elementMargin, ' '),
                    elementIndex += rowCount
            print ""                                    # print row break
