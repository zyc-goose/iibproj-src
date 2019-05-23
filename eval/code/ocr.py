# OCR Evaluation

from ...system.elements.BBox import BBoxGroups
from ...system.subsystems.Align.Align import Align
from ...system.aux.mydiff import MyDiff
from ...system.aux.reflabel import RefLabel
from ...system.cache.Cache import global_cache

class OCREval:
    """OCR Evaluation."""
    def __init__(self, label, align):
        self.label = label
        self.align = align
        self._type_check()
        self.result = None
        self.cache = global_cache
        self.update_cache_key()
        self.update_inputs()
    
    def update_cache_key(self):
        self.cache_key = 'OCREval(label=%s,align=%s)' % (self.label.cache_key, self.align.cache_key)
    
    def update_inputs(self):
        self.ref = self.label.filebuf.get_bbox_groups()
        self.hyp = self.align.result.get_bbox_groups()
    
    def evaluate(self):
        self.update_cache_key()
        self.update_inputs()
        if self.cache_key in self.cache:
            self.result = self.cache[self.cache_key]
        else:
            self.result = dict(
                recall=self.compute_recall_rate(),
                WER=self.compute_text_WER()
            )
            self.cache[self.cache_key] = self.result
        return self.result

    def compute_recall_rate(self):
        """Calculate BBox recall rate."""
        area_total = self.ref.area()
        area_recall = (self.ref & self.hyp)
        return area_recall / area_total
    
    def compute_text_WER(self, wI=0.5, wD=0.5, wS=1):
        """Calculate WER of the OCR text output."""
        def jwf(x, y):
            assert not (x is None and y is None)
            if x is None:
                return -wI
            if y is None:
                return -wD
            return 0 if x == y else -wS
        X, Y = self.ref.words(), self.hyp.words()
        diff = MyDiff(X, Y, jwf)
        diff_align = diff.solve()
        # calculate (I, D, S)
        numI = sum(map(lambda x: x[0] is None, diff_align)) * wI
        numD = sum(map(lambda x: x[1] is None, diff_align)) * wD
        numS = sum(map(lambda x: bool(x[0] and x[1] and x[0] != x[1]), diff_align))
        numIDS = numI + numD + numS
        numTotal = len(X)
        return dict(all=numIDS/numTotal, I=numI/numTotal, D=numD/numTotal, S=numS/numTotal)
    
    def _type_check(self):
        assert isinstance(self.label, RefLabel)
        assert isinstance(self.align, Align)