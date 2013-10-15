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

typedef uint64_t scmp_datum_t;

struct scmp_arg_cmp {
    unsigned int arg;
    enum scmp_compare op;
    scmp_datum_t datum_a;
    scmp_datum_t datum_b;
};


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
#define SCMP_ACT_ALLOW ...
uint64_t _SCMP_ACT_ERRNO(uint64_t code);
uint64_t _SCMP_ACT_TRACE(uint64_t code);

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

uint64_t _SCMP_ACT_ERRNO(uint64_t code) {
    return 0x7ff00000U | (code & 0x0000ffffU);
}
uint64_t _SCMP_ACT_TRACE(uint64_t code) {
    return 0x00050000U | (code & 0x0000ffffU);
}

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
