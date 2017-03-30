import base64
import binascii
import hashlib
import re

from cracken.guessers import PreTerminalGuesser, ManglingGuesser

# Taken from packet captures
challenge = "1092789947"
hash1 = binascii.hexlify(
    base64.b64decode("/AJj/qta3G2RHNdje8AfPeIkIgFct4u03+ceN9jQA4Q=")
)
guessfmtstr = "TheLimpDiskettes:" + challenge + ":{}"

# Load the glossary for the PreTerminalGuesser
PreTerminalGuesser.load_glossary("glossary.txt")

# Register some 1337-speak mangling rules
ManglingGuesser.add_rule(lambda s: s.replace("a", "4"))  
ManglingGuesser.add_rule(lambda s: s.replace("e", "3"))  
ManglingGuesser.add_rule(lambda s: s.replace("i", "1"))  
ManglingGuesser.add_rule(lambda s: s.replace("o", "0"))
ManglingGuesser.add_rule(lambda s: s + "!")  
ManglingGuesser.add_rule(lambda s: s + "?")  


def cracker(preterminal):
    """Given a preterminal, iterate filling it, and then apply mangling rules
    to generate a set of password guesses.
    """
    rval = {"attempts": 0}
    for terminal in PreTerminalGuesser(preterminal):
        for permutation in ManglingGuesser(terminal):
            test = hashlib.sha256(guessfmtstr.format(permutation)).hexdigest()
            rval["attempts"] += 1
            
            if hash1 == test:
                rval["solution"] = permutation
                return rval
    return rval
