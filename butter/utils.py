#!/usr/bin/env python

from select import select as _select
from cffi import FFI as _FFI
from os import close as _close
from collections import deque
import fcntl
import array
import errno

import platform

# Hack to backport PermissionError to older python versions
if platform.python_version_tuple() < ('3', '0', '0'):
    class PermissionError(OSError):
        """You do not have the required pemissions to use this syscall (CAP_SYS_ADMIN)"""
        pass
PermissionError = PermissionError

class InternalError(Exception):
    """This Error occured due to an internal bug or OS misconfiguration"""

class UnknownError(Exception):
    """This error is not handled and is unexpected by this library"""
    def __init__(self, errno):
        self.errno = errno
    
    def __str__(self):
        error_name = errno.errorcode.get(self.errno, "UNKNOWN")
        return "{}: Error: {} ({})".format(self.__doc__, self.errno, error_name)

_ffi = _FFI()
_ffi.cdef("""
#define FIONREAD ...
""")

_C = _ffi.verify("""
#include <sys/ioctl.h>
""", libraries=[], ext_package="butter")

def get_buffered_length(fd):
    buf = array.array("I", [0])
    fcntl.ioctl(fd, _C.FIONREAD, buf)
    return buf[0]
            

class Eventlike(object):
    _fd = None
    def __init__(self, *args, **kwargs):
        """*** This is a cooprative superclass, ensure you use super in the subclass's __init__ ***
        eg: super(self.__class__, self).__init__(*args, **kwargs)
        """
        self._events = []
        super(Eventlike, self).__init__()
    
    def close(self):
        _close(self.fileno())
        self._fd = None

    def fileno(self):
        if self._fd:
            return self._fd
        else:
            raise ValueError("I/O operation on closed file")

    def wait(self):
        # we use select here as the FD may be opened in non blocking mode
        _select([self.fileno()], [], [])

        return self.read_event()

    def closed(self):
        return False if self._fd else True

    def isatty(self):
        return False

    def mode(self):
        return getattr(self, '_mode', "r")

    def name(self):
        return repr(self)

    def read(self):
        raise NotImplementedError

    def readable(self):
        mode = getattr(self, '_mode', "r")
        return True if 'r' in mode or '+' in mode else False

    def readlines(self):
        raise NotImplementedError

    def seek(self):
        raise NotImplementedError

    def seekable(self):
        return False

    def tell(self):
        return 0

    def truncate(self):
        """Discard all events in the queue"""
        self._events = []

    def write(self):
        raise NotImplementedError

    def writable(self):
        mode = getattr(self, '_mode', "r")
        return True if 'w' in mode else False

    def writelines(self):
        raise NotImplementedError

    def __repr__(self):
        fd = "closed" if self.closed() else self.fileno()
        return "<{} fd={}>".format(self.__class__.__name__, fd)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if other._fd == self._fd:
                return True
        return False

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            if other._fd != self._fd:
                return True
        return False

    def __hash__(self):
        return hash(self.__class__) ^ hash(self._fd)


    ### Event like behavior ###
    def __iter__(self):
        while True:
            yield self.wait()

    def read_event(self):
        """Return a single event, may read more than one event from the kernel and cache the values
        """
        try:
            event = self._events.pop(0)
        except IndexError:
            events = self._read_events()
            event = events.pop(0)
            self._events = events

        return event

    def read_events(self):
        """Read and return multiple events from the kernel
        """
        events = self._events
        self._events = []
        if len(events) > 0:
            return events
        else:
            return self._read_events()

