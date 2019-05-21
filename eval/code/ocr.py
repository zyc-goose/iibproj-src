# OCR Evaluation

from ...system.elements.BBox import BBoxGroups
from ...system.aux.mydiff import MyDiff

class OCREval:
    """OCR Evaluation."""
    def __init__(self, ref, hyp):
        self.ref = ref
        self.hyp = hyp
        self.result = None
        self._type_check()
    
    def evaluate(self):
        self.result = dict(
            recall=self.compute_recall_rate(),
            WER=self.compute_text_WER()
        )
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
        align = diff.solve()
        # calculate (I, D, S)
        numI = sum(map(lambda x: x[0] is None, align)) * wI
        numD = sum(map(lambda x: x[1] is None, align)) * wD
        numS = sum(map(lambda x: x and y and x != y, align))
        numIDS = numI + numD + numS
        numTotal = len(X)
        return dict(all=numIDS/numTotal, I=numI/numTotal, D=numD/numTotal, S=numS/numTotal)
    
    def _type_check(self):
        assert isinstance(self.ref, BBoxGroups)
        assert isinstance(self.hyp, BBoxGroups)