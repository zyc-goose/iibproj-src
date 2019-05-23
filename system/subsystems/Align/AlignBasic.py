from .Align import Align
from ...aux.mydiff import MyDiff
from ...elements.BBox import BBoxWord, BBoxWordInfo
from ...elements.WStamp import WStamp
from ...elements.Match import Match, Matches
from ...elements.TInterval import TIntervalGroup, TInterval
from ...elements.TStamp import TStamp
from ...cache.Cache import global_cache
from pprint import pprint
from math import exp, sqrt
import difflib

class AlignBasic(Align):
    """The baseline alignment algorithm based on diff."""
    def __init__(self, ocr, speech):
        super().__init__(ocr, speech)
        self.word_lists = WordLists()
        self.cache = global_cache
        self.set_params()
    
    def update_cache_key(self):
        params_str = 'params(gauss={gauss},common={common},key={key})'.format(**self.params)
        self.cache_key = 'AlignBasic(%s,%s,%s)' % (self.ocr.cache_key, self.speech.cache_key, params_str)
    
    def set_params(self, gauss=None, common=None, key=None):
        self.params = dict(gauss=gauss, common=common, key=key)
        self.set_jwf(**self.params)
        self.update_cache_key()
    
    def process(self):
        self.ocr.process()
        self.speech.process()
        self.update_cache_key()
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

    def set_jwf(self, gauss=None, common=None, key=None):
        # JWF
        def jwf(x, y):
            if x is None or y is None or x.word != y.word:
                return 0
            # now x.word == y.word
            if isinstance(y, BBoxWord): # swap
                x, y = y, x
            word = x.word
            ret = 1
            # Penalise matching common words
            if common and common > 0 and (word in self.word_lists.common_words):
                ret *= common
            print('common', ret)
            # Reward matching key words
            if key and key > 0 and (word in self.word_lists.key_words):
                ret *= key
            print('key', ret)
            # Time Constraint
            if gauss and gauss > 0:
                s = gauss
                f = lambda d: exp((-0.5*d*d) / (s*s)) # no need to normalise
                y_relpos = y.tstamp.to_sec() / self.speech.audio_len
                dx = (x.info.relpos - y_relpos) * 50 # assume a 50min lecture
                ret *= f(dx)
            print('gauss', ret)
            return ret
        self.jwf = jwf


import os, json

class WordLists:
    def __init__(self):
        self.pathdir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../../data/wordlists'))
        self.path1 = os.path.join(self.pathdir, 'common_words.json')
        self.path2 = os.path.join(self.pathdir, 'key_words.json')
        with open(self.path1, 'r') as f1:
            self.common_words = json.load(f1)
        with open(self.path2, 'r') as f2:
            self.key_words = json.load(f2)