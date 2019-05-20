from .subsystems.Align.AlignBasic import AlignBasic
from .subsystems.OCR.OCRTess import OCRTess
from .subsystems.Speech.SpeechGC import SpeechGC

from pprint import pprint

class System:
    """The Integrated System."""

    def __init__(self, filename):
        self.ocr = OCRTess(filename)
        self.speech = SpeechGC(filename)
        self.align = AlignBasic(self.ocr, self.speech)
    
    def run(self):
        """Run the system."""
        matches = self.align.process()
        pprint(matches)
        
if __name__ == '__main__':
    filename = 'lecture1'
    system = System(filename)
    system.run()