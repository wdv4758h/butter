#!/usr/bin/env python
"""timerfd: recive timing events on a file descriptor"""

from .utils import Eventlike as _Eventlike
from .utils import CLOEXEC_DEFAULT as _CLOEXEC_DEFAULT
from ._timerfd import TimerVal, timerfd, timerfd_gettime, timerfd_settime
from ._timerfd import TFD_CLOEXEC, TFD_NONBLOCK, TFD_TIMER_ABSTIME
from ._timerfd import CLOCK_REALTIME, CLOCK_MONOTONIC
from ._timerfd import ffi as _ffi
import os as _os

class Timer(_Eventlike, TimerVal):
    """Timer is both an event like object providing the file-like/event-like interface as well
    as a TimerVal object to allow setting of the periodicity and offset of the timer in a single
    interface without creating a separate throw away TimerVal object
    
    To use, instance an instance as per normal:
    
    >>> t = Timer()
    
    Then manipulate the timer using the TimerVal like interface:
    
    >>> t.occuring.every(seconds=1).after(seconds=500000000)
    
    Finally, use the Timer object as you would normally for an event like object:
    
    >>> for i, event in enumerate(t):
    ...     print ("Timer Fired")
    ...     if i >= 2: break
    
    This should print 'Timer Fired' after 0.5s followed by 1s after that

    read()ing and wait()ing on this socket returns an integer representing the amount
    of timer expiration's since the last time the timer was read. This can be used to make
    a high precision low overhead timer by using a repeating event with an expiry
    of 1ns and then using read() to get the amount of elapsed nano seconds. This has
    near 0% cpu overhead. Using the timer in this manner is refered to as an 'interval
    timer'
    """
    def __init__(self, clock_type=CLOCK_MONOTONIC, flags=0, closefd=_CLOEXEC_DEFAULT):
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
        super(self.__class__, self).__init__()
        self._fd = timerfd(clock_type, flags, closefd=closefd)
    
    def get_current(self):
        """Retrives the current values of the timer from the kernel
        
        Returns
        --------
        :return: The old timer value
        :rtype: TimerVal
        """
        return timerfd_gettime(self.fileno())

    def update(self, absolute=False):
        """Update the kernel with the current values for the timer
        
        Arguments
        ---------
        :param bool absolute: Determines if the values in the timer should be considered absolute
        (seconds since UNIX epoch) or if they should be added to the current time to determine
        when the next event occurs
        
        Returns
        --------
        :return: The old timer value
        :rtype: TimerVal
        """
        flags = TFD_TIMER_ABSTIME if absolute else 0
        old_timer = timerfd_settime(self.fileno(), self._timerspec, flags)
        
        return old_timer
    
    def _read_events(self):
        data = _os.read(self.fileno(), 8)
        value = _ffi.new('uint64_t[1]')
        _ffi.buffer(value, 8)[0:8] = data

        return [value[0]] # value's container is not a list
                          # lets make it one to expose a fammliar
                          # interface
    def __repr__(self):
            fd = "closed" if self.closed() else self.fileno()
            return "<{} fd={} offset=({}s, {}ns) reoccuring=({}s, {}ns)>".format(self.__class__.__name__,
                                                                           fd,
                                                                           self._timerspec.it_value.tv_sec,
                                                                           self._timerspec.it_value.tv_nsec,
                                                                           self._timerspec.it_interval.tv_sec,
                                                                           self._timerspec.it_interval.tv_nsec)

