from ...elements.WStamp import WStamps

class Speech:
    """Super class for all Speech Recogniser instances."""

    def __init__(self, path=None):
        self.path = path
        self.result = None
    
    def process(self):
        """Run the Speech Recogniser and return the result."""
        self.result = WStamps()
        return self.result
    
    def reset(self):
        """Clear the generated result if exists."""
        self.result = None