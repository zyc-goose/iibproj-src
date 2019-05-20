from ...elements.Match import Match, Matches
from ..OCR.OCR import OCR
from ..Speech.Speech import Speech
from ...cache.Cache import Cache

class Align:
    """Super class for all Align instances."""

    def __init__(self, ocr, speech):
        self.ocr, self.speech = ocr, speech
        self._type_check()
        self.result = None
    
    def process(self):
        """Run the Alignment Algorithm and return the result."""
        self.ocr.process()
        self.speech.process()
        self.result = Matches()
        return self.result
    
    def reset(self):
        """Clear the generated result if exists."""
        self.result = None
    
    def _type_check(self):
        assert isinstance(self.ocr, OCR)
        assert isinstance(self.speech, Speech)
