#!/usr/bin/env python
"""An example showing off using tee in production use
pipes data from stdin to stdout but looks for the magic 'exit' command
in the stream and exit when it sees it

Known Bugs:
* Partial reads of 'exit' command where a command may be read partially over
  multiple reads() will not exit correctly

to run:
$ alias dog=cat
$ cat | python splice.py | dog

type 'exit' to cause the pipeline to exit, any other typed data will pass through the
pipeline uneditied
"""
import sys
import os

# gets arg 1 of sys.argv if set otherwise falls back to 'exit' as argv will be too
# short and 'exit' will be on the end (in pos 1)
command = (sys.argv + ['exit'])[1]

max_len = 2**24 # chosen arbitrarily

while True:
    bytes = tee(sys.stdin, sys.stdout, max_len)
    print("tee'd {} bytes".format(bytes))
    sys.stdout.flush()
    if command in sys.stdin.read(bytes):
        print("Exit command ({}) found, exiting".format(command))
        break

