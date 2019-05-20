from tkinter import *
from tkinter import ttk

from .component import Component
from .canvas import MainCanvas

from PIL import Image, ImageTk
import pdf2image
import os

class PDFViewer(Component):
    def __init__(self, parent):
        super().__init__(parent, 'PDFViewer')
        # Current PDF Path
        self.path = None
        # Main PDF Canvas
        self.canvas = MainCanvas(self)
        # PDF Page Navigator
        self.navigator = Navigator(self)
        # Grid Configuration
        self.canvas.grid(row=0, column=0, sticky=(N,S,E,W))
        self.navigator.grid(row=1, column=0)
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=0)
        self.frame.columnconfigure(0, weight=1)
        # Listeners
        self.addListener('<OpenPDF>', self.handleOpenPDF)
        self.addListener('<PageChange>', self.handlePageChange)
        self.addListener('<PleaseUpdateRects>', self.handlePleaseUpdateRects)
        # Set Initial State
        self.setState(
            curPage=0, totalPage=0,
        )
    
    def requestRects(self):
        event = dict(name='<RequestRects>', page=self.state['curPage'])
        self.emitEvent('MainFrame', event)
    
    def handleOpenPDF(self, event):
        filename = event['filename']
        pdfpath = os.path.normpath(os.path.join(os.path.dirname(__file__), '../data/%s.pdf' % filename))
        if self.path == pdfpath:
            return None
        self.path = pdfpath
        # Read PDF images
        try:
            images = pdf2image.convert_from_path(pdfpath)
            curPage, totalPage = 1, len(images)
            self.setState(
                curPage=curPage, totalPage=totalPage,
                images=images
            )
            self.requestRects()
        except:
            print('PDFViewer: cannot open PDF')
    
    def handlePageChange(self, event):
        self.setState(curPage=event['newPage'])
        self.requestRects()
    
    def handlePleaseUpdateRects(self, event):
        self.requestRects()
    
    def afterSetState(self):
        curPage, totalPage = self.state['curPage'], self.state['totalPage']
        if curPage > 0:
            image = self.state['images'][curPage - 1]
        else:
            image = None
        self.navigator.setState(curPage=curPage, totalPage=totalPage)
        self.canvas.setState(image=image, page=curPage)


class Navigator(Component):
    def __init__(self, parent):
        super().__init__(parent, 'Navigator')
        # Navigation Buttons
        self.prevButton = ttk.Button(self.frame, text='prev')
        self.nextButton = ttk.Button(self.frame, text='next')
        # Label for Page Number
        self.pageStrVar = StringVar()
        self.pageLabel = ttk.Label(self.frame, textvariable=self.pageStrVar)
        # Grid Configuration
        self.prevButton.grid(row=0, column=0)
        self.nextButton.grid(row=0, column=2)
        self.pageLabel.grid(row=0, column=1)
        # Bindings
        self.prevButton.configure(command=self.onClickPrev)
        self.nextButton.configure(command=self.onClickNext)
        # Set Initial State
        self.setState(curPage=0, totalPage=0)
    
    def afterSetState(self):
        self.pageStrVar.set('%d / %d' % 
            (self.state['curPage'], self.state['totalPage'])
        )
    
    def onPageChange(self, newPage):
        event = dict(name='<PageChange>', newPage=newPage)
        self.emitEvent('PDFViewer', event)
    
    def onClickPrev(self):
        curPage, totalPage = self.state['curPage'], self.state['totalPage']
        if curPage > 1:
            self.onPageChange(curPage - 1)
    
    def onClickNext(self):
        curPage, totalPage = self.state['curPage'], self.state['totalPage']
        if curPage < totalPage:
            self.onPageChange(curPage + 1)

