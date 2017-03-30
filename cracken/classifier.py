"""
    cracken.classifier
    ~~~~~~~~~~~~~~~~~

    This module implements the classify function, which takes a file containing
    passwords in plaintext and generates a glossary, grammar, and set of base
    structures, based on the passwords.

    Can be invoked directly as `python cracken/classifier.py passwords.txt` to
    classify the contents of `passwords.txt`. 
"""
import collections
import functools
import re

def classify(wordfile, structfile="base_structs.txt", 
        grammarfile="prob_grammar.txt", glossaryfile="glossary.txt"):
    """Generates profiling information for other cracken utilities.

    Reads plaintext passwords from `wordfile`, and uses them to generate
    a glossary, as well as a collection of base structures ordered by 
    probability and a probabilistic grammar mapping to the non-terminals in the 
    base structures. Parameters control the file names to which profiling will 
    be written.
    """
    bases = collections.defaultdict(float)
    gloss = collections.defaultdict(set)
    probs = collections.defaultdict(
        functools.partial(collections.defaultdict, float)
    )

    total = 0

    # Parse the words
    with open(wordfile) as f:
        for word in f:
            total += 1
            word = word.strip()

            # Tokenize the input string
            s = re.sub(r'[A-Z]', r'C', word)
            s = re.sub(r"[a-z']", r'L', s)
            s = re.sub(r'[0-9]', r'D', s)
            s = re.sub(r'[_\W]',  r'S', s)
            
            #print s
            # Reduce the string, i.e. "LLLLDDD"->"L4D3"
            new, prev, cnt = s[0], s[0], 1
            for c in s[1:]:
                if c != prev:
                    new += str(cnt) + '|' + c
                    cnt = 0
                cnt += 1
                prev = c
            
            new += str(cnt)
            bases[new] += 1

            # Parse the string components into the probability structures
            i = 0
            for ident in new.split('|'):
                cnt = int(ident[1:])
                if ident[0] == "L":
                    gloss[cnt].add(word[i:i+cnt])
                else:
                    probs[ident][word[i:i+cnt]] += 1
                i += cnt

    # Write the base structures with their probabilities
    with open(structfile, "w") as f:
        for c in sorted(bases, key=bases.get, reverse=True):
            f.write("{:20} {}\n".format(c, bases[c]/total))

    # Write the glossary
    with open(glossaryfile, "w") as f:
        for length in sorted(gloss):
            for word in sorted(gloss[length]):
                f.write("{:3} {}\n".format(length, word))

    # Write the probabilistic grammar
    with open(grammarfile, "w") as f:
        for nterm in sorted(probs):
            total = sum(probs[nterm].values())
            for term in sorted(probs[nterm], key=probs[nterm].get, reverse=True):
                f.write("{:3} {:10} {}\n".format(nterm, term, probs[nterm][term]/total))
            
            
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("passfile")
    args = parser.parse_args()
    classify(args.passfile)
