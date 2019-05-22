from .TStamp import TStamp

class WStamp:
    """Word with TimeStamp as in Transcript.
    attributes:
        word - the recognised word
        tstamp - starting time of the word
    """

    def __init__(self, word, tstamp, from_obj=False):
        self.word = word
        if from_obj:
            self.tstamp = TStamp(**tstamp)
        else:
            self.tstamp = tstamp
        self._type_check()
    
    def to_obj(self):
        return dict(word=self.word, tstamp=self.tstamp.to_obj())

    def __eq__(self, other):
        return self.word == other.word
    
    def __str__(self):
        return 'WStamp(word=%s, tstamp=%s)' % (self.word, self.tstamp)
    
    def __repr__(self):
        return self.__str__()
        
    def _type_check(self):
        if not isinstance(self.word, str):
            raise TypeError('word should be a str')
        if not isinstance(self.tstamp, TStamp):
            raise TypeError('tstamp should be a TStamp object')


class WStamps(list):
    """A List of WStamp objects."""

    def __init__(self, wstamps=(), from_obj=False):
        if from_obj:
            list.__init__(self, map(lambda x: WStamp(**x, from_obj=True), wstamps))
        else:
            list.__init__(self, wstamps)
    
    def to_obj(self):
        return list(map(lambda x: x.to_obj(), self))

    