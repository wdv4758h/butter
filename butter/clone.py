#!/usr/bin/env python

from .utils import PermissionError
from cffi import FFI
import errno

ffi = FFI()
ffi.cdef("""

#define CLONE_FS      ...
#define CLONE_NEWNS   ...
#define CLONE_NEWUTS  ...
#define CLONE_NEWIPC  ...
#define CLONE_NEWUSER ...
#define CLONE_NEWPID  ...
#define CLONE_NEWNET  ...

//#long __clone(unsigned long flags, void *child_stack, ...);
long __clone(unsigned long flags, void *child_stack,
             void *ptid, void *ctid, void *regs);

int unshare(int flags);
int setns(int fd, int nstype);
""")
  

C = ffi.verify("""  
#include <sched.h>
#include <unistd.h>
#include <sys/types.h>
#include <unistd.h>

// man page
//long __clone(unsigned long flags, void *child_stack, ...);
long __clone(unsigned long flags, void *child_stack,
             void *ptid, void *ctid,
             void *regs);
""", libraries=[], ext_package="butter")

CLONE_ALL = C.CLONE_NEWIPC  | \
            C.CLONE_NEWNET  | \
            C.CLONE_NEWNS   | \
            C.CLONE_NEWUTS  | \
            C.CLONE_NEWPID  | \
            C.CLONE_NEWUSER

CLONE_NEWNS = C.CLONE_NEWNS
CLONE_NEWUTS = C.CLONE_NEWUTS
CLONE_NEWIPC = C.CLONE_NEWIPC
CLONE_NEWUSER = C.CLONE_NEWUSER
CLONE_NEWPID = C.CLONE_NEWPID
CLONE_NEWNET = C.CLONE_NEWNET


def unshare(flags):
    """Unshare the current namespace and create a new one

    Arguments
    ----------
    :param int flags: The flags controlling which namespaces to unshare

    Flags
    ------
    CLONE_NEWNS: Unshare the mount namespace causing mounts in this namespace
                 to not be visible to the parent namespace
    CLONE_NEWUTS: Unshare the system hostname allowing it to be changed independently
                  to the rest of the system
    CLONE_NEWIPC: Unshare the IPC namespace 
    CLONE_NEWUSER: Unshare the UID space allowing UIDs to be remapped to the parent
    CLONE_NEWPID: Unshare the PID space allowing remapping of PIDs relative to the parent
    CLONE_NEWNET: Unshare the network namespace, creating a separate set of network
                  interfaces/firewall rules

    Exceptions
    -----------
    :raises ValueError: Invalid value in flags
    """
    fd = C.unshare(flags)

    if fd < 0:
        err = ffi.errno
        if err == errno.EINVAL:
            raise ValueError("Invalid value in flags")
        elif err == errno.EPERM:
            raise PermissionError("Process in chroot or has incorrect permissions")
        elif err == errno.EUSERS:
            raise PermissionError("CLONE_NEWUSER specified but max user namespace nesting has been reached")
        elif err == errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory available")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))

    return fd


### prctl

def main():
    import os, errno, sys
    
#    ret = C.__clone(CLONE_NEWNET|CLONE_NEWUTS|CLONE_NEWIPC|CLONE_NEWNS, ffi.NULL)
#    ret = C.__clone(CLONE_NEWNET|CLONE_NEWUTS|CLONE_NEWIPC|CLONE_NEWNS, ffi.NULL, ffi.NULL, ffi.NULL, ffi.NULL)

    ret = C.unshare(CLONE_NEWNET|CLONE_NEWUTS|CLONE_NEWIPC|CLONE_NEWNS)
#    ret = C.unshare(CLONE_ALL)
    if ret >= 0:
#        with open("/proc/self/uid_map", "w") as f:
#            f.write("0 0 1\n")
        os.execl('/bin/bash', 'bash')
    else:
        print(ret, ffi.errno, errno.errorcode[ffi.errno])
        print("failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
