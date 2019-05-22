from .Align import Align
from ...aux.mydiff import MyDiff
from ...elements.BBox import BBoxWord, BBoxWordInfo
from ...elements.WStamp import WStamp
from ...elements.Match import Match, Matches
from ...elements.TInterval import TIntervalGroup, TInterval
from ...elements.TStamp import TStamp
from ...cache.Cache import global_cache
from pprint import pprint
import difflib

class AlignBasic(Align):
    """The baseline alignment algorithm based on diff."""
    def __init__(self, ocr, speech, jwf_name='basic-diff'):
        super().__init__(ocr, speech)
        self.set_jwf(jwf_name)
        self.jwf_name = jwf_name
        self.cache = global_cache
        self.update_cache_key()
    
    def update_cache_key(self):
        self.cache_key = 'AlignBasic(%s,%s,jwf=%s)' % (self.ocr.cache_key, self.speech.cache_key, self.jwf_name)
    
    def process(self):
        self.update_cache_key() # update hashkey first
        self.ocr.process()
        self.speech.process()
        self.result = self.compute_matches(self.find_pivots())
        return self.result
    
    def compute_matches(self, pivots):
        X, Y = self.ocr.result, self.speech.result
        matches = Matches()
        for bg in X:
            matches.append(Match(bg, TIntervalGroup([TInterval()], from_obj=False)))
        tail = (BBoxWord(''), WStamp('', TStamp(puresec=self.speech.audio_len)))
        tail[0].info.set(gid=len(matches), wid=0, glen=0)
        pivots.append(tail)
        prev_gid, prev_weight = -1, 0
        prev_ts = TStamp() # initial 0
        for bword, wstamp in pivots:
            cur_gid = bword.info.gid
            cur_weight = bword.info.wid
            cur_ts = wstamp.tstamp
            if prev_gid != cur_gid:
                weights = [prev_weight]
                for gid in range(prev_gid + 1, cur_gid):
                    weights.append(len(X[gid].words()))
                weights.append(cur_weight)
                sum_of_weights = sum(weights)
                ts_gap = cur_ts - prev_ts # in float, > 0
                if sum_of_weights == 0: # assign uniform weights if sum = 0
                    for i in range(len(weights)):
                        weights[i] = 1 
                    sum_of_weights = len(weights)
                ts = prev_ts + ((weights[0] / sum_of_weights) * ts_gap)
                if prev_gid != -1:
                    matches[prev_gid].tinterval_group[0].end = ts
                for gid in range(prev_gid + 1, cur_gid):
                    matches[gid].tinterval_group[0].start = ts
                    ts = ts + ((weights[gid - prev_gid] / sum_of_weights) * ts_gap)
                    matches[gid].tinterval_group[0].end = ts
                if cur_gid < len(matches):
                    matches[cur_gid].tinterval_group[0].start = ts
            prev_gid = cur_gid
            prev_weight = bword.info.glen - bword.info.wid
            prev_ts = cur_ts
        pivots.pop()
        return matches
    
    def find_diff_align(self):
        if self.cache_key in self.cache: # try to find in cache
            cached_raw = self.cache[self.cache_key]
            map_f = lambda T, x: T(**x, from_obj=True) if x is not None else None
            return [(map_f(BBoxWord, a), map_f(WStamp, b)) for a, b in cached_raw]
        X = self.ocr.result.words()
        Y = self.speech.result
        diff = MyDiff(X, Y, self.jwf)
        diff_align = diff.solve()
        map_f = lambda x: x.to_obj() if x is not None else None
        self.cache[self.cache_key] = [(map_f(a), map_f(b)) for a, b in diff_align]
        return diff_align
    
    def find_pivots(self):
        diff_align = self.find_diff_align()
        pf = lambda x: (x[0] is not None) and (x[1] is not None) and (x[0].word == x[1].word)
        pivots = list(filter(pf, diff_align))
        return pivots

    def set_jwf(self, jwf_name):
        # basic-diff
        def jwf_basic_diff(x, y):
            if x is None or y is None:
                return 0
            return 1 if x.word == y.word else 0
        # jwf dict
        if jwf_name == 'basic-diff':
            self.jwf = jwf_basic_diff