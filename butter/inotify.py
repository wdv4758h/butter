#!/usr/bin/env python
"""inotify: Wrapper around the inotify syscalls providing both a function based and file like interface"""

from .utils import get_buffered_length as _get_buffered_length
from .utils import Eventlike as _Eventlike
from .utils import CLOEXEC_DEFAULT as _CLOEXEC_DEFAULT

from ._inotify import inotify_init, inotify_add_watch, inotify_rm_watch
from ._inotify import str_to_events
from ._inotify import event_name

import os as _os

# Import all the constants
from ._inotify import C as _C
_l = locals()
for key in dir(_C):
    if key.startswith('IN_'):
        _l[key] = getattr(_C, key)
del key, _C, _l

class Inotify(_Eventlike):
    def __init__(self, flags=0, closefd=_CLOEXEC_DEFAULT):
        super(self.__class__, self).__init__()
        fd = inotify_init(flags, closefd=closefd)
        self._fd = fd
        
        self._events = []

        if flags & IN_NONBLOCK:
            self.blocking = false
        
    def watch(self, path, events):
        wd = inotify_add_watch(self.fileno(), path, events)
        
        return wd
        
    def del_watch(self, wd):
        self.ignore(wd)

    def ignore(self, wd):
        inotify_rm_watch(self.fileno(), wd)
        
    def _read_events(self):
        fd = self.fileno()
        
        buf_len = _get_buffered_length(fd)
        raw_events = _os.read(fd, buf_len)

        events = str_to_events(raw_events)

        return events
