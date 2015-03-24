#!/usr/bin/env python
"""timerfd: recive timing events on a file descriptor"""

from .utils import Eventlike as _Eventlike
from .utils import CLOEXEC_DEFAULT as _CLOEXEC_DEFAULT
from ._timerfd import TimerVal, TimerSpec, timerfd, timerfd_gettime, timerfd_settime
from ._timerfd import TFD_CLOEXEC, TFD_NONBLOCK, TFD_TIMER_ABSTIME
from ._timerfd import CLOCK_REALTIME, CLOCK_MONOTONIC
from ._timerfd import ffi as _ffi
import os as _os

class Timerfd(_Eventlike):
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
        self._timerspec = TimerSpec()
    
    def set_one_off(self, seconds, nano_seconds=0, absolute=False):
        timer = TimerSpec()
        timer.one_off = seconds
        timer.one_off = nano_seconds
        
        old_val = self._update(timer, absolute=absolute)
        
        return old_val
        
    def set_reoccuring(self, seconds, nano_seconds=0, 
                             next_seconds=0, next_nano_seconds=0,
                             absolute=False):
        timer = TimerSpec()
        # set nano seconds first, if seconds is a float it
        # will get overidden. this was we dont need any
        # if conditionals/guards
        timer.reoccuring_nano = nano_seconds
        timer.reoccuring = seconds
        
        if next_seconds or next_nano_seconds:
            timer.one_off = next_nano_seconds
            timer.one_off = next_seconds
        else:
            timer.one_off = nano_seconds
            timer.one_off = seconds

        old_val = self._update(timer, absolute=absolute)
        
        return old_val

    def get_current(self):
        return timerfd_gettime(self.fileno())

    def _update(self, timerspec, absolute=False):
        flags = TFD_TIMER_ABSTIME if absolute else 0
        old_timer = timerfd_settime(self.fileno(), timerspec, flags)
        
        return old_timer
    
    @property
    def enabled(self):
        return self.get_current().enabled

    @property
    def disabled(self):
        return not self.enabled

    def disable(self):
        timer = self.get_current()
        timer.disable()

        self._update(timer)

    def _read_events(self):
        data = _os.read(self.fileno(), 8)
        value = _ffi.new('uint64_t[1]')
        _ffi.buffer(value, 8)[0:8] = data

        return [value[0]] # value's container is not a list
                          # lets make it one to expose a fammliar
                          # interface
