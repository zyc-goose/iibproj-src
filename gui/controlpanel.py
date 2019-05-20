from tkinter import *
from tkinter import ttk

from .component import Component
from .labeller import Labeller
from .system import System

class ControlPanel(Component):
    def __init__(self, parent):
        super().__init__(parent, 'ControlPanel')
        self.configure(padding=10)
        # Mode Selector
        self.selector = ModeSelector(self)
        # Mode Container
        self.container = ModeContainer(self)
        # Grid Configuration
        self.frame.columnconfigure(0, weight=1)
        self.selector.grid(row=0, column=0, sticky=NSEW)
        self.container.grid(row=1, column=0, sticky=NSEW)
        # Select Default Mode
        self.selector.onModeChange()


class ModeSelector(Component):
    def __init__(self, parent):
        super().__init__(parent, 'ModeSelector', withLabel=True)
        self.configure(text='Mode Selector', padding=10)
        # Radio Buttons
        self.mode = StringVar()
        self.rbSystem = ttk.Radiobutton(self.frame, text='System', variable=self.mode, value='System', command=self.onModeChange)
        self.rbLabeller = ttk.Radiobutton(self.frame, text='Labeller', variable=self.mode, value='Labeller', command=self.onModeChange)
        # Grid Configuration
        self.frame.columnconfigure(0, weight=1)
        self.rbSystem.grid(row=0, column=0, sticky=EW)
        self.rbLabeller.grid(row=1, column=0, sticky=EW)
        # Default Mode
        self.mode.set('Labeller')

    def onModeChange(self):
        print('onModeChange')
        event = dict(name='<ModeChange>', mode=self.mode.get())
        self.emitEvent('ControlPanel', event)


class ModeContainer(Component):
    def __init__(self, parent):
        super().__init__(parent, 'ModeContainer')
        # Modes
        self.mode = None
        self.modeEntity = None
        # Registered Modes
        self.labellerMode = Labeller(self)
        self.registry = dict(
            System=System(self),
            Labeller=Labeller(self),
        )
        # Listeners
        self.addListener('<ModeChange>', self.handleModeChange)
        # Grid Configuration
        self.frame.columnconfigure(0, weight=1)
    
    def handleModeChange(self, event):
        print('handleModeChange')
        # Hide previous mode
        if self.modeEntity:
            self.modeEntity.forget()
        # Show new mode
        modeName = event['mode']
        print(modeName)
        for key, entity in self.registry.items():
            if key == modeName:
                entity.enable()
                self.modeEntity = entity
            else:
                entity.disable()
        print(self.modeEntity)
        if self.modeEntity:
            self.modeEntity.grid(row=0, column=0, sticky=EW)
            self.modeEntity.pleaseUpdateRects()
        # request open PDF
        event = dict(name='<RequestOpenPDF>')
        self.emitEvent('MainFrame', event)