from tkinter import *
from tkinter import ttk

from .mainframe import MainFrame

class Root:
    def __init__(self):
        self.root = Tk()
        self.root.title('Talking Handouts')
        # Create necessary variables for MainFrame
        self.children = []
        self.frame = self.root
        self.mainframe = MainFrame(self)
        # Grid Configuration
        self.mainframe.grid(row=0, column=0, sticky=NSEW)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
    
    def mainloop(self):
        self.root.mainloop()

root = Root()
root.mainloop()