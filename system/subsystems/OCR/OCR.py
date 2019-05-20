from ...elements.BBox import BBoxGroups

class OCR:
    """Super class for all OCR instances."""

    def __init__(self, path=None):
        self.path = path
        self.result = None
    
    def process(self):
        """Run the OCR engine and return the result."""
        self.result = BBoxGroups()
        return self.result
    
    def reset(self):
        """Clear the generated result if exists."""
        self.result = None