from .TStamp import TStamp

class TInterval:
    """Time Interval specified by a starting TStamp and an ending TStamp.
    attributes:
        start - the starting TStamp object
        end - the ending TStamp object
    """
    
    def __init__(self, start=None, end=None, from_obj=False):
        if from_obj:
            self.start = TStamp(**start)
            self.end = TStamp(**end)
        else:
            self.start = start if start else TStamp()
            self.end = end if end else TStamp()
        self._type_check()

    def length(self):
        return self.end - self.start
    
    def to_obj(self):
        return dict(start=self.start.to_obj(), end=self.end.to_obj())
    
    def contains(self, ts):
        return ts >= self.start and ts <= self.end

    def scale(self, frac, alpha=0.5):
        delta = (frac - 1) * self.length()
        return TInterval(self.start + (-delta * alpha), self.end + (delta * (1 - alpha)))
    
    def shift(self, delta):
        return TInterval(self.start + delta, self.end + delta)
    
    def __and__(self, other):
        ts1 = max(self.start, other.start)
        ts2 = min(self.end, other.end)
        return max(0, ts2 - ts1)
    
    def __str__(self):
        return 'TInterval(start=%s, end=%s)' % (self.start, self.end)
    
    def __repr__(self):
        return self.__str__()

    def _type_check(self):
        if not isinstance(self.start, TStamp):
            raise TypeError('start should be a TStamp object')
        if not isinstance(self.end, TStamp):
            raise TypeError('end should be a TStamp object')


class TIntervalGroup(list):
    """Group of TInterval objects (atomic element for alignment)."""
    
    def __init__(self, group=(), ISE=False):
        """ISE: Initial Single Element"""
        list.__init__(self, map(lambda x: TInterval(**x, from_obj=True), group))
        if len(group) == 0 and ISE:
            self.append(TInterval())
    
    def to_obj(self):
        return list(map(lambda x: x.to_obj(), self))

    def reduce(self):
        """Re-organise and merge the intersecting intervals."""
        res = []
        for elem in sorted(self, key=lambda x: x.start):
            if len(res) and elem.start <= res[-1].end <= elem.end:
                res[-1].end = elem.end
            elif len(res) == 0 or res[-1].end < elem.start:
                res.append(elem)
        list.__init__(self, res)

