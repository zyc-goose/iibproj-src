# Alignment Algorithm Evaluation

from ...system.elements.Match import Matches
from ...system.elements.TInterval import TInterval, TIntervalGroup
from ...system.subsystems.Align.Align import Align
from ...system.aux.reflabel import RefLabel
from ...system.cache.Cache import global_cache

class AlignEval:
    """Alignment Algorithm Evaluation."""
    def __init__(self, label, align):
        self.label = label
        self.align = align
        self._type_check()
        self.result = None
        self.hyp_matched_segs = None
        self.cache = global_cache
        self.update_cache_key()
        self.update_inputs()
    
    def update_cache_key(self):
        self.cache_key = 'AlignEval(label=%s,align=%s)' % (self.label.cache_key, self.align.cache_key)
    
    def update_inputs(self):
        self.ref = self.label.filebuf
        self.hyp = self.align.result
    
    def evaluate(self):
        self.update_cache_key()
        self.update_inputs()
        if self.cache_key in self.cache:
            self.hyp_matched_segs = self.segs_from_obj(self.cache[self.cache_key])
        else:
            self.hyp_matched_segs = self.find_matching_segments()
            self.cache[self.cache_key] = self.segs_to_obj(self.hyp_matched_segs)
        self.result = dict(recall=self.compute_recall_rate())
        return self.result
    
    def segs_to_obj(self, segs):
        return [seg.to_obj() for seg in segs]
    
    def segs_from_obj(self, obj):
        return [TIntervalGroup(x, from_obj=True) for x in obj]
    
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
                hyp_matched_segs[max_gid].extend(match_ref.tinterval_group.copy())
            print('%d -> %d' % (gid_ref, max_gid))
        for seg in hyp_matched_segs:
            seg.reduce()
        return hyp_matched_segs
    
    def compute_recall_rate(self):
        len_total = sum(seg.length() for seg in self.hyp_matched_segs)
        len_recall = 0
        for tg_ref, match_hyp in zip(self.hyp_matched_segs, self.hyp):
            tg_hyp = match_hyp.tinterval_group
            len_recall += (tg_ref & tg_hyp)
        return len_recall / len_total
    
    def _type_check(self):
        assert isinstance(self.label, RefLabel)
        assert isinstance(self.align, Align)
