"""
    cracken.generator
    ~~~~~~~~~~~~~~~~~

    This module implements the PreTerminalHeap class, which generates
    preterminal guesses for likely password patterns.
"""
from __future__ import absolute_import

from collections    import defaultdict

import heapq
import re

class PreTerminalHeap(object):
    """PreTerminalHeap objects generate a stream of preterminal guesses.

    Given a probablistic grammar, a PreTerminalHeap will generate a set of
    preterminal guesses, which will be provided in order of decreasing 
    probability.
    """
    def __init__(self, base_structs, prob_grammar):
        self._base_structs = []
        self._prob_grammar = defaultdict(list)
        self._queue = []
        
        with open(base_structs) as f:
            for line in f:
                struct, prob = line.split()       
                self._base_structs.append(
                    (struct.split('|'), float(prob))
                )
        
        with open(prob_grammar) as f:
            for line in f:
                nterm, term, prob = line.split()
                self._prob_grammar[nterm].append((term, float(prob)))
                
    
    def build_preterminal(self, bs_idx, nt_idxs):
        """Given a base structure index and an index for each non-terminal in
        that base structure, return the resultant preterminal"""
        res, cur_nt_idx = "", 0
        for nt in self._base_structs[bs_idx][0]:
            if "L" in nt:
                res += '|{}|'.format(nt)
            else:
                res += self._prob_grammar[nt][nt_idxs[cur_nt_idx]][0]
                cur_nt_idx += 1
        return res


    def calc_pt_prob(self, bs_idx, nt_idxs):
        """Given a base structure index and an index for each non-terminal in 
        that base structure, return the probability of that the resultant
        preterminal"""
        prod = 1
        l = [nt for nt in self._base_structs[bs_idx][0] if "L" not in nt]
        for nt, idx in zip(l, nt_idxs):
            prod *= self._prob_grammar[nt][idx][1]
        return prod

    
    def __iter__(self):
        for idx, bs in enumerate(self._base_structs):
            nt_idxs = [0 for nt in bs[0] if "L" not in nt]
            heapq.heappush(self._queue, (
                (1 - self.calc_pt_prob(idx, nt_idxs)), 
                idx, nt_idxs
            ))
        
        return self

    
    def next(self):
        """Pull the next preterminal from the heap, inserting new preterminals
        which are the next most likely forms of that preterminal"""
        try:
            prob, bs_idx, nt_idxs = heapq.heappop(self._queue)
        except IndexError:
            raise StopIteration()

        l = [nt for nt in self._base_structs[bs_idx][0] if "L" not in nt]
        for i, nt in enumerate(l):
            if nt_idxs[i] + 1 < len(self._prob_grammar[nt]):
                new_nt_idxs = list(nt_idxs)
                new_nt_idxs[i] += 1
                new_prob = 1 - self.calc_pt_prob(bs_idx, new_nt_idxs)

                if (new_prob, bs_idx, new_nt_idxs) not in self._queue:
                    heapq.heappush(self._queue, (new_prob, bs_idx, new_nt_idxs))

        return self.build_preterminal(bs_idx, nt_idxs)

