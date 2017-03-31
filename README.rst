=========
 Cracken
=========

A framework for generating password guesses based on profiling.

``cracken`` provides a classifier for profiling collections of plaintext passwords, and several tools which use that profiling to generate password guesses. Also included is a tool for parallelizing tasks across multiple hosts.

------------
 Components
------------
    
    cracken.classifier
        Given a file of plaintext passwords, the ``classify()`` method generates a glossary, set of base structures, and a probablistic grammar. This profiling information is used by the guessers.

    cracken.generator
        Contains the PreTerminalHeap, a generator which takes the base structures and probabilistic grammar, and generates preterminals which can be filled with glossary terms to generate password guesses.

    cracken.guessers
        Contains the PreTerminalGuesser, which generates password guesses with the output of the PreTerminalHeap. Also contains the ManglingGuesser, which applies mangling rules to the given string to generate password guesses.

    cracken.bullpen
        Contains the Bullpen utility for distributing tasks across multiple hosts. The Bullpen implements a distributed task queue the likes of Celery, but which automatically launches its workers and uses the Python `multiprocessing` library's Manager server as the transport layer.

    head.py
        A working example utilizing all components of the framework to implement a password cracker.

    worker.py
        The worker task loaded by the Bullpen in ``head.py``.
