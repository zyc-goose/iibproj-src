# mywer.py
#
# This script implements WER calculation based on Levenshtein Distance
# which includes percentage information of insertions (I), deletions (D)
# and substitutions (S)

import re
from collections import namedtuple

# Definition of my own WER object
# MyWER = namedtuple('MyWER', 'WER, IR, DR, SR')
class MyWER:
    def __init__(self, WER=0, IR=0, DR=0, SR=0):
        self.WER, self.IR, self.DR, self.SR = WER, IR, DR, SR
    
    def __add__(self, other):
        return MyWER(self.WER + other.WER, self.IR + other.IR, self.DR + other.DR, self.SR + other.SR)
    
    def __mul__(self, other):
        return MyWER(self.WER*other, self.IR*other, self.DR*other, self.SR*other)
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __str__(self):
        return 'MyWER(WER=%s, IR=%s, DR=%s, SR=%s)' % (self.WER, self.IR, self.DR, self.SR)


# Definition of 3-tuple: (I, D, S)
class EditDist:
    def __init__(self, I=0, D=0, S=0):
        self.I, self.D, self.S = I, D, S
    
    def __add__(self, other):
        return EditDist(self.I + other.I, self.D + other.D, self.S + other.S)
    
    def __mul__(self, other):
        return EditDist(self.I*other, self.D*other, self.S*other)
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __lt__(self, other):
        return self.getSum() < other.getSum()
    
    def __str__(self):
        return 'I=%d, D=%d, S=%d' % (self.I, self.D, self.S)

    def getSum(self):
        return self.I + self.D + self.S


def str2list(s):
    if not isinstance(s, str):
        raise TypeError('input argument must be str')
    return re.sub(r'[^\w]', ' ', s.lower()).split()


def getEditDist(hyp, ref):
    """Calculate (I, D, S) based on hypothesis and reference.
    Here hyp and ref are both lists."""
    if not (isinstance(hyp, list) and isinstance(ref, list)):
        raise TypeError('both arguments must be lists')
    # define some consts
    oneI, oneD, oneS = EditDist(I=1), EditDist(D=1), EditDist(S=1)
    # DP init
    dp = [EditDist(D=i+1) for i in range(len(ref))]
    # DP main loop
    # use hyp[i] and ref[j] to index elements
    prevdp = EditDist() # buffer for dp[i - 1, j - 1], initially 0
    for i in range(len(hyp)):
        for j in range(len(ref)):
            # I: dp[i, j] = dp[i - 1, j] + (1, 0, 0)
            ansI = dp[j] + oneI
            # D: dp[i, j] = dp[i, j - 1] + (0, 1, 0)
            ansD = (dp[j - 1] if j > 0 else (i+1)*oneI) + oneD
            # S: dp[i, j] = dp[i - 1, j - 1] + (0, 0, hyp[i] != ref[j])
            ansS = prevdp + oneS*(hyp[i] != ref[j])
            # prepare dp[i - 1, j - 1] for next iteration
            prevdp = dp[j]
            # calculate dp[i, j]
            dp[j] = min(ansI, ansD, ansS)
    return dp[-1]

def getWER(hyp, ref):
    """Here hyp & ref are strings"""
    hyp, ref = str2list(hyp), str2list(ref)
    res = getEditDist(hyp, ref)
    I, D, S = res.I, res.D, res.S
    N = len(ref)
    return MyWER((I+D+S)/N, I/N, D/N, S/N)
    
if __name__ == '__main__':
    s1 = 'what are you doing now'
    s2 = 'what you doing yesterday morning'
    res = getEditDist(str2list(s1), str2list(s2))
    print(res)
    print(getWER(s1, s2))
