import time

class TStamp:
    """TimeStamp as in Transcript.
    attributes:
        min - minutes
        sec - seconds
        msec - milliseconds
    """

    def __init__(self, puresec=None, min=0, sec=0, msec=0):
        if puresec is not None:
            self.set_from_sec(puresec)
        else:
            self.set(min, sec, msec)
        self._type_check()
    
    def to_obj(self):
        return dict(min=self.min, sec=self.sec, msec=self.msec)
    
    def to_sec(self):
        """return timestamp in seconds (float)."""
        return self.min*60 + self.sec + self.msec/1000
    
    def set(self, min=0, sec=0, msec=0):
        min, sec, msec = int(min), int(sec), int(msec)
        self.min, self.sec, self.msec = min, sec, msec
    
    def set_from_sec(self, puresec=0):
        whole = int(puresec)
        frac = puresec - whole
        self.min = whole // 60
        self.sec = whole % 60
        self.msec = int(1000*frac)
    
    def __add__(self, other):
        """Add two timestamps together (rhs can be a number)."""
        assert isinstance(other, (int, float, TStamp))
        if isinstance(other, TStamp):
            other = other.to_sec()
        return TStamp(puresec=(self.to_sec() + other))

    def __sub__(self, other):
        """return time difference in seconds."""
        return self.to_sec() - other.to_sec()

    def __lt__(self, other):
        return (self - other) < 0

    def __le__(self, other):
        return (self - other) <= 0
    
    def __str__(self):
        return '(%d:%02d:%03d)' % (self.min, self.sec, self.msec)
    
    def __repr__(self):
        return self.__str__()

    def _type_check(self):
        if not isinstance(self.min, int):
            raise TypeError('min should be an int')
        if not isinstance(self.sec, int):
            raise TypeError('sec should be an int')
        if not isinstance(self.msec, int):
            raise TypeError('msec should be an int')


if __name__ == '__main__':
    t1 = TStamp()
    for i in range(10):
        t1 += -25.378
        print(t1)
    t2 = TStamp(puresec=-45.678)
    print(t2 + 46.789)
    