from tkinter import *
from tkinter import ttk

from .component import Component
from ..system.elements.TStamp import TStamp
from ..system.elements.TInterval import TInterval
from ..system.aux.audioplayer import AudioPlayer
from ..system.aux.setinterval import setInterval

import time, os

class AudioCanvas(Component):
    def __init__(self, parent):
        super().__init__(parent, 'AudioCanvas')
        self.cursor = self.audioCursor =  None
        self.cbstopper = self.audioTimer = None
        self.mouseX = self.mouseY = None
        self.textL = self.textM = self.textR = self.textG = None
        self.player = None
        self.setGeometry()
        self.canvas = Canvas(self.frame)
        self.canvas.configure(
            width=self.FrameWidth,
            height=self.FrameHeight,
        )
        # Grid Configuration
        self.canvas.grid(row=0, column=0, sticky=(N,S,E,W))
        # Bindings
        self.canvas.bind('<Button-1>', self.handleB1)
        self.canvas.bind('<Key>', self.handleKey)
        self.canvas.bind('<Motion>', self.handleMotion)
        self.canvas.bind('<Leave>', self.handleLeave)
        self.canvas.bind('<MouseWheel>', self.handleMouseWheel)
        # State
        self.setState(
            FrameRange=TInterval(TStamp(-10), TStamp(1001)),
            AudioLength=TStamp(1000),
            Ch1Segments=[],
            Ch2Segments=[],
        )
    
    def setGeometry(self):
        # Frame
        self.FrameWidth = 400
        self.FrameHeight = 160
        self.HalfFrameHeight = self.FrameHeight // 2
        # Vertical Bars
        self.HorizonEndBarHeight = 50
        self.SegmentEndBarHeight = 5
        self.TimeToHeight = {60:15, 10:10, 5:7, 1:5}
        # Channels
        self.ChannelOffset = 30
        # Limits
        self.MinFrameRangeLength = 1.5
    
    def WTC(self, ts):
        """World coordinate to Canvas coordinate (x-dir)."""
        assert isinstance(ts, TStamp)
        FR, FW = self.state['FrameRange'], self.FrameWidth
        frac = (ts - FR.start) / FR.length()
        return round(FW * frac)
    
    def CTW(self, x):
        """Canvas coordinate to World coordinate (x-dir)."""
        FR, FW = self.state['FrameRange'], self.FrameWidth
        frac = x / FW
        return FR.start + (frac * FR.length())
    
    def initAudioPlayer(self, filename):
        self.player = AudioPlayer(filename)
        self.setState(AudioLength=TStamp(self.player.length))
        delta = 0.08 * self.player.length
        self.setState(FrameRange=TInterval(TStamp(-delta), TStamp(self.player.length + delta)))

    def moveAudioCursor(self):
        initTS = self.audioTimer
        self.player.play(start=self.audioTimer.to_sec())
        start = time.time()
        @setInterval(0.05)
        def callback():
            self.audioTimer = initTS + (time.time() - start)
            self.drawAudioCursor()
            self.drawTStamps()
        self.cbstopper = callback()
    
    def placeAudioCursor(self):
        x, FH, AL = self.mouseX, self.FrameHeight, self.state['AudioLength']
        tsx = self.CTW(x)
        if tsx > AL:
            if self.cbstopper is not None:
                self.cbstopper.set()
                time.sleep(0.06)
            self.player.stop()
            return False
        self.audioTimer = max(TStamp(0), tsx)
        self.drawAudioCursor()
        return True
    
    def drawAudioCursor(self):
        if self.audioTimer is None:
            return None
        if self.player.playing:
            FR = self.state['FrameRange']
            m1 = FR.start + (0.96 * FR.length())
            if self.audioTimer > m1:
                self.shiftX(0.85 * FR.length())
        x = self.WTC(self.audioTimer)
        FH, AL = self.FrameHeight, self.state['AudioLength']
        if self.audioTimer >= AL: # should stop
            self.player.stop()
            self.cbstopper.set()
            time.sleep(0.06)
            self.canvas.delete('audio-cursor')
            self.audioTimer = None
            return None
        self.canvas.delete('audio-cursor')
        self.canvas.create_line((x, -10, x, FH + 10), fill='green', tag='audio-cursor')
    
    def drawRuler(self):
        FR, AL = self.state['FrameRange'], self.state['AudioLength']
        HEBH = self.HorizonEndBarHeight
        TTH = self.TimeToHeight
        FW, FH = self.FrameWidth, self.FrameHeight
        HFH = self.HalfFrameHeight
        xh0, xh1 = self.WTC(TStamp()), self.WTC(AL)
        # horizontal rule
        self.canvas.create_line((-10, HFH, FW + 10, HFH))
        # draw the horizon bars
        self.canvas.create_line((xh0, HFH - HEBH, xh0, HFH + HEBH))
        self.canvas.create_line((xh1, HFH - HEBH, xh1, HFH + HEBH))
        # draw the scale
        n0 = round(max(0, FR.start.to_sec()))
        n1 = int(min(AL, FR.end).to_sec())
        for n in range(n0, n1 + 1):
            for t, h in TTH.items():
                if n % t == 0 and (FR.length() / t) <= 200:
                    ts = TStamp(puresec=n)
                    x = self.WTC(ts)
                    self.canvas.create_line((x, HFH - h, x, HFH + h))
                    break
    
    def drawCursor(self):
        if self.cursor is not None:
            self.canvas.delete(self.cursor)
        if self.mouseX is None:
            return None
        x, FH = self.mouseX, self.FrameHeight
        self.cursor = self.canvas.create_line((x, -10, x, FH + 10), fill='orange')
    
    def drawTStamps(self):
        FW, FH = self.FrameWidth, self.FrameHeight
        HFW = FW // 2
        if self.mouseX:
            ts = self.getTStampAtCursor()
            self.canvas.delete('textM')
            self.canvas.create_text(HFW, FH - 12, text=str(ts), fill='purple', tag='textM')
        FR = self.state['FrameRange']
        self.canvas.delete('textL')
        self.canvas.delete('textR')
        self.canvas.create_text(50, 10, text=str(FR.start), tag='textL')
        self.canvas.create_text(FW - 50, 10, text=str(FR.end), tag='textR')
        if self.audioTimer is not None:
            self.canvas.delete('textG')
            self.canvas.create_text(HFW, 10, text=str(self.audioTimer), fill='darkgreen', tag='textG')
    
    def drawChannel(self, channel):
        if channel == 1:
            segs, color = self.state['Ch1Segments'], 'blue'
            choff = self.HalfFrameHeight - self.ChannelOffset
        else:
            segs, color = self.state['Ch2Segments'], 'red'
            choff = self.HalfFrameHeight + self.ChannelOffset
        FR, SEBH = self.state['FrameRange'], self.SegmentEndBarHeight
        for seg in segs:
            if (FR & seg) > 0:
                x0, x1 = self.WTC(seg.start), self.WTC(seg.end)
                self.canvas.create_line((x0, choff, x1, choff), fill=color)
                self.canvas.create_line((x0, choff - SEBH, x0, choff + SEBH), fill=color)
                self.canvas.create_line((x1, choff - SEBH, x1, choff + SEBH), fill=color)
    
    def drawAllChannels(self):
        self.drawChannel(1)
        self.drawChannel(2)
    
    def focus(self):
        """Show all segments with proper scale."""
        ts0, ts1 = self.state['AudioLength'], TStamp(0)
        ch1segs, ch2segs = self.state['Ch1Segments'], self.state['Ch2Segments']
        for seg in ch1segs:
            ts0 = min(ts0, seg.start)
            ts1 = max(ts1, seg.end)
        for seg in ch2segs:
            ts0 = min(ts0, seg.start)
            ts1 = max(ts1, seg.end)
        if ts0 < ts1:
            MFRL = self.MinFrameRangeLength
            frac = 1.25; tslen = ts1 - ts0
            if tslen > 0:
                frac = max(frac, (MFRL + 0.1) / tslen)
            NFR = TInterval(ts0, ts1).scale(frac)
            NFR = self.checkNFR(NFR)
            if NFR is not None:
                self.setState(FrameRange=NFR)
    
    def getTStampAtCursor(self):
        if self.mouseX:
            return self.CTW(self.mouseX)
        return None
    
    def checkNFR(self, NFR):
        FW, AL = self.FrameWidth, self.state['AudioLength']
        r = 0.1 # margin ratio
        if AL.to_sec() / NFR.length() < 1 - 2*r:
            return None
        if NFR.length() < self.MinFrameRangeLength:
            return None
        margin = NFR.length() * r
        m0, m1 = NFR.start + margin, NFR.end + (-margin)
        if m0.to_sec() < 0:
            return NFR.shift(-m0.to_sec())
        if AL < m1:
            return NFR.shift(AL - m1)
        return NFR
    
    def scaleX(self, frac, alpha=0.5):
        NFR = self.state['FrameRange'].scale(frac, alpha)
        NFR = self.checkNFR(NFR)
        if NFR is not None:
            self.setState(FrameRange=NFR)
    
    def shiftX(self, delta):
        NFR = self.state['FrameRange'].shift(delta)
        NFR = self.checkNFR(NFR)
        if NFR is not None:
            self.setState(FrameRange=NFR)

    def handleB1(self, event):
        self.canvas.focus_set()
        print(self.cbstopper)
        if self.cbstopper is not None:
            self.cbstopper.set()
            time.sleep(0.06)
        if self.placeAudioCursor():
            self.moveAudioCursor()
    
    def handleKey(self, event):
        delta = self.state['FrameRange'].length() * 0.1
        if event.char == 'a': # move left
            self.shiftX(-delta)
        elif event.char == 'd': # move right
            self.shiftX(delta)
        elif event.char == 'f': # focus
            self.focus()
        elif event.char == ' ': # pause / resume
            if self.audioTimer is not None:
                if self.player.playing:
                    if self.cbstopper is not None:
                        self.player.stop()
                        self.cbstopper.set()
                        self.cbstopper = None
                else:
                    self.moveAudioCursor()
    
    def handleMotion(self, event):
        self.mouseX = self.canvas.canvasx(event.x)
        self.mouseY = self.canvas.canvasy(event.y)
        self.drawCursor()
        self.drawTStamps()
    
    def handleLeave(self, event):
        if self.cursor is not None:
            self.canvas.delete(self.cursor)
            self.cursor = None
        if self.textM is not None:
            self.canvas.delete(self.textM)
            self.textM = None
    
    def handleMouseWheel(self, event):
        FW = self.FrameWidth
        self.scaleX(1 + (-event.delta / 50), self.mouseX / FW)
    
    def afterSetState(self):
        self.canvas.delete('all')
        self.drawRuler()
        self.drawAllChannels()
        self.drawCursor()
        self.drawAudioCursor()
        self.drawTStamps()


class AudioVisualiser(Component):
    def __init__(self, parent):
        super().__init__(parent, 'AudioVisualiser', withLabel=True)
        self.frame.configure(text='Audio Visualiser')
        self.audioCanvas = AudioCanvas(self)
        # Grid Configuration
        self.audioCanvas.grid(row=0, column=0)
    
    def sendSegments(self, segs, channel):
        if channel == 1:
            self.audioCanvas.setState(Ch1Segments=segs)
        else:
            self.audioCanvas.setState(Ch2Segments=segs)
        self.audioCanvas.focus()
    
    def initAudioPlayer(self, filename):
        self.audioCanvas.initAudioPlayer(filename)


class TmpRoot:
    def __init__(self):
        self.root = Tk()
        self.root.title('Audio Canvas')
        # Create necessary variables for MainFrame
        self.children = []
        self.frame = self.root
        self.mainframe = AudioCanvas(self)
        # Grid Configuration
        self.mainframe.grid(row=0, column=0, sticky=NSEW)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
    
    def mainloop(self):
        self.root.mainloop()

if __name__ == '__main__':
    root = TmpRoot()
    root.mainloop()