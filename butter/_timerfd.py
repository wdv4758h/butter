#!/usr/bin/env python
"""timerfd: recive timing events on a file descriptor

For new code use TimerVal instead of TimerSpec as TimerSpec is slated to be removed 
after the 1.0 release and provides a simplier and faster interface that is easier
to interpret
"""

from .utils import UnknownError, InternalError, CLOEXEC_DEFAULT
from collections import namedtuple
from cffi import FFI
import errno
import math

TimePair = namedtuple('TimePair', 'seconds nano_seconds')

ffi = FFI()
ffi.cdef("""
#define TFD_CLOEXEC ...
#define TFD_NONBLOCK ...

#define TFD_TIMER_ABSTIME ...

#define CLOCK_REALTIME ...
#define CLOCK_MONOTONIC ...

typedef long int time_t;

struct timespec {
    time_t tv_sec; /* Seconds */
    long tv_nsec; /* Nanoseconds */
};

struct itimerspec {
    struct timespec it_interval; /* Interval for periodic timer */
    struct timespec it_value; /* Initial expiration */
};

int timerfd_create(int clockid, int flags);

int timerfd_settime(int fd, int flags,
                    const struct itimerspec *new_value,
                    struct itimerspec *old_value);

int timerfd_gettime(int fd, struct itimerspec *curr_value);
""")

C = ffi.verify("""
#include <sys/timerfd.h>
#include <stdint.h> /* Definition of uint64_t */
#include <time.h>
""", libraries=[], ext_package="butter")


TFD_CLOEXEC = C.TFD_CLOEXEC
TFD_NONBLOCK = C.TFD_NONBLOCK
TFD_TIMER_ABSTIME = C.TFD_TIMER_ABSTIME

CLOCK_REALTIME = C.CLOCK_REALTIME
CLOCK_MONOTONIC = C.CLOCK_MONOTONIC

class TimerVal(object): 
    """ timer = TimerVal()
    timer.occuring.every(mins=5, nano_seconds=3).after(seconds=5)
    timer.offset(seconds=3).and_repeats.every(seconds=5)
    """
    __slots__ = ['_timerspec']
    def __init__(self, timerspec=None):
        if timerspec:
            self._timerspec = timerspec
        else:
            self._timerspec = ffi.new('struct itimerspec *')
        
        super(TimerVal, self).__init__()

    @property
    def occuring(self):
        return self
    @property
    def and_repeats(self):
        return self
    
    def every(self, seconds=None, nano_seconds=None):
        if seconds is not None:
            self._timerspec.it_interval.tv_sec = seconds
            # arm the timer
            if not self._timerspec.it_value.tv_sec:
                self._timerspec.it_value.tv_sec = seconds
        if nano_seconds is not None:
            self._timerspec.it_interval.tv_nsec = nano_seconds
            # arm the timer
            if not self._timerspec.it_value.tv_nsec:
                self._timerspec.it_value.tv_nsec = nano_seconds
        return self
        
    def repeat(self, seconds=None, nano_seconds=None):
        return self.every(seconds, nano_seconds)
        
    def repeats(self, seconds=None, nano_seconds=None):
        return self.every(seconds, nano_seconds)
    
    def after(self, seconds=None, nano_seconds=None):
        if seconds is not None:
            self._timerspec.it_value.tv_sec = seconds
        if nano_seconds is not None:
            self._timerspec.it_value.tv_nsec = nano_seconds
        return self
        
    def offset(self, seconds=None, nano_seconds=None):
        return self.after(seconds, nano_seconds)

    def __timerspec__(self):
        return self._timerspec

    def __bool__(self):
        return bool(self.it_value.tv_sec or self.it_value.tv_nsec)
    
    @property
    def enabled(self):
        """Will this timer fire if used?, returns a bool"""
        return bool(self)
    
    def disable(self):
        """Disable the timer from firing"""
        return self.offset(0, 0)

    @property
    def next_event(self):
        """returns a tuple containg (seconds, nanoseconds) representing when the timer next expires"""
        return TimePair(self._timerspec.it_value.tv_sec, self._timerspec.it_value.tv_nsec)

    @property
    def period(self):
        """returns a tuple containg (seconds, nanoseconds) representing how freqently the timer expires"""
        return TimePair(self._timerspec.it_interval.tv_sec, self._timerspec.it_interval.tv_nsec)
    
    def __repr__(self):
        return "<{} offset=({}s, {}ns) reoccuring=({}s, {}ns)>".format(self.__class__.__name__,
                                                                       self._timerspec.it_value.tv_sec, 
                                                                       self._timerspec.it_value.tv_nsec,
                                                                       self._timerspec.it_interval.tv_sec, 
                                                                       self._timerspec.it_interval.tv_nsec)


def timerfd(clock_type=CLOCK_MONOTONIC, flags=0, closefd=CLOEXEC_DEFAULT):
    """Create a new timerfd
    
    Arguments
    ----------
    :param int clock_type: The type of clock to use internally
                           DEFAULT: CLOCK_MONOTONIC
    :param int flags: Flags to specify extra options
    
    Flags
    ------
    CLOCK_REALTIME: Use a clock that mirrors the system time
                    (will be affected by settime)
    CLOCK_MONOTONIC: Use a Monotonically increasing clock value
    TFD_CLOEXEC: Close the timerfd when executing a new program
    TFD_NONBLOCK: Open the socket in non-blocking mode

    in nearly all simple cases you will want CLOCK_MONOTONIC. When
    using CLOCK_REALTIME you will need to be aware of and adjust for
    the clock moving back and forwards (eg ntp, admins, daylight savings,
    leap seconds, clock drift, time dilation as you approach the speed
    of light)
    
    Returns
    --------
    :return: The file descriptor representing the timerfd
    :rtype: int
    
    Exceptions
    -----------
    :raises ValueError: Invalid value in flags
    :raises OSError: Max per process FD limit reached
    :raises OSError: Max system FD limit reached
    :raises OSError: Could not mount (internal) anonymous inode device
    :raises MemoryError: Insufficient kernel memory
    """
    assert isinstance(clock_type, int), 'Clock Type must be an integer'
    assert isinstance(flags, int), 'Flags must be an integer'

    if closefd:
        flags |= TFD_CLOEXEC
        
    fd = C.timerfd_create(clock_type, flags)
    
    if fd < 0:
        err = ffi.errno
        if err == errno.EINVAL:
            if not (clock_type & CLOCK_MONOTONIC) and not (clock_type & CLOCK_REALTIME):
                raise ValueError("clock_type is not one of CLOCK_MONOTONIC or CLOCK_REALTIME")
            raise ValueError("Invalid value in flags")
        elif err == errno.EMFILE:
            raise OSError("Max per process FD limit reached")
        elif err == errno.ENFILE:
            raise OSError("Max system FD limit reached")
        elif err == errno.ENODEV:
            raise OSError("Could not mount (internal) anonymous inode device")
        elif err == errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory available")
        else:
            # If you are here, its a bug. send us the traceback
            raise UnknownError(err)

    return fd


def timerfd_gettime(fd):
    """Get the current expiry time of a timerfd
    
    Arguments
    ----------
    :param int fd: File descriptor representing the timerfd

    Returns
    --------
    :return: The file descriptor representing the timerfd
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
    
    curr_val = ffi.new('struct itimerspec *')
    ret = C.timerfd_gettime(fd, curr_val)
    
    if ret < 0:
        err = ffi.errno
        if err == errno.EBADF:
            raise ValueError("fd is not a valid file descriptor")
        elif err == errno.EFAULT:
            raise InternalError("curr_val is not a valid pointer (internal/bug, let us know)")
        elif err == errno.EINVAL:
            raise ValueError("fd is not a valid timerfd")
        else:
            # If you are here, its a bug. send us the traceback
            raise UnknownError(err)

    curr_val = TimerVal(timerspec=curr_val)
    return curr_val


def timerfd_settime(fd, timer_spec, flags=0):
    """Set the expiry time of a timerfd
    
    Arguments
    ----------
    :param int fd: File descriptor representing the timerfd
    :param int inital_value: The inital value to set the timerfd to
    :param int flags: Flags to specify extra options
    
    Flags
    ------
    TFD_TIMER_ABSTIMER: The specified time is an absolute value rather than relative to now
        
    Returns
    --------
    :return: The file descriptor representing the timerfd
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
    assert isinstance(flags, int), 'flags must be an integer'
    
    if hasattr(timer_spec, '__timerspec__'):
        timer_spec = timer_spec.__timerspec__()

    assert isinstance(timer_spec, FFI.CData) # ensure passed in value is what we want
    
    old_timer_spec = ffi.new('struct itimerspec *')

    ret = C.timerfd_settime(fd, flags, timer_spec, old_timer_spec)
    
    if ret < 0:
        err = ffi.errno
        if err == errno.EINVAL:
            if timer_spec.it_interval.tv_sec > 999999999:
                raise ValueError("Repeat Seconds > 999,999,999")
            elif timer_spec.it_interval.tv_nsec > 999999999:
                raise ValueError("Repeat Nano seconds > 999,999,999")
            elif timer_spec.it_value.tv_sec > 999999999:
                raise ValueError("Offset Seconds > 999,999,999")
            elif timer_spec.it_value.tv_nsec > 999999999:
                raise ValueError("Offset Nano seconds > 999,999,999")
            else:
                raise ValueError('flags is invalid or fd not a timerfd')
        elif err == errno.EFAULT:
            raise InternalError("timer_spec does not point to a valid timer specfication")
        elif err == errno.EMFILE:
            raise OSError("Max per process FD limit reached")
        elif err == errno.ENFILE:
            raise OSError("Max system FD limit reached")
        elif err == errno.ENODEV:
            raise OSError("Could not mount (internal) anonymous inode device")
        elif err == errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory available")
        else:
            # If you are here, its a bug. send us the traceback
            raise UnknownError(err)
            
    old_timer_spec = TimerVal(timerspec=old_timer_spec)
    return old_timer_spec
