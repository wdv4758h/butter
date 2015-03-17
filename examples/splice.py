#!/usr/bin/env python

"""Simple test to confirm that splice works and can handle short reads
where we write less than len that we dont block and wait but get the exact
same data out the other end
"""
import sys
import os

val = 'thisisatest'

fd1_ingress, fd1_egress = os.pipe()
fd2_ingress, fd2_egress = os.pipe()

print('writing')
os.write(fd1_egress, val)

print('splicing')
# Make sure we are splicing() more than the buffer of data we have chosen as a
# sentinal value to ensure that nothing blocks unexpectly (hard coded magic values
# lead to chaos)
splice(fd1_ingress, fd2_egress, flags=SPLICE_F_NONBLOCK, len=len(val)*2)

print('reading')
buf = os.read(fd2_ingress, len(val)+5) # this works as pipes can give a short read

print('verifing ("{}" == "{}")'.format(buf, val))
assert buf == val, 'value transformed through pipe transistion'

print('all ok')
