# My own implementation of the 'diff' algorithm
# Base algorithm: Hirschberg's algorithm (optimised Needleman-Wunsch algorithm)
#
# JWF: Joint Weight (score) Function f(x, y):
#
#      f(None, y) : insertion score    (I)
#      f(x, None) : deletion score     (D)
#      f(x, y)    : substitution score (S)
#
# The algorithm finds the optimal alignment of X and Y based on f(x, y)
# by maximising the total score of the alignment.
#
# Note: x from X;  y from Y.

import numpy as np

class MyDiff:
    """My own diff implementation."""
    def __init__(self, X, Y, jwf):
        self.X = X
        self.Y = Y
        self.jwf = jwf  # joint weight function f(x, y)
    
    def solve(self):
        return self.Hirschberg(self.X, self.Y)
    
    def Hirschberg(self, X, Y):
        if len(X) == 0:
            return [(None, y) for y in Y]
        if len(Y) == 0:
            return [(x, None) for x in X]
        if len(X) == 1:
            return self.NW_align_unity_X(X[0], Y)
        if len(Y) == 1:
            return self.NW_align_unity_Y(X, Y[0])
        N1, N2 = len(X), len(Y)
        xmid = (N1 // 2)
        scoreL = self.NW_score(X[0:xmid], Y)
        scoreR = self.NW_score(X[xmid:][::-1], Y[::-1])
        ymid = (scoreL + np.flip(scoreR, 0)).argmax()
        return self.Hirschberg(X[0:xmid], Y[0:ymid]) + self.Hirschberg(X[xmid:], Y[ymid:])
    
    def NW_score(self, X, Y):
        """Return the last line of the NW score matrix (dim(ret) == dim(Y) + 1)."""
        X = [None] + X;  N1 = len(X) # i
        Y = [None] + Y;  N2 = len(Y) # j
        score = np.zeros(N2)
        # initialise first line (i = 0, X[i] = None)
        for j in range(1, N2):
            score[j] = score[j - 1] + self.jwf(None, Y[j])
        # main loop (i, j)
        for i in range(1, N1):
            score_sub = score[0] # score[i - 1, j - 1]
            score[0] = score[0] + self.jwf(X[i], None)
            for j in range(1, N2):
                scoreD = score[j]     + self.jwf(X[i], None) # score[i - 1, j]
                scoreI = score[j - 1] + self.jwf(None, Y[j]) # score[i - 1, j]
                scoreS = score_sub    + self.jwf(X[i], Y[j]) # score[i - 1, j - 1]
                score_sub = score[j]
                score[j] = max(scoreD, scoreI, scoreS)
        return score
    
    def NW_align_unity_X(self, x, Y):
        """NW alignment when len(X) = 1, x = X[0]."""
        align = [(None, y) for y in Y]
        gain_best, j_best = self.jwf(x, None), -1
        for j, y in enumerate(Y):
            gain = self.jwf(x, y) - self.jwf(None, y)
            if gain > gain_best:
                gain_best, j_best = gain, j
        if j_best == -1:
            return [(x, None)] + align
        align[j_best] = (x, Y[j_best])
        return align
    
    def NW_align_unity_Y(self, X, y):
        """NW alignment when len(Y) = 1, y = Y[0]."""
        align = self.NW_align_unity_X(y, X)
        return [x[::-1] for x in align]
    
    def _type_check(self):
        assert isinstance(self.X, list)
        assert isinstance(self.Y, list)
        assert callable(self.jwf)


if __name__ == '__main__':
    def jwf(x, y):
        if x is None or y is None:
            return -2
        if x == y:
            return 2
        return -1
    # test 1
    X = list('AGTACGCA') # AGTACGCA
    Y = list('TATGC')    # --TATGC-
    diff = MyDiff(X, Y, jwf)
    print(diff.solve())
    # test 2
    def jwf2(x, y):
        return 1 if x == y else -1
    X = list('GCATGCU') #
    Y = list('GATTACA') #
    diff2 = MyDiff(X, Y, jwf2)
    print(diff2.solve())