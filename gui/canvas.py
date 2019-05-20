from tkinter import *
from tkinter import ttk

from .component import Component
from PIL import Image, ImageTk
from math import sqrt

from ..system.elements.BBox import BBoxGUI as Rect
from ..system.elements.Coords import Coords

class MainCanvas(Component):
    def __init__(self, parent):
        super().__init__(parent, 'MainCanvas')
        # Canvas
        self.vscroll = ttk.Scrollbar(self.frame, orient=VERTICAL)
        self.canvas = Canvas(self.frame)
        self.canvas.configure(
            background='silver',
            width=700, height=600,
            scrollregion=(0,0,350,600),
            yscrollcommand=self.vscroll.set
        )
        self.vscroll.configure(command=self.canvas.yview)
        # Grid Configuration
        self.canvas.grid(row=0, column=0, sticky=(N,S,E,W))
        self.vscroll.grid(row=0, column=1, sticky=(N,S))
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        # Bindings
        self.canvas.bind('<Configure>', self.handleConfigure)
        self.canvas.bind('<Button-1>', self.handleClickB1)
        self.canvas.bind('<B1-Motion>', self.handleMotionB1)
        self.canvas.bind('<B1-ButtonRelease>', self.handleReleaseB1)
        self.canvas.bind('<Motion>', self.handleMotion)
        self.canvas.bind('<MouseWheel>', self.handleMouseWheel)
        # Listeners
        self.addListener('<ResponseRects>', self.handleResponseRects)
        self.addListener('<PageChange>', self.handlePageChange)
        # Set Initial State
        self.setState(
            image=None, page=0, width=350, height=495,
            rects=[]
        )
    
    def insideRect(self, rect, x, y):
        assert isinstance(rect, Rect)
        coords = self.decodeRect(rect.coords)
        return coords.contains_point(x, y)
    
    def findRectAt(self, x, y):
        rects = self.state['rects']
        for rect in rects:
            if self.insideRect(rect, x, y):
                return rect
        return None
    
    def getRectArea(self, x0, y0, x1, y1):
        return (x1 - x0) * (y1 - y0)
    
    def encodeRect(self, coords):
        """From canvas coordinates to PDF coordinates."""
        assert isinstance(coords, Coords)
        canvasWidth, canvasHeight = self.state['width'], self.state['height']
        imageWidth, imageHeight = self.state['image'].size
        return coords.scale_XY(imageWidth / canvasWidth, imageHeight / canvasHeight)
    
    def decodeRect(self, coords):
        """From PDF coordinates to canvas coordinates."""
        assert isinstance(coords, Coords)
        canvasWidth, canvasHeight = self.state['width'], self.state['height']
        imageWidth, imageHeight = self.state['image'].size
        return coords.scale_XY(canvasWidth / imageWidth, canvasHeight / imageHeight)
    
    def drawRects(self):
        # Delete existing rects
        self.canvas.delete('inscreen')
        # Draw new rects
        rects = self.state['rects']
        for rect in rects:
            assert isinstance(rect, Rect)
            canvasID = self.canvas.create_rectangle(
                *self.decodeRect(rect.coords).to_tuple(),
                fill='', outline=rect.color,
                tags=('inscreen',)
            )
            rect.canvasID = canvasID
    
    def requestRects(self):
        event = dict(name='<RequestRects>', page=self.state['page'])
        self.emitEvent('MainFrame', event)
    
    def handleResponseRects(self, event):
        # Delete existing rects
        self.setState(rects=event['rects'])
    
    def handleMotion(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        # Find rect under cursor
        tarRect = self.findRectAt(x, y)
        tarRectID = tarRect.id if tarRect else None
        # Update rectangle highlighting
        for rect in self.state['rects']:
            if rect.id == tarRectID:
                self.canvas.itemconfig(rect.canvasID, outline='orange')
            else:
                self.canvas.itemconfig(rect.canvasID, outline=rect.color)
    
    def handleClickB1(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        # Show event and coordinates
        coord = ' pos=(%d,%d)' % (x, y)
        self.updateStatusBar('<Button-1>' + coord)
        # Find rectangle under cursor, if exists
        rect = self.findRectAt(x, y)
        self.selectedRectID = rect.id if rect else None
        # Create active rectangle
        self.activeRect = self.canvas.create_rectangle(x, y, x, y, fill='', outline='green')
        self.arX, self.arY = x, y
    
    def handleMotionB1(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        # Show event and coordinates
        coord = ' pos=(%d,%d)' % (x, y)
        self.updateStatusBar('<B1-Motion>' + coord)
        # Update coordinates of active rectangle
        self.canvas.coords(self.activeRect, self.arX, self.arY, x, y)
    
    def handleReleaseB1(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        # Show event and coordinates
        coord = ' pos=(%d,%d)' % (x, y)
        self.updateStatusBar('<B1-ButtonRelease>' + coord)
        # Check the area of the active rectangle
        coords = Coords(*self.canvas.coords(self.activeRect))
        if coords.area() < 10: # a click
            if self.selectedRectID:
                event = dict(name='<SelectRect>', id=self.selectedRectID)
            else:
                event = dict(name='<DeselectRect>')
        else:
            event = dict(
                name='<NewRectFinished>',
                page=self.state['page'],
                coords=self.encodeRect(coords)
            )
        self.emitEvent('MainFrame', event)
        # Remove active rectangle
        self.canvas.delete(self.activeRect)
        self.activeRect = None
        # Request updated rectangles
        self.requestRects()
    
    def handleConfigure(self, event):
        width = event.width
        height = int(width * sqrt(2))
        print(width, height)
        self.setState(width=width, height=height)
    
    def handleMouseWheel(self, event):
        self.canvas.yview_scroll(-event.delta, 'units')
    
    def handlePageChange(self, event):
        self.canvas.yview_moveto(0.0)
    
    def afterSetState(self):
        image = self.state['image']
        if image:
            width, height = self.state['width'], self.state['height']
            self.canvas.configure(scrollregion=(0,0,width,height))
            image = image.resize((width, height), Image.ANTIALIAS)
            self.image = ImageTk.PhotoImage(image=image)
            self.canvas.create_image(0, 0, image=self.image, anchor=NW)
            self.drawRects()
        