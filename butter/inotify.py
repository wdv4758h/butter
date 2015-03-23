#!/usr/bin/env python
"""inotify: Wrapper around the inotify syscalls providing both a function based and file like interface"""

from .utils import get_buffered_length as _get_buffered_length
from .utils import Eventlike as _Eventlike
from .utils import CLOEXEC_DEFAULT as _CLOEXEC_DEFAULT

from ._inotify import inotify_init, inotify_add_watch, inotify_rm_watch
from ._inotify import str_to_events
from ._inotify import event_name

from errno import EINVAL as _EINVAL

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
            self._blocking = False
        else:
            self._blocking = True
        
    def watch(self, path, events):
        wd = inotify_add_watch(self.fileno(), path, events)
        
        return wd
        
    def del_watch(self, wd):
        self.ignore(wd)

    def ignore(self, wd):
        inotify_rm_watch(self.fileno(), wd)
        
    def _read_events(self):
        fd = self.fileno()
        
        # The following code is complex but required to get the same values with
        # expected behavior with blocking/non-blocking fd's
        # blockers will block, non-blockers will return []
        buf_len = _get_buffered_length(fd)
        if buf_len == 0:
            try:
                _os.read(fd, 0)
            except OSError as err:
                # eat the OS error as the ammount of bytes in the buffer may have increased from 0
                # between the _get_buffered_length and here, we eat the exception and try again
                # so the caller does not ahve to deal with it. if there is a greater issue
                # the second read should blow up
                if err.errno != _EINVAL:
                    raise
                pass
            buf_len = _get_buffered_length(fd)
        raw_events = _os.read(fd, buf_len)

        events = str_to_events(raw_events)

        return events

def watch(path, events=IN_ALL_EVENTS):
    """Quick Convience function to watch a file or dir for any changes

    If a dir argument is provided this call will not recursively watch the directories
    due to limitations in inotify's API. if you wish to watch directories recursively
    you will need to recurs it yourself and add the watches manually

    Warning: if using this function to watch a file or dir repeatedly you may miss events
    due to a race condition, consider using the Inotify object instead to get all the 
    file events
    
    This function will not watch directories recursively if given a directory as an 
    argument and will only return events occurring in that directory
    
    Arguments
    ----------
    :param str path: the file/dir to watch for events to occur on
    :param int events: The inotify IN_* events to watch path for

    Returns
    --------
    :return: The file descriptor representing the signalfd
    :rtype: int

    """
    inotify = Inotify()
    try:
        wd = inotify.watch(path, events)
        event = inotify.wait()
    finally:
        inotify.close()
    
    return event
