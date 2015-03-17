#!/usr/bin/env python

EXIT = 1
EXIT_GROUP = 248
READ = 3
WRITE = 4
SIGRETURN = 119
RT_SIGACTION = 174

print('a')

filter = _C.seccomp_init(_C.SCMP_ACT_KILL)
filter = _C.seccomp_init(_C.SCMP_ACT_KILL)
_C.seccomp_rule_add(filter, _C.SCMP_ACT_ALLOW, EXIT, 0)
_C.seccomp_rule_add(filter, _C.SCMP_ACT_ALLOW, EXIT_GROUP, 0)
_C.seccomp_rule_add(filter, _C.SCMP_ACT_ALLOW, READ, 0)
import sys
from collections import namedtuple
Comparison = namedtuple('Comparison', 'arg op arg1 arg2')
only_stderr =_ffi.new('struct scmp_arg_cmp[1]')
only_stderr[0] = {'arg':0, 'op':_C.SCMP_CMP_EQ, 'datum_a':sys.stderr.fileno()}
only_stderr[0] = Comparison(0,_C.SCMP_CMP_EQ, sys.stderr.fileno(), 0)
_C.seccomp_rule_add(filter, _C.SCMP_ACT_ALLOW, WRITE, 1, only_stderr)
_C.seccomp_rule_add(filter, _C.SCMP_ACT_ALLOW, SIGRETURN, 0)
_C.seccomp_rule_add(filter, _C.SCMP_ACT_ALLOW, RT_SIGACTION, 0)
sys.stderr.write('1\n')
ret = _C.seccomp_load(filter)
sys.stderr.write(str(ret))

