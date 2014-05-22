#!/usr/bin/env python
"""signalfd: Recive signals over a file descriptor"""

from __future__ import print_function

from .utils import get_buffered_length as _get_buffered_length

from os import write as _write, read as _read, close as _close
from cffi import FFI as _FFI
import errno as _errno

_ffi = _FFI()
_ffi.cdef("""
#define SFD_CLOEXEC ...
#define SFD_NONBLOCK ...

struct signalfd_siginfo {
    uint32_t ssi_signo; /* Signal number */
    int32_t ssi_errno; /* Error number (unused) */
    int32_t ssi_code; /* Signal code */
    uint32_t ssi_pid; /* PID of sender */
    uint32_t ssi_uid; /* Real UID of sender */
    int32_t ssi_fd; /* File descriptor (SIGIO) */
    uint32_t ssi_tid; /* Kernel timer ID (POSIX timers)
    uint32_t ssi_band; /* Band event (SIGIO) */
    uint32_t ssi_overrun; /* POSIX timer overrun count */
    uint32_t ssi_trapno; /* Trap number that caused signal */
    int32_t ssi_status; /* Exit status or signal (SIGCHLD) */
    int32_t ssi_int; /* Integer sent by sigqueue(3) */
    uint64_t ssi_ptr; /* Pointer sent by sigqueue(3) */
    uint64_t ssi_utime; /* User CPU time consumed (SIGCHLD) */
    uint64_t ssi_stime; /* System CPU time consumed (SIGCHLD) */
    uint64_t ssi_addr; /* Address that generated signal
                        (for hardware-generated signals) */
//    uint8_t pad[X]; /* Pad size to 128 bytes (allow for
//                        additional fields in the future) */
    ...;
};
/*
# define _SIGSET_NWORDS ...
typedef struct
{
    unsigned long int __val[_SIGSET_NWORDS];
} __sigset_t;

typedef __sigset_t sigset_t;

int signalfd(int fd, const sigset_t *mask, int flags);

int sigemptyset(sigset_t *set);
int sigfillset(sigset_t *set);
int sigaddset(sigset_t *set, int signum);
int sigdelset(sigset_t *set, int signum);
int sigismember(const sigset_t *set, int signum);
*/
""")

_C = _ffi.verify("""
#include <linux/signalfd.h>
#include <stdint.h> /* Definition of uint64_t */
#include <signal.h>
""", libraries=[])

NEW_SIGNALFD = -1 # Create a new signal rather than modify an exsisting one

def signalfd(mask, fd=NEW_SIGNALFD, flags=0):
    """Create a new signalfd
    
    Arguments
    ----------
    :param int mask: The mask of signals to listen for
    :param int fd: The file descriptor to modify, if set to NEW_SIGNALFD then a new FD is returned
    :param int flags: 
    
    Flags
    ------
    SFD_CLOEXEC: Close the eventfd when executing a new program
    SFD_NONBLOCK: Open the socket in non-blocking mode
    
    Returns
    --------
    :return: The file descriptor representing the signalfd
    :rtype: int
    
    Exceptions
    -----------
    :raises ValueError: Invalid value in flags
    :raises OSError: Max per process FD limit reached
    :raises OSError: Max system FD limit reached
    :raises OSError: Could not mount (internal) anonymous inode device
    :raises MemoryError: Insufficient kernel memory
    """
    ret_fd = _C.eventfd(inital_value, flags)
    
    if ret_fd < 0:
        err = _ffi.errno
        if err == _errno.EBADF:
            raise ValueError("FD is not a valid file descriptor")
        elif err == _errno.EINVAL:
            if not (flags & (SFD_CLOEXEC|SFD_NONBLOCK)):
                raise ValueError("Mask contains invalid values")
            else:
                raise OSError("FD is not a signalfd")
        elif err == _errno.EMFILE:
            raise OSError("Max system FD limit reached")
        elif err == _errno.ENFILE:
            raise OSError("Max system FD limit reached")
        elif err == _errno.ENODEV:
            raise OsError("Could not mount (internal) anonymous inode device")
        elif err == _errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory available")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))

    return ret_fd

SFD_CLOEXEC = _C.SFD_CLOEXEC
SFD_NONBLOCK = _C.SFD_NONBLOCK

class Signalfd(object):
    def __init__(self, sigmask=set(), flags=0, fd=NEW_SIGNALFD):
        """Create a new Signalfd object

        Arguments
        ----------
        :param int sigmask: Set of signals to respond on
        :param int flags: Flags to open the signalfd with
        
        Flags
        ------
        SFD_CLOEXEC: Close the signalfd when executing a new program
        SFD_NONBLOCK: Open the socket in non-blocking mode
        """
        self._fd = fd
        
        self._sigmask = _ffi.new('sigset_t[1]')
        self.disable_all()
        
        self._flags = flags
        
        self._update()
        
    def __contains__(self, signal):
        val = _C.sigismember(self._sigmask, signal)
        
        if val < 0:
            raise ValueError('Signal is not a valid signal number')
        
        return bool(val)
    
    def _update(self):
        return signalfd(self._sigmask, self.fileno(), self._flags)

    def enable(self, signal):
        _C.sigaddset(self._sigmask, signal)
        self._update()

    def enable_all(self):
        _C.sigfillset(self._sigmask)
        self._update()
        
    def disable(self, signal):
        _C.sigdelset(self._sigmask, signal)
        self._update()
        
    def disable_all(self):
        _C.sigemptyset(self._sigmask)
        self._update()
        
    def wait(self):
        from select import select
        
        select([self.fileno()], [], [])
        event = self._read_event()
        
        return event
    
    def close(self):
        _close(self.fileno())
        self._fd = None
    
    def fileno(self):
        if self._fd:
            return self._fd
        else:
            raise ValueError("I/O operation on closed file")
        
    def _read_event(self):
        fd = self.fileno()
        l = _get_buffered_length(fd)
        buf = _read(fd, l)
        siginfo = _ffi.new('signalfd_siginfo[1]')
        
        siginfo[:l] = buf
        
        return siginfo

def _main():
    import signal
    import os
    
    sigmask = SignalMask()
    sigmask.enable(signal.SIGINT)
    
    sfd = Signalfd(sigmask)
    
    signal.signal(signal.SIGINT, os.getpid())
    
    s = sfd.wait()
    if s.signal == signal.SIGINT:
        print("We get signal")
    else:
        print("Bomb not set up")
    
    
if __name__ == "__main__":
    _main()
