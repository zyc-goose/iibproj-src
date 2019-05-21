# Alignment Algorithm Evaluation

from ...system.elements.Match import Matches
from ...system.elements.TInterval import TInterval, TIntervalGroup

class AlignEval:
    """Alignment Algorithm Evaluation."""
    def __init__(self, ref, hyp):
        self.ref = ref
        self.hyp = hyp
    
    def find_matching_segments(self):
        """Find ref segments for each hyp chunks."""
        hyp_matched_segs = [TIntervalGroup() for i in range(len(self.hyp))]
        for gid_ref, match_ref in enumerate(self.ref):
            bg_ref = match_ref.bbox_group
            max_gid, max_area = -1, 0
            for gid_hyp, bg_hyp in enumerate(self.hyp.get_bbox_groups()):
                rx, ry = bg_ref.page_range(), bg_hyp.page_range()
                if ry[0] > rx[1]:
                    break
                area = (bg_ref & bg_hyp)
                if area > max_area:
                    max_gid, max_area = gid_hyp, area
            if max_gid != -1:
                hyp_matched_segs[max_gid].extend(match_ref.tinterval_group)
        for seg in hyp_matched_segs:
            seg.reduce()
        return hyp_matched_segs
                
    
    def _type_check(self):
        assert isinstance(self.ref, Matches)
        assert isinstance(self.hyp, Matches)
