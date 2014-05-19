#!/usr/bin/env python
"""timerfd: recive timing events on a file descriptor"""

from __future__ import print_function

from os import write as _write, read as _read, close as _close
from select import select as _select
from cffi import FFI as _FFI
import errno as _errno
import math as _math

_ffi = _FFI()
_ffi.cdef("""
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

_C = _ffi.verify("""
#include <sys/timerfd.h>
#include <stdint.h> /* Definition of uint64_t */
#include <time.h>
""", libraries=[])

def timerfd(clock_type=0, flags=0):
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
    fd = _C.timerfd_create(clock_type, flags)
    
    if fd < 0:
        err = _ffi.errno
        if err == _errno.EINVAL:
            if not clock_type  & (CLOCK_MONOTONIC|CLOCK_REALTIME):
                raise ValueError("clock_type is not one of CLOCK_MONOTONIC or CLOCK_REALTIME")
            raise ValueError("Invalid value in flags")
        elif err == _errno.EMFILE:
            raise OSError("Max per process FD limit reached")
        elif err == _errno.ENFILE:
            raise OSError("Max system FD limit reached")
        elif err == _errno.ENODEV:
            raise OsError("Could not mount (internal) anonymous inode device")
        elif err == _errno.ENOMEM:
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
    curr_val = _ffi.new('struct itimerspec *')
    ret = _C.timerfd_gettime(fd, curr_val)
    
    if ret < 0:
        err = _ffi.errno
        if err == _errno.EBADF:
            raise ValueError("fd is not a valid file descriptor")
        elif err == _errno.EFAULT:
            raise IOError("curr_val is not a valid pointer (internal/bug, let us know)")
        elif err == _errno.EINVAL:
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
    
    old_timer_spec = _ffi.new('struct itimerspec *')

    ret = _C.timerfd_settime(fd, flags, timer_spec, old_timer_spec)
    
    if ret < 0:
        err = _ffi.errno
        if err == _errno.EINVAL:
            if timer_spec.it_interval.tv_sec > 999999999:
                raise ValueError("Nano seconds in it_interval is > 999,999,999")
            elif timer_spec.it_value.tv_nsec > 999999999:
                raise ValueError("Nano seconds in it_value is > 999,999,999")
            else:
                raise ValueError('flags is invalid or fd not a timerfd')
        elif err == _errno.EFAULT:
            raise IOError("timer_spec does not point to a valid timer specfication")
        elif err == _errno.EMFILE:
            raise OSError("Max per process FD limit reached")
        elif err == _errno.ENFILE:
            raise OSError("Max system FD limit reached")
        elif err == _errno.ENODEV:
            raise OsError("Could not mount (internal) anonymous inode device")
        elif err == _errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory available")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))
            
    old_timer_spec = TimerSpec(timerspec=old_timer_spec)
    return old_timer_spec

class TimerSpec(object):
    def __init__(self, reoccuring=None, reoccuring_sec=None, reoccuring_nano=None, 
                       one_off=None, one_off_sec=None, one_off_nano=None,
                       timerspec=None):
   
        if timerspec:
            self._timerspec = timerspec
        else:
            self._timerspec = _ffi.new('struct itimerspec *')
            
        if reoccuring:
            self.reoccuring = reoccuring
        if reoccuring_sec:
            self.reoccuring_sec = reoccuring_sec
        if reoccuring_nano:
            self.reoccuring_nano = reoccuring_nano
        if one_off:
            self.one_off = one_off
        if one_off_sec:
            self.one_off_sec = one_off_sec
        if one_off_nano:
            self.one_off_nano = one_off_nano
    
    @property
    def reoccuring(self):
        return self.reoccuring_sec + (self.reoccuring_nano / 1000000000)
        
    @reoccuring.setter
    def reoccuring(self, val):
        if isinstance(val, float):
            x, y = _math.modf(val)
            sec = int(y)
            nano = round(1000000000 * x)
        else:
            sec = val
            nano = 0
        
        self.reoccuring_sec = sec
        self.reoccuring_nano = nano
    
    @property
    def reoccuring_sec(self):
        return self._timerspec.it_interval.tv_sec
        
    @reoccuring_sec.setter
    def reoccuring_sec(self, val):
        self._timerspec.it_interval.tv_sec = val

    @property
    def reoccuring_nano(self):
        return self._timerspec.it_interval.tv_nsec
    
    @reoccuring_nano.setter
    def reoccuring_nano(self, val):
        self._timerspec.it_interval.tv_nsec = val

    @property
    def one_off(self):
        return self.one_off_sec + (self.one_off_nano / 1000000000)
        
    @one_off.setter
    def one_off(self, val):
        if isinstance(val, float):
            x, y = _math.modf(val)
            sec = int(y)
            nano = round(1000000000 * x)
        else:
            sec = val
            nano = 0
        
        self.one_off_sec = sec
        self.one_off_nano = nano

    @property
    def one_off_sec(self):
        return self._timerspec.it_value.tv_sec
        
    @one_off_sec.setter
    def one_off_sec(self, val):
        self._timerspec.it_value.tv_sec = val

    @property
    def one_off_nano(self):
        return self._timerspec.it_value.tv_nsec
    
    @one_off_nano.setter
    def one_off_nano(self, val):
        self._timerspec.it_value.tv_nsec = val
    
    def __timerspec__(self):
        return self._timerspec
    
    def __bool__(self):
        return False is self.one_off == 0.0 else True
    
    @property
    def enabled(self):
        return bool(self)
    
    @property
    def disabled(self):
        return not self.enabled

TFD_CLOEXEC = _C.TFD_CLOEXEC
TFD_NONBLOCK = _C.TFD_NONBLOCK
TFD_TIMER_ABSTIME = _C.TFD_TIMER_ABSTIME

CLOCK_REALTIME = _C.CLOCK_REALTIME
CLOCK_MONOTONIC = _C.CLOCK_MONOTONIC

class Timerfd(object):
    def __init__(self, clock_type=CLOCK_REALTIME, flags=0):
        """Create a new Timerfd object

        Arguments
        ----------
        :param int clock_type: The type of clock to use for timing
        :param int flags: Flags to specify extra options
        
        Flags
        ------
        CLOCK_REALTIME: Use a time source that matches the wall time
        CLOCK_MONOTONIC: Use a monotonically incrementing time source
        TFD_CLOEXEC: Close the timerfd when executing a new program
        TFD_NONBLOCK: Open the socket in non-blocking mode
        """
        self._fd = timerfd_create(clock_type, flags)
        self._timerspec = TimerSpec()
    
    def set_one_off(self, seconds, nano_seconds=None, absolute=False, update=True):
        self._timerspec.one_off = seconds
        if nano_seconds:
            self._timerspec.one_off_nano = nano_seconds
        
        old_val = None
        if update:
            old_val = self._update(absolute=absolute)
        
        return old_val
        
    def set_reoccuring(self, seconds, nano_seconds=None, absolute=False):
        self._timerspec.reoccuring = seconds
        if nano_seconds:
            self._timerspec.reoccuring_nano = seconds
        
        # prime the timer with the same val
        self.set_one_off(seconds, nano_seconds, update=update)

        old_val = None
        # Allow disabling of the update function in case we wish
        # to set the inital period to somthign diffrent
        if update:
            old_val = self._update(absolute=absolute)
        
        return old_val

    def _update(self, absolute=False):
        flags = TFD_TIMER_ABSTIME if absolute else 0
        old_timer = timerfd_settime(self._fd, self._timerspec, flags)
        
        return old_timer
    
    def wait(self):
        """Wait for the next timer event (ethier one off or periodic)
        
        Returns
        --------
        :return: The amount of timerfd events that have fired since the last read()
        :rtype: int
        """
        select([self._fd], [], [])
        
        data = _read(self._fd, 8)
        value = _ffi.new('uint64_t[1]')
        _ffi.buffer(value, 8)[0:8] = data

        return value[0]
    
    def close(self):
        _close(self._fd)

    def fileno(self):
        return self._fd

    @property
    def enabled(self):
        return self.timer_val.enabled

    @enabled.setter
    def enabled(self, val):
        assert isinstance(val, bool), "enabled() requires a boolean"
        self.timer_val.enabled = val
        
        self._update()

    @property
    def disabled(self):
        return not self.enabled

    @disabled.setter
    def disabled(self, val):
        assert isinstance(val, bool), "disabled() requires a boolean"
        self.timer_val.disabled = val

        self._update()

def _main():
    pass
        
# import asyncio code if avalible
# must be done here as otherwise the module's dict
# does not have the required functions defined yet
# as it is a circular import
import platform
#if platform.python_version_tuple() >= ('3', '4', '0'):
#    from .asyncio.eventfd import Eventfd as Eventfd_async
    
if __name__ == "__main__":
    _main()
