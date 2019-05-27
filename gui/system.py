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
from ..system.aux.reflabel import RefLabel
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
        self.paramPanel = ParamPanel(self)
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
        self.paramPanel.grid(row=1, column=0, sticky=EW)
        self.audioVisualiser.grid(row=2, column=0)
        self.evalPanel.grid(row=3, column=0, sticky=EW)
        # Subsystems
        self.ocr = OCR()
        self.speech = Speech()
        self.align = Align(self.ocr, self.speech)
        # Evaluation
        self.ocrEval = self.alignEval = None
        # Config
        self.config = dict(
            scale='par',
            lang='eng',
            gauss=None, # gaussian std (scale)
            common=None, # common word gain
            key=None, # key word gain
        )
        # State
        self.setState(
            curGroupID=-1,
            totalGroup=0,
            curBBoxID=-1,
            totalBBox=0,
        )
    
    def setConfig(self, **kwargs):
        self.config.update(kwargs)
    
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
        if self.alignEval and self.alignEval.hyp_matched_segs and gid > -1:
            segs = self.alignEval.hyp_matched_segs[gid]
            self.audioVisualiser.sendSegments(segs, 2)
    
    def runSystem(self):
        if isinstance(self.ocr, OCRTess):
            self.ocr.set_scale(self.config['scale'])
            self.ocr.set_lang(self.config['lang'])
        if isinstance(self.align, AlignBasic):
            self.align.set_params(
                gauss=self.config['gauss'],
                common=self.config['common'],
                key=self.config['key'],
            )
        self.align.process()
        self.pleaseUpdateRects()
        if self.label is not None:
            self.label.reopen()
            self.evalPanel.reset()
            self.ocrEval = OCREval(self.label, self.align)
            self.evalPanel.passOCRResult(self.ocrEval.evaluate())
            self.alignEval = AlignEval(self.label, self.align)
            self.evalPanel.passAlignResult(self.alignEval.evaluate())
        self.setState()
    
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
        self.label = RefLabel(filename)
    
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
        # Model Selector
        self.lang = StringVar()
        self.langBox = ttk.LabelFrame(self.frame, text='Model', padding=5)
        self.rbEng = ttk.Radiobutton(self.langBox, text='eng', variable=self.lang, value='eng', command=self.onLangChange)
        self.rbEngHw = ttk.Radiobutton(self.langBox, text='eng-9000', variable=self.lang, value='eng-9000', command=self.onLangChange)
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
        self.langBox.grid(row=1, column=0, sticky=EW)
        self.langBox.columnconfigure(0, weight=1)
        self.langBox.columnconfigure(1, weight=1)
        self.rbEng.grid(row=0, column=0, sticky=W)
        self.rbEngHw.grid(row=0, column=1, sticky=W)
        self.textBox.grid(row=2, column=0, sticky=EW)
        self.textBox.columnconfigure(0, weight=1)
        self.textField.grid(row=0, column=0, sticky=EW)
        # State
        self.setState(
            text=''
        )
    
    def afterSetState(self):
        self.textField.replace('1.0', 'end', self.state['text'])
    
    def onScaleChange(self):
        self.parent.setConfig(scale=self.scale.get())
        self.parent.runSystem()
    
    def onLangChange(self):
        self.parent.setConfig(lang=self.lang.get())
        self.parent.runSystem()


class ParamPanel(Component):
    """Panel for Parameters."""
    def __init__(self, parent):
        super().__init__(parent, 'ParamPanel', withLabel=True)
        self.configure(text='Parameters', padding=5)
        # Box - Gauss
        self.boxGauss = ttk.Frame(self.frame)
        self.labelGauss = ttk.Label(self.boxGauss, text='sigma=')
        self.svGauss = StringVar()
        self.entryGauss = ttk.Entry(self.boxGauss, textvariable=self.svGauss, width=5)
        # Box - Common
        self.boxCommon = ttk.Frame(self.frame)
        self.labelCommon = ttk.Label(self.boxCommon, text='alpha=')
        self.svCommon = StringVar()
        self.entryCommon = ttk.Entry(self.boxCommon, textvariable=self.svCommon, width=5)
        # Box - Key
        # self.boxKey = ttk.Frame(self.frame)
        # self.labelKey = ttk.Label(self.boxKey, text='key=')
        # self.svKey = StringVar()
        # self.entryKey = ttk.Entry(self.boxKey, textvariable=self.svKey, width=5)
        # Button
        self.buttonSet = ttk.Button(self.frame, text='set', command=self.onClickSet)
        # Grid Configuration
        self.boxGauss.grid(row=0, column=0)
        self.labelGauss.grid(row=0, column=0)
        self.entryGauss.grid(row=0, column=1)
        self.boxCommon.grid(row=0, column=1)
        self.labelCommon.grid(row=0, column=0)
        self.entryCommon.grid(row=0, column=1)
        # self.boxKey.grid(row=0, column=2)
        # self.labelKey.grid(row=0, column=0)
        # self.entryKey.grid(row=0, column=1)
        self.buttonSet.grid(row=0, column=4, sticky=E)
    
    def getVar(self, sv):
        try:
            ret = float(sv.get())
            return ret if ret > 0 else None
        except ValueError:
            return None
        return None
    
    def onClickSet(self):
        self.parent.setConfig(
            gauss=self.getVar(self.svGauss),
            common=self.getVar(self.svCommon),
            # key=self.getVar(self.svKey),
        )
        self.parent.runSystem()


class EvalPanel(Component):
    """Evaluation Panel."""
    def __init__(self, parent):
        super().__init__(parent, 'EvalPanel', withLabel=True)
        self.configure(text='Evaluation', padding=5)
        # TreeView
        self.tree = ttk.Treeview(self.frame, columns=('Result',), height=7)
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
        TPR = f(res['TPR'])
        TNR = f(res['TNR'])
        werAll = f(res['WER']['all'])
        werI, werD, werS = f(res['WER']['I']), f(res['WER']['D']), f(res['WER']['S'])
        iid1 = self.tree.insert(parent='', index='end', text='OCR-TPR', values=(TPR,))
        iid3 = self.tree.insert(parent='', index='end', text='OCR-TNR', values=(TNR,))
        iid2 = self.tree.insert(parent='', index='end', text='OCR-WER', values=(werAll,))
        iid21 = self.tree.insert(parent=iid2, index='end', text='I', values=(werI,))
        iid22 = self.tree.insert(parent=iid2, index='end', text='D', values=(werD,))
        iid23 = self.tree.insert(parent=iid2, index='end', text='S', values=(werS,))
    
    def passAlignResult(self, res):
        f = lambda x: ('%.2f%%' % (x * 100))
        recall = f(res['recall'])
        iid1 = self.tree.insert(parent='', index='end', text='Align-Recall', values=(recall,))