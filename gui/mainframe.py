from tkinter import *
from tkinter import ttk
from tkinter import filedialog

from .component import Component
from .pdfviewer import PDFViewer
from .controlpanel import ControlPanel

import os
import re

class MainFrame(Component):
    def __init__(self, parent):
        super().__init__(parent, 'MainFrame')
        # Left Frame: PDF Viewer
        self.filename = 'lecture1'
        # viewer
        self.viewer = PDFViewer(self)
        self.viewer.configure(
            width=300, height=500,
            borderwidth=4, relief='ridge'
        )
        # Right Frame: Control Panel
        self.panel = ControlPanel(self)
        self.panel.configure(
            width=300, height=500,
        )
        # Status Bar
        self.status = StatusBar(self)
        self.status.configure(
            height=30
        )
        # Listeners
        self.addListener('<RequestOpenPDF>', self.handleRequestOpenPDF)
        # Grid Configuration
        self.viewer.grid(row=0, column=0, sticky=NSEW)
        self.panel.grid(row=0, column=1, sticky=NSEW)
        self.status.grid(row=1, column=0, columnspan=2, sticky=NSEW)
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=0)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=0, minsize=460)
        # Bindings
        self.frame.bind('<Configure>', self.print)
        # Open Initial PDF
        self.openPDF(self.filename)
    
    def handleRequestOpenPDF(self, event):
        self.openPDF(self.filename)
    
    def openPDF(self, filename):
        event = dict(
            name='<OpenPDF>',
            filename=filename
        )
        self.emitEvent('MainFrame', event)
    
    def print(self, event):
        print(event.width, event.height)


class StatusBar(Component):
    def __init__(self, parent):
        super().__init__(parent, 'StatusBar')
        # Status Label
        self.statusText = StringVar()
        self.statusText.set('Ready')
        self.status = ttk.Label(self.frame)
        self.status.configure(textvariable=self.statusText)
        # Listeners
        self.addListener('<StatusUpdate>', self.handleStatusUpdate)
        # Grid Configuration
        self.status.grid(row=0, column=0, sticky=W)
    
    def handleStatusUpdate(self, event):
        self.statusText.set(event['message'])