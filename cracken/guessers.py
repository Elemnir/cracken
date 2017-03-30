"""
    cracken.guessers
    ~~~~~~~~~~~~~~~~

    This module provides several guesser iterators which, given an appropriate 
    input, will generate a number of password guesses based on their input.
"""
import collections
import re

class PreTerminalGuesser(object):
    """Iterable which generates passwords by combining a preterminal with words
    from a dictionary.
    """
    glossary = None
    
    def __init__(self, preterminal):
        self.slots = [
            term for term in preterminal.split("|")
            if re.search(r"L\d+", term)
        ]
        self.idxs = [0 for term in self.slots]
        self.lens = [int(term[1:]) for term in self.slots]
        self.fmtstr = re.sub(r"\|L\d+\|", "{}", preterminal)
    
    
    @classmethod
    def load_glossary(cls, fname):
        """Class method which loads the glossary of words used by instances
        for generating password guesses. The glossary should consist of lines 
        of the form:
        
            <length> <word>
        """
        cls.glossary = collections.defaultdict(list)
        with open(fname) as f:
            for line in f:
                cnt, word = line.split()
                cls.glossary[int(cnt)].append(word)

    
    def __iter__(self):
        self.idxs = [0 for term in self.slots]
        self.exhausted = False
        return self

    
    def next(self):
        if self.exhausted:
            raise StopIteration()

        guess = self.fmtstr.format(
            *[self.glossary[l][self.idxs[i]] for i, l in enumerate(self.lens)]
        )

        # Increment the indices
        for i in reversed(range(len(self.idxs))):
            self.idxs[i] += 1
            if self.idxs[i] >= len(self.glossary[self.lens[i]]):
                self.idxs[i] %= len(self.glossary[self.lens[i]])
            else:
                break

        # Break once we've tried all possible words in the dictionary
        if len(self.idxs) == 0 or all(i == 0 for i in self.idxs):
            self.exhausted = True
        
        return guess


class ManglingGuesser(object):
    """Iterable which generates passwords by applying transformation rules.
    
    Iterating over a ManglingGuesser instance will enumerate all combinations
    of the mangling rules registered to the class with `add_rule`. Rules are
    applied in the order they were registered.
    """
    rules = []

    def __init__(self, word):
        self.word = word
    
    
    @classmethod
    def add_rule(cls, rule):
        """Add a callable `rule` to the rules. The rule should accept a string, 
        and return a string with the rule's transformation applied.
        """
        cls.rules.append(rule)

    
    def __iter__(self):
        self.val = 0
        self.lim = 2 ** len(self.rules)
        return self

    
    def next(self):
        if self.val == self.lim:
            raise StopIteration()
        
        # Rule combinations are enumerated by treating a counter as a bit mask 
        # then applying that mask to the ruleset to filter which rules should 
        # be applied this round.
        guess = self.word
        bit_str = bin(self.val)[2:].rjust(len(self.rules), '0')
        for rule, bit in zip(self.rules, bit_str):
            if bit == "1":
                guess = rule(guess)

        self.val += 1
        return guess
