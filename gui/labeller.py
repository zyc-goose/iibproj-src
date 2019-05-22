from tkinter import *
from tkinter import ttk
from tkinter import filedialog

from .component import Component
from .audiovisualiser import AudioCanvas
from ..system.elements.Match import Match, Matches
from ..system.elements.BBox import BBoxGroup, BBoxGUI, BBox
from ..system.elements.TInterval import TIntervalGroup, TInterval
from ..system.elements.TStamp import TStamp
from uuid import uuid4
import json, os

class Labeller(Component):
    def __init__(self, parent):
        super().__init__(parent, 'Labeller', withLabel=True)
        self.configure(text='Labeller', padding=5)
        # Current Active File
        self.filepath = ''
        self.filebuf = Matches()
        # Managers
        self.fileManager = FileManager(self)
        self.groupManager = GroupManager(self)
        self.bboxManager = BBoxManager(self)
        self.textManager = TextManager(self)
        self.intervalManager = IntervalManager(self)
        # Grid Configuration
        self.frame.columnconfigure(0, weight=1)
        self.fileManager.grid(row=0, column=0, sticky=NSEW)
        self.groupManager.grid(row=1, column=0, sticky=EW)
        self.bboxManager.grid(row=2, column=0, sticky=EW)
        self.textManager.grid(row=3, column=0, sticky=EW)
        self.intervalManager.grid(row=4, column=0, sticky=EW)
        # Bindings
        self.addListener('<OpenPDF>', self.handleOpenPDF)
        self.addListener('<NewRectFinished>', self.handleNewRectFinished)
        self.addListener('<RequestRects>', self.handleRequestRects)
        self.addListener('<SelectRect>', self.handleSelectRect)
        self.addListener('<DeselectRect>', self.handleDeselectRect)
        # Initial State
        self.setState(
            filename='',
            modified=False,
            curGroupID=-1,
            totalGroup=0,
            curBBoxID=-1,
            totalBBox=0,
        )
    
    def afterSetState(self):
        self.fileManager.setState(
            filename=self.state['filename'],
            modified=self.state['modified']
        )
        self.groupManager.setState(
            curGroupID=self.state['curGroupID'],
            totalGroup=self.state['totalGroup'],
        )
        self.bboxManager.setState(
            curBBoxID=self.state['curBBoxID'],
            totalBBox=self.state['totalBBox'],
        )
        bbox = self.getCurrentBBox()
        self.textManager.setState(
            uuid=bbox.id if bbox else None,
            text=bbox.text if bbox else ''
        )
        self.intervalManager.setState(
            filename=self.state['filename'],
            curGroupID=self.state['curGroupID'],
        )
    
    def getCurrentBBox(self):
        bbox = None
        if self.state['curGroupID'] > -1:
            bg = self.filebuf[self.state['curGroupID']].bbox_group
            if self.state['curBBoxID'] > -1:
                bbox = bg[self.state['curBBoxID']]
        return bbox
    
    def getCurrentTIntGroup(self):
        if self.state['curGroupID'] > -1:
            tg = self.filebuf[self.state['curGroupID']].tinterval_group
        else:
            tg = None
        return tg
    
    def pleaseUpdateRects(self):
        """Notify the Canvas that new rects are available for request"""
        event = dict(name='<PleaseUpdateRects>')
        self.emitEvent('MainFrame', event)
    
    def cleanFileBuf(self):
        """Clean-up invalid entries in the file buffer."""
        if self.filebuf is None:
            return None
        for m in self.filebuf:
            tg = list(filter(lambda x: x.start < x.end, m.tinterval_group))
            m.tinterval_group = TIntervalGroup(tg, from_obj=False)
    
    def fileOpen(self):
        filename = self.state['filename']
        if filename == '':
            return None
        path = os.path.join(os.path.dirname(__file__), '../labels', filename + '.json')
        path = os.path.normpath(path)
        # create file if not already exist
        try:
            f = open(path, 'r')
        except FileNotFoundError:
            f = open(path, 'w')
            json.dump(Matches().to_obj(), f)
        finally:
            f.close()
        with open(path, 'r') as fin:
            self.filebuf = Matches(json.load(fin), from_obj=True)
            # self.cleanFileBuf()
        self.filepath = path
        self.setState(
            modified=False,
            curGroupID=-1,
            totalGroup=len(self.filebuf),
            curBBoxID=-1,
            totalBBox=0,
        )
        # notify that new file has been opened
        self.pleaseUpdateRects()
    
    def fileSave(self):
        # self.cleanFileBuf()
        with open(self.filepath, 'w') as fout:
            json.dump(self.filebuf.to_obj(), fout, indent=4)
        self.setState(modified=False)
    
    def fileClear(self):
        """Clear up the current buffer"""
        self.filebuf = Matches()
        self.setState(curGroupID=-1, totalGroup=0, curBBoxID=-1, totalBBox=0)
        self.fileBufferChanged()
        self.pleaseUpdateRects()
    
    def fileBufferChanged(self):
        self.setState(modified=True)
    
    def removeEmptyGroup(self):
        # remove group if it's empty (has no bbox inside)
        gid = self.state['curGroupID']
        if gid != -1 and len(self.filebuf[gid].bbox_group) == 0:
            self.filebuf.pop(gid)
            self.setState(curGroupID=gid - 1, totalGroup=len(self.filebuf))
            self.fileBufferChanged()
    
    def groupCreate(self):
        self.removeEmptyGroup()
        m = Match(BBoxGroup(), TIntervalGroup())
        gid = self.state['curGroupID']
        gid = len(self.filebuf) if gid == -1 else gid + 1
        self.filebuf.insert(gid, m)
        self.setState(
            modified=True,
            curGroupID=gid,
            totalGroup=len(self.filebuf),
            curBBoxID=-1,
            totalBBox=0,
        )
        self.fileBufferChanged()
        self.pleaseUpdateRects()
    
    def groupDelete(self):
        gid = self.state['curGroupID']
        if gid > -1:
            self.filebuf.pop(gid)
            if gid - 1 > -1:
                tblen = len(self.filebuf[gid-1].bbox_group)
            else:
                tblen = 0
            self.setState(
                curGroupID=gid-1, 
                totalGroup=len(self.filebuf), 
                curBBoxID=-1, 
                totalBBox=tblen
            )
            self.fileBufferChanged()
            self.pleaseUpdateRects()
    
    def BBoxDelete(self):
        gid = self.state['curGroupID']
        bid = self.state['curBBoxID']
        if gid > -1 and bid > -1:
            self.filebuf[gid].bbox_group.pop(bid)
            self.setState(curBBoxID=bid-1, totalBBox=len(self.filebuf[gid].bbox_group))
            self.fileBufferChanged()
            self.pleaseUpdateRects()

    def getBBoxText(self):
        bbox = self.getCurrentBBox()
        return bbox.text

    def saveBBoxText(self, text):
        if self.state['curGroupID'] > -1 and self.state['curBBoxID'] > -1:
            match = self.filebuf[self.state['curGroupID']]
            bbox = match.bbox_group[self.state['curBBoxID']]
            bbox.set_text(text)
            self.fileBufferChanged()
    
    def saveTIntervalGroup(self, tg):
        if self.state['curGroupID'] > -1:
            assert isinstance(tg, TIntervalGroup)
            self.filebuf[self.state['curGroupID']].tinterval_group = tg
            self.fileBufferChanged()
    
    def handleOpenPDF(self, event):
        self.setState(filename=event['filename'])
        self.fileOpen()
    
    def handleNewRectFinished(self, event):
        # add new bbox
        if self.state['curGroupID'] >= 0:
            match = self.filebuf[self.state['curGroupID']]
            bbox = BBox(event['coords'], '', event['page'])
            bid = self.state['curBBoxID'] + 1
            match.bbox_group.insert(bid, bbox)
            self.setState(
                curBBoxID=bid,
                totalBBox=len(match.bbox_group)
            )
            self.fileBufferChanged()
    
    def handleRequestRects(self, event):
        rects = []
        for groupID, match in enumerate(self.filebuf):
            for bboxID, bbox in enumerate(match.bbox_group):
                if bbox.page == event['page']:
                    if groupID == self.state['curGroupID']:
                        if bboxID == self.state['curBBoxID']:
                            rect = BBoxGUI(bbox, color='red')
                        else:
                            rect = BBoxGUI(bbox, color='cyan')
                    else:
                        rect = BBoxGUI(bbox, color='blue')
                    rects.append(rect)
        event = dict(
            name='<ResponseRects>',
            rects=rects
        )
        self.emitEvent('MainFrame', event)
    
    def handleSelectRect(self, event):
        self.removeEmptyGroup()
        for groupID, match in enumerate(self.filebuf):
            for bboxID, bbox in enumerate(match.bbox_group):
                if bbox.id == event['id']:
                    print('handleSelectRect Success')
                    self.setState(
                        curGroupID=groupID, 
                        curBBoxID=bboxID,
                        totalBBox=len(match.bbox_group)
                    )
                    return True
        return False
    
    def handleDeselectRect(self, event):
        self.removeEmptyGroup()
        self.setState(curGroupID=-1, curBBoxID=-1, totalBBox=0)

        
class FileManager(Component):
    def __init__(self, parent):
        assert isinstance(parent, Labeller)
        super().__init__(parent, 'FileManager', withLabel=True)
        self.configure(text='File:', padding=5)
        # File IO Buttons Container
        self.buttonContainer = ttk.Frame(self.frame)
        # File IO Buttons
        self.buttonClear = ttk.Button(self.buttonContainer, text='Clear', command=self.parent.fileClear)
        self.buttonRevert = ttk.Button(self.buttonContainer, text='Revert', command=self.parent.fileOpen)
        self.buttonSave = ttk.Button(self.buttonContainer, text='Save', command=self.parent.fileSave)
        # Grid Configuration
        self.frame.columnconfigure(0, weight=1)
        self.buttonContainer.grid(row=0, column=0, sticky=EW)
        self.buttonContainer.columnconfigure(0, weight=1)
        self.buttonContainer.columnconfigure(1, weight=1)
        self.buttonContainer.columnconfigure(2, weight=1)
        self.buttonClear.grid(row=0, column=0, sticky=EW)
        self.buttonRevert.grid(row=0, column=1, sticky=EW)
        self.buttonSave.grid(row=0, column=2, sticky=EW)
        # Initial State
        self.setState(
            filename='',
            modified=False
        )
    
    def afterSetState(self):
        self.configure(text='File: ' + self.state['filename'] + ('*' if self.state['modified'] else ''))


class GroupManager(Component):
    def __init__(self, parent):
        super().__init__(parent, 'GroupManager', withLabel=True)
        self.configure(text='Group:', padding=5)
        # Buttons Container
        self.buttonContainer = ttk.Frame(self.frame)
        # Buttons
        self.buttonCreate = ttk.Button(self.buttonContainer)
        self.buttonCreate.configure(
            text='Create Group', command=self.parent.groupCreate
        )
        self.buttonDelete = ttk.Button(self.buttonContainer)
        self.buttonDelete.configure(
            text='Delete Group', command=self.parent.groupDelete
        )
        # Grid Configuration
        self.frame.columnconfigure(0, weight=1)
        self.buttonContainer.grid(row=0, column=0, sticky=EW)
        self.buttonContainer.columnconfigure(0, weight=1)
        self.buttonContainer.columnconfigure(1, weight=1)
        self.buttonCreate.grid(row=0, column=0, sticky=EW)
        self.buttonDelete.grid(row=0, column=1, sticky=EW)
        # Initial State
        self.setState(
            curGroupID=-1,
            totalGroup=0,
        )
    
    def afterSetState(self):
        self.configure(text='Group: (%d/%d)' % (self.state['curGroupID'] + 1, self.state['totalGroup']))
    
    def onClickCreate(self):
        pass
    
    def onClickDelete(self):
        pass


class BBoxManager(Component):
    def __init__(self, parent):
        super().__init__(parent, 'BBoxManager', withLabel=True)
        self.configure(text='BBox:', padding=5)
        # Buttons Container
        self.buttonContainer = ttk.Frame(self.frame)
        # Buttons
        self.buttonListen = ttk.Button(self.buttonContainer)
        self.buttonListen.configure(
            text='Listen: ON', command=self.onClickListen
        )
        self.buttonDelete = ttk.Button(self.buttonContainer)
        self.buttonDelete.configure(
            text='Delete', command=self.parent.BBoxDelete
        )
        # Grid Configuration
        self.frame.columnconfigure(0, weight=1)
        self.buttonContainer.grid(row=0, column=0, sticky=EW)
        self.buttonContainer.columnconfigure(0, weight=1)
        self.buttonContainer.columnconfigure(1, weight=1)
        self.buttonListen.grid(row=0, column=0, sticky=EW)
        self.buttonDelete.grid(row=0, column=1, sticky=EW)
        # Initial State
        self.setState(
            curBBoxID=-1,
            totalBBox=0,
        )
    
    def afterSetState(self):
        self.configure(text='BBox: (%d/%d)' % (self.state['curBBoxID'] + 1, self.state['totalBBox']))
    
    def onClickListen(self):
        pass
    
    def onClickDelete(self):
        pass


# source: https://stackoverflow.com/questions/40617515/python-tkinter-text-modified-callback
class CustomText(Text):
    def __init__(self, *args, **kwargs):
        """A text widget that report on internal widget commands"""
        super().__init__(*args, **kwargs)

        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, command, *args):
        cmd = (self._orig, command) + args
        result = self.tk.call(cmd)

        if command in ("insert", "delete", "replace"):
            self.event_generate("<<TextModified>>")

        return result


class TextManager(Component):
    def __init__(self, parent):
        super().__init__(parent, 'TextManager', withLabel=True)
        self.configure(text='Text:', padding=5)
        # Text Box
        self.text = CustomText(self.frame, width=20, height=5, font='Menlo')
        # Buttons
        self.buttonSave = ttk.Button(self.frame)
        self.buttonSave.configure(
            text='Save', command=self.onClickSave
        )
        self.buttonRevert = ttk.Button(self.frame)
        self.buttonRevert.configure(
            text='Revert', command=self.onClickRevert
        )
        # Grid Configuration
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=0)
        self.text.grid(row=0, column=0, columnspan=2, sticky=EW)
        self.buttonSave.grid(row=1, column=0, sticky=EW)
        self.buttonRevert.grid(row=1, column=1, sticky=EW)
        # Bindings
        self.text.bind('<<TextModified>>', self.onTextChange)
        # Initial State
        self.uuid = None
        self.setState(
            uuid=None,
            modified=False
        )
    
    def afterSetState(self):
        # update display
        if self.state['uuid'] is None:
            s = ' (inactive)'
        elif self.state['modified']:
            s = ' (modified)'
        else:
            s = ''
        self.configure(text='Text:' + s)
        # if bbox focus changed, update text
        if self.state['uuid'] != self.uuid:
            self.uuid = self.state['uuid']
            if self.uuid: # bbox exists
                self.onClickRevert() # load text
            else:
                self.text.delete('1.0', 'end')
        # disable text box if no bbox selected
        if self.state['uuid']:
            self.text.configure(state='normal')
            self.buttonSave.state(['!disabled'])
            self.buttonRevert.state(['!disabled'])
        else:
            self.text.configure(state='disabled')
            self.buttonSave.state(['disabled'])
            self.buttonRevert.state(['disabled'])
    
    def onClickRevert(self):
        text = self.parent.getBBoxText().strip()
        self.text.configure(state='normal')
        self.text.replace('1.0', 'end', text)
        self.setState(modified=False)

    def onClickSave(self):
        text = self.text.get('1.0', 'end').strip()
        self.parent.saveBBoxText(text)
        self.setState(modified=False)
    
    def onTextChange(self, event):
        if self.uuid:
            self.setState(modified=True)


class IntervalManager(Component):
    def __init__(self, parent):
        super().__init__(parent, 'IntervalManager', withLabel=True)
        self.configure(text='Interval:', padding=5)
        # Audio Canvas
        self.audioCanvas = AudioCanvasLabeller(self)
        # Grid Configuration
        self.frame.columnconfigure(0, weight=1)
        self.audioCanvas.grid(row=0, column=0)
        # State
        self.groupID = -1
        self.curTInt = TInterval()
        self.curTIntGroup = TIntervalGroup()
        self.setState(curGroupID=-1, filename='')
    
    def afterSetState(self):
        # update display
        if self.state['curGroupID'] == -1:
            s = ' (inactive)'
        else:
            s = ''
        self.configure(text='Interval:' + s)
        # load necessary stuff
        if self.state['curGroupID'] != self.groupID:
            self.groupID = self.state['curGroupID']
            self.curTInt = TInterval()
            self.setCanvasTint()
            if self.groupID == -1:
                self.curTIntGroup = TIntervalGroup()
                self.syncSegments()
            else:
                self.curTIntGroup = self.parent.getCurrentTIntGroup()
                self.syncSegments()
                self.audioCanvas.focus()
        # kangsang kamida music
        filename = self.state['filename']
        if self.audioCanvas.player is None and filename:
            self.audioCanvas.initAudioPlayer(filename)
    
    def handleCanvasB1(self, ts):
        if self.groupID == -1 or self.audioCanvas.switchST is None: # do nothing
            return None
        assert isinstance(ts, TStamp)
        if self.audioCanvas.switchST == 'S':
            self.curTInt.start = ts
        elif self.audioCanvas.switchST == 'T':
            self.curTInt.end = ts
        self.setCanvasTint()
        if self.curTInt.length() > 0 and self.audioCanvas.switchST == 'T':
            self.curTIntGroup.append(self.curTInt.copy())
            self.curTIntGroup.reduce()
            self.parent.fileBufferChanged()
            self.syncSegments()
    
    def handleCanvasKeyX(self, tsx):
        seg_id = -1
        for i, seg in enumerate(self.curTIntGroup):
            if tsx > seg.start and tsx < seg.end:
                seg_id = i
                break
        if seg_id != -1:
            self.curTIntGroup.pop(seg_id)
            self.parent.fileBufferChanged()
            self.syncSegments()
    
    def setCanvasTint(self):
        self.audioCanvas.setS(self.curTInt.start)
        self.audioCanvas.setT(self.curTInt.end)
    
    def syncSegments(self):
        self.audioCanvas.setState(Ch1Segments=self.curTIntGroup)


class AudioCanvasLabeller(AudioCanvas):
    def __init__(self, parent):
        self.textS = self.textT = None
        self.tsS, self.tsT = TStamp(), TStamp()
        self.switchST = None
        super().__init__(parent)
    
    def deleteSegmentAtCursor(self):
        if self.mouseX is None:
            return None
        tsx = self.CTW(self.mouseX)
        self.parent.handleCanvasKeyX(tsx)
    
    def nextSwitchST(self, switchST):
        if switchST is None:
            return 'S'
        if switchST == 'S':
            return 'T'
        return None
    
    def setS(self, tsS):
        assert isinstance(tsS, TStamp)
        self.tsS = tsS
        self.drawTStamps()

    def setT(self, tsT):
        assert isinstance(tsT, TStamp)
        self.tsT = tsT
        self.drawTStamps()
    
    def handleB1(self, event):
        super().handleB1(event)
        self.parent.handleCanvasB1(self.getTStampAtCursor())
    
    def handleKey(self, event):
        super().handleKey(event)
        if event.char == 's': # switch ST
            self.switchST = self.nextSwitchST(self.switchST)
            self.drawTStamps()
        elif event.char == 'x': # delete seg at cursor
            self.deleteSegmentAtCursor()
    
    def handleLeave(self, event):
        super().handleLeave(event)
        self.switchST = None
        self.drawTStamps()

    def drawTStamps(self):
        super().drawTStamps()
        FW, FH = self.FrameWidth, self.FrameHeight
        colorS = 'orange' if self.switchST == 'S' else 'blue'
        colorT = 'orange' if self.switchST == 'T' else 'blue'
        self.canvas.delete('textS')
        self.canvas.delete('textT')
        self.canvas.create_text(50, FH - 12, text='    START\n' + str(self.tsS), fill=colorS, tag='textS')
        self.canvas.create_text(FW - 42, FH - 12, text='     END\n' + str(self.tsT), fill=colorT, tag='textT')
    
    