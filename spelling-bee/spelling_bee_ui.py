#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################
# Syntax :   sudo python spelling_bee_ui.py
################################################################

from Tkinter import *
import tkFont

# Setup window
tkWindow = Tk()
tkWindow.title("Spelling Bee")
tkWindow.geometry('1200x800')
Grid.rowconfigure(tkWindow, 0, weight=7)
Grid.rowconfigure(tkWindow, 1, weight=1)
Grid.columnconfigure(tkWindow, 0, weight=1)

# Setup menu bar
mnuMain = Menu(tkWindow)

mnuStart = Menu(mnuMain, tearoff=0)
mnuStart.add_command(label="Study", command=None)
mnuStart.add_command(label="Revise", command=None)
mnuStart.add_command(label="Test", command=None)
mnuStart.add_separator()
mnuStart.add_command(label="Exit", command=tkWindow.quit)
mnuMain.add_cascade(label="Start", menu=mnuStart)
tkWindow.configure(menu=mnuMain)


# Setup display area
frmDisplay = Frame(tkWindow)
frmDisplay.grid(row=0, column=0, sticky='nsew')
Grid.rowconfigure(frmDisplay, 0, weight=1)
Grid.columnconfigure(frmDisplay, 0, weight=1)
Grid.columnconfigure(frmDisplay, 1, weight=5)

fntWordbox = tkFont.Font(family='Helvetica', size=24)
lstWordbox = Listbox(frmDisplay, font=fntWordbox)
lstWordbox.grid(row=0, column=0, sticky='nsew')

scrollbar = Scrollbar(lstWordbox)
scrollbar.pack(side=RIGHT, fill=Y)
lstWordbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=lstWordbox.yview)

for wordIndex in range(40):
    lstWordbox.insert(wordIndex, "Word" + str(wordIndex))
lstWordbox.select_set(2)

txtInfobox = Text(frmDisplay)
txtInfobox.grid(row=0, column=1, sticky='nsew')

# Setup tool bar
frmToolbar = Frame(tkWindow)
frmToolbar.grid(row=1, column=0, sticky='nsew')
fntToolbar = tkFont.Font(family='Helvetica', size=36, weight='bold')

# Setup toolbar buttons
for rowIndex in range(1):
    Grid.rowconfigure(frmToolbar, rowIndex, weight=1)
    for colIndex in range(4):
        Grid.columnconfigure(frmToolbar, colIndex, weight=1)
        btnToolbar = Button(frmToolbar, font=fntToolbar)
        btnToolbar.grid(row=rowIndex, column=colIndex, sticky='nsew')

        if colIndex == 0:
            btnToolbar["text"] = "◀"
        elif colIndex == 1:
            btnToolbar["text"] = "⟳"
        elif colIndex == 2:
            btnToolbar["text"] = "▶"
        elif colIndex == 3:
            btnToolbar["text"] = "\\ä\\"

tkWindow.mainloop()

########################################################################
# Debugging Commands
########################################################################
'''
cd $PROJ
sudo python spelling_bee_ui.py
'''
