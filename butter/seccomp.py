#!/usr/bin/env python
"""fanotify: wrapper aroudn the fanotify family of syscalls for watching for file modifcation"""

from cffi import FFI as _FFI
from os import O_RDONLY, O_WRONLY, O_RDWR
from os import fdopen
import errno as _errno

READ_EVENTS_MAX = 10

_ffi = _FFI()
_ffi.cdef("""

typedef void * scmp_filter_ctx;

scmp_filter_ctx seccomp_init(uint32_t def_action);
int seccomp_reset(scmp_filter_ctx ctx, uint32_t def_action);
void seccomp_release(scmp_filter_ctx ctx);
int seccomp_merge(scmp_filter_ctx dst, scmp_filter_ctx src);
int seccomp_load(scmp_filter_ctx ctx);

/*
int SCMP_SYS(syscall_name);

struct scmp_arg_cmp SCMP_CMP(unsigned int arg,
                             enum scmp_compare op, ...);
struct scmp_arg_cmp SCMP_A0(enum scmp_compare op, ...);
struct scmp_arg_cmp SCMP_A1(enum scmp_compare op, ...);
struct scmp_arg_cmp SCMP_A2(enum scmp_compare op, ...);
struct scmp_arg_cmp SCMP_A3(enum scmp_compare op, ...);
struct scmp_arg_cmp SCMP_A4(enum scmp_compare op, ...);
struct scmp_arg_cmp SCMP_A5(enum scmp_compare op, ...);
*/

int seccomp_rule_add(scmp_filter_ctx ctx, uint32_t action,
                     int syscall, unsigned int arg_cnt, ...);
int seccomp_rule_add_exact(scmp_filter_ctx ctx, uint32_t action,
                           int syscall, unsigned int arg_cnt, ...);

int seccomp_rule_add_array(scmp_filter_ctx ctx,
                           uint32_t action, int syscall,
                           unsigned int arg_cnt,
                           const struct scmp_arg_cmp *arg_array);
int seccomp_rule_add_exact_array(scmp_filter_ctx ctx,
                                 uint32_t action, int syscall,
                                 unsigned int arg_cnt,
                                 const struct scmp_arg_cmp *arg_array);

//# Default actions
#define SCMP_ACT_KILL ...
#define SCMP_ACT_TRAP ...
// macros that take args, needs fixing
//#define SCMP_ACT_ERRNO ...
//#define SCMP_ACT_TRACE ...
#define SCMP_ACT_ALLOW ...

//#Valid comparison op values are as follows:
#define SCMP_CMP_NE ...
#define SCMP_CMP_LT ...
#define SCMP_CMP_LE ...
#define SCMP_CMP_EQ ...
#define SCMP_CMP_GE ...
#define SCMP_CMP_GT ...
#define SCMP_CMP_MASKED_EQ ...
""")

_C = _ffi.verify("""
#include <seccomp.h>
""", libraries=['seccomp'])

def main():
    EXIT = 1
    EXIT_GROUP = 248
    READ = 3
    WRITE = 4
    SIGRETURN = 119
    RT_SIGACTION = 174
    
    print 'a'
#    filter = _C.seccomp_init(_C.SCMP_ACT_KILL)
    filter = _C.seccomp_init(_C.SCMP_ACT_KILL)
    _C.seccomp_rule_add(filter, _C.SCMP_ACT_ALLOW, EXIT, 0)
    _C.seccomp_rule_add(filter, _C.SCMP_ACT_ALLOW, EXIT_GROUP, 0)
    _C.seccomp_rule_add(filter, _C.SCMP_ACT_ALLOW, READ, 0)
    _C.seccomp_rule_add(filter, _C.SCMP_ACT_ALLOW, WRITE, 0)
    _C.seccomp_rule_add(filter, _C.SCMP_ACT_ALLOW, SIGRETURN, 0)
    _C.seccomp_rule_add(filter, _C.SCMP_ACT_ALLOW, RT_SIGACTION, 0)
    ret = _C.seccomp_load(filter)
    print ret
    
if __name__ == "__main__":
    main()
