#!/usr/bin/env python
"""timerfd: recive timing events on a file descriptor"""

from cffi import FFI
import errno
import math

class PointerError(Exception): pass

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
""", libraries=[])


TFD_CLOEXEC = C.TFD_CLOEXEC
TFD_NONBLOCK = C.TFD_NONBLOCK
TFD_TIMER_ABSTIME = C.TFD_TIMER_ABSTIME

CLOCK_REALTIME = C.CLOCK_REALTIME
CLOCK_MONOTONIC = C.CLOCK_MONOTONIC


class TimerSpec(object):
    """Thin wrapper around the itimerspec c struct providing convience methods"""
    def __init__(self, 
                 one_off=None, one_off_seconds=None, one_off_nano_seconds=None,
                 reoccuring=None, reoccuring_seconds=None, reoccuring_nano_seconds=None, 
                 timerspec=None):
        """Friendly wrapper around a c struct
        
        If setting a raw timerspec via the timerspec field then the reoccuring and one_off fields
        can still be used to customise the timerspec object in one go
        
        Arguments
        ----------
        :param int reoccuring: set the reoccuring interval
        :param int reoccuring_seconds: set the reoccuring intervals seconds field
        :param int reoccuring_nano_seconds: set the reoccuring intervals nano seconds field
        :param int one_off: set a one off interval
        :param int one_off_seconds: set a one off intervals seconds field
        :param int one_off_nanon_seconds: set a one off intervals nano seconds field
        :param int timerspec: set the timerspec to an exisiting timerspec
        """
        self._timerspec = ffi.new('struct itimerspec *')
        # cheap clone (this is harder than it appears at fist glance)
        if timerspec:
            self._timerspec.it_interval.tv_sec = timerspec.it_interval.tv_sec
            self._timerspec.it_interval.tv_nsec = timerspec.it_interval.tv_nsec
            self._timerspec.it_value.tv_sec = timerspec.it_value.tv_sec
            self._timerspec.it_value.tv_nsec = timerspec.it_value.tv_nsec
            
        if one_off:
            self.one_off = one_off
        if one_off_seconds:
            self.one_off_seconds = one_off_seconds
        if one_off_nano_seconds:
            self.one_off_nano_seconds = one_off_nano_seconds

        if reoccuring:
            self.reoccuring = reoccuring
        if reoccuring_seconds:
            self.reoccuring_seconds = reoccuring_seconds
        if reoccuring_nano_seconds:
            self.reoccuring_nano_seconds = reoccuring_nano_seconds
    
    @property
    def reoccuring(self):
        """The interval for reoccuring events in seconds as a float"""
        return self.reoccuring_seconds + (self.reoccuring_nano_seconds / 1000000000.0)
        
    @reoccuring.setter
    def reoccuring(self, val):
        """The interval for reoccuring events in seconds as a float"""
        if isinstance(val, float):
            x, y = math.modf(val)
            sec = int(y)
            nano = round(1000000000 * x)
            nano = int(nano) # python2.7 workaround (returns float there)
        else:
            sec = val
            nano = 0
        
        self.reoccuring_seconds = sec
        self.reoccuring_nano_seconds = nano
    
    @property
    def reoccuring_seconds(self):
        """Seconds part of a reoccuring event as an integer"""
        return self._timerspec.it_interval.tv_sec
        
    @reoccuring_seconds.setter
    def reoccuring_seconds(self, val):
        """Seconds part of a reoccuring event as an integer"""
        self._timerspec.it_interval.tv_sec = val

    @property
    def reoccuring_nano_seconds(self):
        """Nano seconds part of a reoccuring event as an integer"""
        return self._timerspec.it_interval.tv_nsec
    
    @reoccuring_nano_seconds.setter
    def reoccuring_nano_seconds(self, val):
        """Nano seconds part of a reoccuring event as an integer"""
        self._timerspec.it_interval.tv_nsec = val

    @property
    def one_off(self):
        """The interval for a one off event in seconds as a float"""
        return self.one_off_seconds + (self.one_off_nano_seconds / 1000000000.0)
        
    @one_off.setter
    def one_off(self, val):
        """The interval for a one off event in seconds as a float"""
        if isinstance(val, float):
            x, y = math.modf(val)
            sec = int(y)
            nano = round(1000000000 * x)
            nano = int(nano) # python2.7 workaround (returns float there)
        else:
            sec = val
            nano = 0
        
        self.one_off_seconds = sec
        self.one_off_nano_seconds = nano

    @property
    def one_off_seconds(self):
        """Seconds part of a one off event as an integer"""
        return self._timerspec.it_value.tv_sec
        
    @one_off_seconds.setter
    def one_off_seconds(self, val):
        """Seconds part of a one off event as an integer"""
        self._timerspec.it_value.tv_sec = val

    @property
    def one_off_nano_seconds(self):
        """Nano seconds part of a one off event as an integer"""
        return self._timerspec.it_value.tv_nsec
    
    @one_off_nano_seconds.setter
    def one_off_nano_seconds(self, val):
        """Nano seconds part of a one off event as an integer"""
        self._timerspec.it_value.tv_nsec = val
    
    def __timerspec__(self):
        return self._timerspec
    
    def __bool__(self):
        return False if self.one_off == 0.0 else True
    
    @property
    def enabled(self):
        """Will this timer fire if used?, returns a bool"""
        return bool(self)
    
    @property
    def disabled(self):
        """Will this timer not fire if used?, returns a bool"""
        return not self.enabled

    def disable(self):
        """Disable the timer in this timespec"""
        self.one_off = 0.0
    
    @property
    def next_event(self):
        """Convenience accessor for results returned by timerfd_gettime"""
        return self.one_off

    @property
    def next_event_seconds(self):
        """Convenience accessor for results returned by timerfd_gettime"""
        return self.one_off_seconds
        
    @property
    def next_event_nano_seconds(self):
        """Convenience accessor for results returned by timerfd_gettime"""
        return self.one_off_nano_seconds
    
    def __repr__(self):
        return "<{} next={:.3f}s reoccuring={:.3f}s>".format(self.__class__.__name__, self.next_event, self.reoccuring)


def timerfd(clock_type=CLOCK_MONOTONIC, flags=0):
    """Create a new timerfd
    
    Arguments
    ----------
    :param int clock_type: The type of clock to use internally
    :param int flags: Flags to specify extra options
    
    Flags
    ------
    CLOCK_REALTIME: Use a clock that mirrors the system time
                    (will be affected by settime)
    CLOCK_MONOTONIC: Use a Monotonically increasing clock value
    TFD_CLOEXEC: Close the timerfd when executing a new program
    TFD_NONBLOCK: Open the socket in non-blocking mode
    
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
            raise ValueError("Unknown Error: {}".format(err))

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
    curr_val = ffi.new('struct itimerspec *')
    ret = C.timerfd_gettime(fd, curr_val)
    
    if ret < 0:
        err = ffi.errno
        if err == errno.EBADF:
            raise ValueError("fd is not a valid file descriptor")
        elif err == errno.EFAULT:
            raise PointerError("curr_val is not a valid pointer (internal/bug, let us know)")
        elif err == errno.EINVAL:
            raise ValueError("fd is not a valid timerfd")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))

    curr_val = TimerSpec(timerspec=curr_val)
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
    if hasattr(timer_spec, '__timerspec__'):
        timer_spec = timer_spec.__timerspec__()
    
    if hasattr(fd, 'fileno'):
        fd = fd.fileno()
    
    old_timer_spec = ffi.new('struct itimerspec *')

    ret = C.timerfd_settime(fd, flags, timer_spec, old_timer_spec)
    
    if ret < 0:
        err = ffi.errno
        if err == errno.EINVAL:
            if timer_spec.it_interval.tv_sec > 999999999:
                raise ValueError("Nano seconds in it_interval is > 999,999,999")
            elif timer_spec.it_value.tv_nsec > 999999999:
                raise ValueError("Nano seconds in it_value is > 999,999,999")
            else:
                raise ValueError('flags is invalid or fd not a timerfd')
        elif err == errno.EFAULT:
            raise PointerError("timer_spec does not point to a valid timer specfication")
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
            raise ValueError("Unknown Error: {}".format(err))
            
    old_timer_spec = TimerSpec(timerspec=old_timer_spec)
    return old_timer_spec
