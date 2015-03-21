#!/usr/bin/env python
"""signalfd: Recive signals over a file descriptor"""

from .utils import UnknownError, CLOEXEC_DEFAULT
from cffi import FFI
import signal
import errno

ffi = FFI()
ffi.cdef("""
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

#define SIG_BLOCK ...
#define SIG_UNBLOCK ...
#define SIG_SETMASK ...

int pthread_sigmask(int how, const sigset_t *set, sigset_t *oldset);
""")

C = ffi.verify("""
#include <sys/signalfd.h>
#include <stdint.h> /* Definition of uint64_t */
#include <signal.h>
""", libraries=[], ext_package="butter")

SFD_CLOEXEC = C.SFD_CLOEXEC
SFD_NONBLOCK = C.SFD_NONBLOCK

SIG_BLOCK = C.SIG_BLOCK
SIG_UNBLOCK = C.SIG_UNBLOCK
SIG_SETMASK = C.SIG_SETMASK

NEW_SIGNALFD = -1 # Create a new signal rather than modify an exsisting one


def signalfd(signals, fd=NEW_SIGNALFD, flags=0, closefd=CLOEXEC_DEFAULT):
    """Create a new signalfd
    
    Arguments
    ----------
    :param sigset_t signals: raw cdata to pass to the syscall
    :param int signals: A single int representing the signal to listen for
    :param list signals: A list of signals to listen for
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
    if hasattr(fd, 'fileno'):
        fd = fd.fileno()

    assert isinstance(fd, int), 'fd must be an integer'
    assert isinstance(flags, int), 'Flags must be an integer'

    if closefd:
        flags |= SFD_CLOEXEC

    if isinstance(signals, ffi.CData):
        mask = signals
    else:
        mask = ffi.new('sigset_t[1]')
        # if we have multiple signals then all is good
        try:
            signals = iter(signals)
        except TypeError:
        # if not make the value iterable
            signals = [signals]

        for signal in signals:
            C.sigaddset(mask, signal)

    ret_fd = C.signalfd(fd, mask, flags)
    
    if ret_fd < 0:
        err = ffi.errno
        if err == errno.EBADF:
            raise ValueError("FD is not a valid file descriptor")
        elif err == errno.EINVAL:
            if (flags & (0xffffffff ^ (SFD_CLOEXEC|SFD_NONBLOCK))):
                raise ValueError("Mask contains invalid values")
            else:
                raise ValueError("FD is not a signalfd")
        elif err == errno.EMFILE:
            raise OSError("Max system FD limit reached")
        elif err == errno.ENFILE:
            raise OSError("Max system FD limit reached")
        elif err == errno.ENODEV:
            raise OSError("Could not mount (internal) anonymous inode device")
        elif err == errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory available")
        else:
            # If you are here, its a bug. send us the traceback
            raise UnknownError(err)

    return ret_fd


def pthread_sigmask(action, signals):
    """Create a new signalfd
    
    Arguments
    ----------
    :param int action: The action to take on the supplied signals (bitmask)
    :param list signals: An iterable of signals
    :param int signals: A single signal
    
    Flags: action
    -----------
    SIG_BLOCK: Block the signals in sigmask from being delivered
    SIG_UNBLOCK: Unblock the signals in the supplied sigmask
    SIG_SETMASK: Set the active signals to match the supplied sigmask
    
    Returns
    --------
    :return: The old set of active signals
    :rtype: sigset
    
    Exceptions
    -----------
    :raises ValueError: Invalid value in 'how'
    :raises ValueError: sigmask is not a valid sigmask_t
    """
    assert isinstance(action, int), '"How" must be an integer'

    new_sigmask = ffi.new('sigset_t[1]')
    old_sigmask = ffi.new('sigset_t[1]')

    # if we have multiple signals then all is good
    try:
        signals = iter(signals)
    except TypeError:
    # if not make the value iterable
        signals = [signals]

    for signal in signals:
        C.sigaddset(new_sigmask, signal)
    
    ret = C.pthread_sigmask(action, new_sigmask, ffi.NULL)
    
    if ret < 0:
        err = ffi.errno
        if err == errno.EINVAL:
            raise ValueError("Action is an invalid value (not one of SIG_BLOCK, SIG_UNBLOCK or SIG_SETMASK)")
        elif err == errno.EFAULT:
            raise ValueError("sigmask is not a valid sigset_t")
        else:
            # If you are here, its a bug. send us the traceback
            raise UnknownError(err)


signum_to_signame = {val:key for key, val in signal.__dict__.items()
                     if isinstance(val, int) and "_" not in key}
