import os, time, json
from ..elements.Match import Matches

class RefLabel:
    def __init__(self, filename):
        self.filename = filename
        self.path = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../labels/%s.json' % filename))
        self.reopen()

    def update_cache_key(self):
        self.cache_key = time.asctime(time.gmtime(os.path.getmtime(self.path)))
    
    def reopen(self):
        with open(self.path, 'r') as fin:
            self.filebuf = Matches(json.load(fin), from_obj=True)
        self.update_cache_key()
