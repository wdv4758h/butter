#!/usr/bin/env python

from cffi import FFI
ffi = FFI()
ffi.cdef("""

#define CLONE_FS      ...
#define CLONE_NEWNS   ...
#define CLONE_NEWUTS  ...
#define CLONE_NEWIPC  ...
#define CLONE_NEWUSER ...
#define CLONE_NEWPID  ...
#define CLONE_NEWNET  ...

long __clone(unsigned long flags, void *child_stack, ...);
//           void *ptid, void *ctid, struct pt_regs *regs);

int unshare(int flags);
int setns(int fd, int nstype);
""")
  

C = ffi.verify("""  
#include <sched.h>
#include <unistd.h>
#include <sys/types.h>
#include <unistd.h>

// man page
long __clone(unsigned long flags, void *child_stack, ...);
//           void *ptid, void *ctid,
//           struct pt_regs *regs);
""", libraries=[])

CLONE_ALL = C.CLONE_NEWIPC  | \
            C.CLONE_NEWNET  | \
            C.CLONE_NEWNS   | \
            C.CLONE_NEWUTS  | \
            C.CLONE_NEWPID  | \
            C.CLONE_NEWUSER

CLONE_FS = C.CLONE_FS
CLONE_NEWNS = C.CLONE_NEWNS
CLONE_NEWUTS = C.CLONE_NEWUTS
CLONE_NEWIPC = C.CLONE_NEWIPC
CLONE_NEWUSER = C.CLONE_NEWUSER
CLONE_NEWPID = C.CLONE_NEWPID
CLONE_NEWNET = C.CLONE_NEWNET

### prctl

def main():
    tid = C.__clone(CLONE_NEWUTS|CLONE_NEWNET, 0,0,0,0)
    
    if tid == 0:
        # child
        os.execl('/bin/bash', ['bash'])
    else:
        # parent
        os.wait()
        print('child exited')

if __name__ == "__main__":
    main()
