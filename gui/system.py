from tkinter import *
from tkinter import ttk
from tkinter import filedialog

from .component import Component
from .audiovisualiser import AudioCanvas, AudioVisualiser
from ..system.subsystems.OCR.OCRTess import OCRTess, OCR
from ..system.subsystems.Speech.SpeechGC import SpeechGC, Speech
from ..system.subsystems.Align.AlignBasic import AlignBasic, Align
from ..system.elements.BBox import *
from ..system.elements.Match import Match, Matches
from ..eval.code.ocr import OCREval
from ..eval.code.align import AlignEval

import json, os

class System(Component):
    def __init__(self, parent):
        super().__init__(parent, 'System', withLabel=True)
        self.configure(text='System', padding=5)
        self.filename = None
        self.label = None
        # Components
        self.ocrPanel = OCRPanel(self)
        self.audioVisualiser = AudioVisualiser(self)
        self.evalPanel = EvalPanel(self)
        # Listeners
        self.addListener('<RequestRects>', self.handleRequestRects)
        self.addListener('<SelectRect>', self.handleSelectRect)
        self.addListener('<DeselectRect>', self.handleDeselectRect)
        self.addListener('<OpenPDF>', self.handleOpenPDF)
        # Grid Configuration
        self.frame.columnconfigure(0, weight=1)
        self.ocrPanel.grid(row=0, column=0, sticky=EW)
        self.audioVisualiser.grid(row=1, column=0)
        self.evalPanel.grid(row=2, column=0, sticky=EW)
        # Subsystems
        self.ocr = OCR()
        self.speech = Speech()
        self.align = Align(self.ocr, self.speech)
        # State
        self.setState(
            curGroupID=-1,
            totalGroup=0,
            curBBoxID=-1,
            totalBBox=0,
        )
    
    def afterSetState(self):
        gid = self.state['curGroupID']
        bid = self.state['curBBoxID']
        if self.ocr.result and gid > -1 and bid > -1:
            t = self.ocr.result[gid][bid].text
        else:
            t = '(no box selected)'
        self.ocrPanel.setState(text=t)
        if self.align.result and gid > -1: # hyp
            segs = self.align.result[gid].tinterval_group
            self.audioVisualiser.sendSegments(segs, 1)
        if self.label and gid > -1: # ref
            segs = self.label[gid].tinterval_group
            self.audioVisualiser.sendSegments(segs, 2)
    
    def runSystem(self, scale):
        if isinstance(self.ocr, OCRTess):
            self.ocr.set_scale(scale)
        self.align.process()
        self.pleaseUpdateRects()
        if self.filename:
            self.label = self.readLabelData(self.filename)
        if self.label is not None:
            self.evalPanel.reset()
            self.ocrEval = OCREval(self.label.get_bbox_groups(), self.align.result.get_bbox_groups())
            self.evalPanel.passOCRResult(self.ocrEval.evaluate())
            self.alignEval = AlignEval(self.label, self.align.result)
            self.evalPanel.passAlignResult(self.alignEval.evaluate())
    
    def readLabelData(self, filename):
        path = os.path.normpath(os.path.join(os.path.dirname(__file__), '../labels/%s.json' % filename))
        with open(path, 'r') as fin:
            label = json.load(fin)
        return Matches(label, from_obj=True)
    
    def pleaseUpdateRects(self):
        """Notify the Canvas that new rects are available for request"""
        event = dict(name='<PleaseUpdateRects>')
        self.emitEvent('MainFrame', event)
    
    def handleOpenPDF(self, event):
        filename = event['filename']
        if self.filename == filename:
            return None
        self.filename = filename
        self.ocr = OCRTess(filename)
        self.speech = SpeechGC(filename)
        self.align = AlignBasic(self.ocr, self.speech)
        self.audioVisualiser.initAudioPlayer(filename)
        # evaluation
        self.label = self.readLabelData(filename)
    
    def handleRequestRects(self, event):
        rects = []
        # check if OCR result is ready
        if self.ocr.result:
            for groupID, bg in enumerate(self.ocr.result):
                for bboxID, bbox in enumerate(bg):
                    if bbox.page == event['page']:
                        if groupID == self.state['curGroupID']:
                            rect = BBoxGUI(bbox, color='red')
                        else:
                            rect = BBoxGUI(bbox, color='blue')
                        rects.append(rect)
        event = dict(
            name='<ResponseRects>',
            rects=rects
        )
        self.emitEvent('MainFrame', event)
    
    def handleSelectRect(self, event):
        # check if OCR result is ready
        if self.ocr.result:
            for groupID, bg in enumerate(self.ocr.result):
                for bboxID, bbox in enumerate(bg):
                    if bbox.id == event['id']:
                        print('handleSelectRect Success')
                        self.setState(
                            curGroupID=groupID, 
                            curBBoxID=bboxID,
                        )
                        return True
        return False
    
    def handleDeselectRect(self, event):
        self.setState(curGroupID=-1, curBBoxID=-1)
    

class OCRPanel(Component):
    def __init__(self, parent):
        super().__init__(parent, 'OCRPanel', withLabel=True)
        self.configure(text='OCR', padding=5)
        # Buttons (not used, maybe useful)
        self.buttonRun = ttk.Button(self.frame, text='Run', command=None)
        # Scale Selector
        self.scale = StringVar()
        self.scaleBox = ttk.LabelFrame(self.frame, text='Scale', padding=5)
        self.rbWord = ttk.Radiobutton(self.scaleBox, text='Word', variable=self.scale, value='word', command=self.onScaleChange)
        self.rbLine = ttk.Radiobutton(self.scaleBox, text='Line', variable=self.scale, value='line', command=self.onScaleChange)
        self.rbPar = ttk.Radiobutton(self.scaleBox, text='Paragraph', variable=self.scale, value='par', command=self.onScaleChange)
        self.rbPage = ttk.Radiobutton(self.scaleBox, text='Page', variable=self.scale, value='page', command=self.onScaleChange)
        # BBoxGroup Text Viewer
        self.textBox = ttk.LabelFrame(self.frame, text='Text in the Group', padding=5)
        self.textField = Text(self.textBox, width=20, height=5, font='Menlo')
        # Grid Configuration
        self.frame.columnconfigure(0, weight=1)
        # self.buttonRun.grid(row=0, column=0, sticky=EW)
        self.scaleBox.grid(row=0, column=0, sticky=EW)
        self.scaleBox.columnconfigure(0, weight=1)
        self.scaleBox.columnconfigure(1, weight=1)
        self.scaleBox.columnconfigure(2, weight=1)
        self.scaleBox.columnconfigure(3, weight=1)
        self.rbWord.grid(row=0, column=0, sticky=W)
        self.rbLine.grid(row=0, column=1, sticky=W)
        self.rbPar.grid(row=0, column=2, sticky=W)
        self.rbPage.grid(row=0, column=3, sticky=W)
        self.textBox.grid(row=1, column=0, sticky=EW)
        self.textBox.columnconfigure(0, weight=1)
        self.textField.grid(row=0, column=0, sticky=EW)
        # State
        self.setState(
            text=''
        )
    
    def afterSetState(self):
        self.textField.replace('1.0', 'end', self.state['text'])
    
    def onScaleChange(self):
        self.parent.runSystem(scale=self.scale.get())


class EvalPanel(Component):
    """Evaluation Panel."""
    def __init__(self, parent):
        super().__init__(parent, 'EvalPanel', withLabel=True)
        self.configure(text='Evaluation', padding=5)
        # TreeView
        self.tree = ttk.Treeview(self.frame, columns=('Result',), height=6)
        self.tree.heading('#0', text='Name')
        self.tree.heading('Result', text='Result')
        self.tree.column('#0', width=200)
        self.tree.column('Result', width=200)
        # Grid Configuration
        self.frame.columnconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky=NSEW)
        
    def reset(self):
        self.tree.delete(*self.tree.get_children())
    
    def passOCRResult(self, res):
        f = lambda x: ('%.2f%%' % (x * 100))
        recall = f(res['recall'])
        werAll = f(res['WER']['all'])
        werI, werD, werS = f(res['WER']['I']), f(res['WER']['D']), f(res['WER']['S'])
        iid1 = self.tree.insert(parent='', index='end', text='OCR-Recall', values=(recall,))
        iid2 = self.tree.insert(parent='', index='end', text='OCR-WER', values=(werAll,))
        iid21 = self.tree.insert(parent=iid2, index='end', text='I', values=(werI,))
        iid22 = self.tree.insert(parent=iid2, index='end', text='D', values=(werD,))
        iid23 = self.tree.insert(parent=iid2, index='end', text='S', values=(werS,))
    
    def passAlignResult(self, res):
        f = lambda x: ('%.2f%%' % (x * 100))
        recall = f(res['recall'])
        iid1 = self.tree.insert(parent='', index='end', text='Align-Recall', values=(recall,))