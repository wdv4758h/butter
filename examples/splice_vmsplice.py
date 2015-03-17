#!/usr/bin/env python

import sys
import os

r_fd, w_fd = os.pipe()

buf = ["this is a test",
       " and this should be on the same line",
       "\nsupprise, newline this time\n"
      ]
bytes = vmsplice(w_fd, buf)
print('vmspliced {} bytes'.format(bytes))
splice(r_fd, sys.stdout, len=bytes)
print('spliced {} bytes'.format(bytes))

