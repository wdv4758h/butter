#!/usr/bin/env python
"""signalfd: Recive signals over a file descriptor"""

from __future__ import print_function

from .utils import get_buffered_length as _get_buffered_length

from os import write as _write, read as _read, close as _close
from select import select as _select
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

//# define _SIGSET_NWORDS     (1024 / (8 * sizeof (unsigned long int)))
// 32bits: 1024 / 8 / 4  = 32
// 64bits: 1024 / 8 / 4  = 16
// however we can just cheat and define it as 32 as 16 fits in 32 and there
// is no length arg for the functions
//#define _SIGSET_NWORDS 32
typedef struct
{
//    unsigned long int __val[_SIGSET_NWORDS];
    unsigned long int __val[32];
} __sigset_t;

typedef __sigset_t sigset_t;

int signalfd(int fd, const sigset_t *mask, int flags);

int sigemptyset(sigset_t *set);
int sigfillset(sigset_t *set);
int sigaddset(sigset_t *set, int signum);
int sigdelset(sigset_t *set, int signum);
int sigismember(const sigset_t *set, int signum);
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
    SFD_CLOEXEC: Close the signalfd when executing a new program
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
    ret_fd = _C.signalfd(fd, mask, flags)
    
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
    def __init__(self, sigmask=set(), flags=0):
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
        self._flags = flags

        self._sigmask = sigmask = _ffi.new('sigset_t[1]')

        self._fd = signalfd(sigmask, NEW_SIGNALFD, flags)
        
    def __contains__(self, signal):
        val = _C.sigismember(self._sigmask, signal)
        
        if val < 0:
            raise ValueError('Signal is not a valid signal number')
        
        return bool(val)
    
    def _update(self):
        return signalfd(self._sigmask, self.fileno(), self._flags)

    def enable(self, signals):
        """Mark signals as active on signalfd
        
        :param int signals: A single signal to listen for
        :param list signals: A list of signals to listen for
        
        enable will mark all signals passed in on signalfd and takes
        ethier a signal integer representing the signal to add or an
        iterable if signals to (bulk) add
        
        The latter for is used for more efficent updates of signal masks
        """
        # if we have multipel signals then all is good
        try:
            signals = iter(signals)
        except TypeError:
        # if not make the value iterable
            signals = [signals]

        for signal in signals:
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
        _select([self.fileno()], [], [])
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
        SIGNALFD_SIGINFO_LENGTH = 128 # Bytes
        buf = _read(self.fileno(), SIGNALFD_SIGINFO_LENGTH)
        siginfo = _ffi.new('struct signalfd_siginfo *')

        _ffi.buffer(siginfo, SIGNALFD_SIGINFO_LENGTH)[0:SIGNALFD_SIGINFO_LENGTH] = buf
        
        return siginfo


def _main():
    import signal
    import os
    
    print("creating signalfd")
    sfd = Signalfd()
    print("Enabling keyboard interrupt via signalfd")
    sfd.enable(signal.SIGINT)

    print("Ignoring SIGINT via normal channels")
    signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGINT])
    print("Sending self SIGINT")
    os.kill(os.getpid(), signal.SIGINT)

    print("Waiting for SIGINT")
    s = sfd.wait()
    if s.ssi_signo == signal.SIGINT:
        print("We get signal")
    else:
        print("Bomb not set up")
    
    sfd.close()
    try:
        sfd.close()
    except ValueError:
        print("Attempted to close closed signalfd and failed, OK")
    else:
        print("Attempted to close closed signalfd and succseeded, ERROR")
    
    
if __name__ == "__main__":
    _main()
