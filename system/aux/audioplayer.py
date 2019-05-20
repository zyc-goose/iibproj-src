from mutagen.mp3 import MP3
from ..elements.TStamp import TStamp
import pygame.mixer
import os

class AudioPlayer:
    def __init__(self, filename):
        self.filename = filename
        self.path = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../audio/%s.mp3' % filename))
        audio = MP3(self.path)
        self.length = audio.info.length
        pygame.mixer.init()
        pygame.mixer.music.load(self.path)
        self.playing = False
    
    def play(self, start=0.0):
        assert isinstance(start, (int, float, TStamp))
        if isinstance(start, TStamp):
            start = start.to_sec()
        pygame.mixer.music.play(start=start)
        self.playing = True
    
    def pause(self):
        pygame.mixer.music.pause()
        self.playing = False

    def unpause(self):
        pygame.mixer.music.unpause()
        self.playing = False
    
    def stop(self):
        pygame.mixer.music.stop()
        self.playing = False