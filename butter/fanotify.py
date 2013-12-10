#!/usr/bin/env python
"""fanotify: wrapper around the fanotify family of syscalls for watching for file modifcation"""

from utils import get_buffered_length as _get_buffered_length
from os import getpid as _getpid, readlink as _readlink
from os import fdopen as _fdopen, close as _close
from os import read as _read
from os import O_RDONLY, O_WRONLY, O_RDWR
from os.path import join as _path_join
from select import select as _select
from collections import namedtuple
from cffi import FFI as _FFI
import errno as _errno

READ_EVENTS_MAX = 10

_ffi = _FFI()
_ffi.cdef("""
#define FAN_CLOEXEC ...
#define FAN_NONBLOCK ...
#define FAN_CLASS_NOTIF ...
#define FAN_CLASS_CONTENT ...
#define FAN_CLASS_PRE_CONTENT ...
#define FAN_UNLIMITED_QUEUE ...
#define FAN_UNLIMITED_MARKS ...

#define FAN_MARK_ADD ...
#define FAN_MARK_REMOVE ...
#define FAN_MARK_DONT_FOLLOW ...
#define FAN_MARK_ONLYDIR ...
#define FAN_MARK_MOUNT ...
#define FAN_MARK_IGNORED_MASK ...
#define FAN_MARK_IGNORED_SURV_MODIFY ...
#define FAN_MARK_FLUSH ...

#define FAN_ALL_MARK_FLAGS ...

#define FAN_ACCESS ...
#define FAN_MODIFY ...
#define FAN_CLOSE_WRITE ...
#define FAN_CLOSE_NOWRITE ...
#define FAN_OPEN ...
#define FAN_Q_OVERFLOW ...
#define FAN_OPEN_PERM ...
#define FAN_ACCESS_PERM ...
#define FAN_ONDIR ...
#define FAN_EVENT_ON_CHILD ...

// FAN_CLOSE_WRITE|FAN_CLOSE_NOWRITE
#define FAN_CLOSE ...

// Access control flags
#define FAN_ALLOW ...
#define FAN_DENY ...

// #define FAN_EVENT_OK ...
// #define FAN_EVENT_NEXT ...


struct fanotify_response {
    int32_t fd;
    uint32_t response;
};

//#define __aligned_u64 __u64 __attribute__((aligned(8)))
struct fanotify_event_metadata {
    uint32_t event_len;
    uint8_t vers;
    uint8_t reserved;
    uint16_t metadata_len;
    uint64_t mask;
    int32_t fd;
    int32_t pid;
};


int fanotify_init(unsigned int flags, unsigned int event_f_flags);
int fanotify_mark (int fanotify_fd, unsigned int flags, uint64_t mask, int dfd, const char *pathname);
""")

_C = _ffi.verify("""
#include <linux/fcntl.h>
#include <sys/fanotify.h>
""", libraries=[])

class Fanotify(object):
    _closed = True
    _fileno = None
    blocking = True
    def __init__(self, flags, event_flags=O_RDONLY):
        fd = fanotify_init(flags, event_flags)
        self._closed = True
        self._fileno = fd

        self._events = []

        if flags & FAN_NONBLOCK:
            self.blocking = false

    def watch(self, flags, mask, path, dfd=0):
        flags |= FAN_MARK_ADD
        fanotify_mark(self._fileno, flags, mask, path, dfd)

    def del_watch(self, flags, mask, path, dfd=0):
        flags |= FAN_MARK_REMOVE
        fanotify_mark(self._fileno, flags, mask, path, dfd)

    def fileno(self):
        return self._fileno

    def close(self):
        os.close(self._fileno)

    def closed(self):
        return self._closed

    def isatty(self):
        return False

    def mode(self):
        return "r"

    def name(self):
        return "<fanotify fd:{}>".format(self._fileno)

    def read(self):
        raise NotImplemented

    def readable(self):
        return False

    def readlines(self):
        raise NotImplemented

    def seek(self):
        raise NotImplemented

    def seekable(self):
        return False

    def tell(self):
        return 0

    def truncate(self):
        """Discard all events in the queue"""
        self._events = []

    def write(self):
        raise NotImplemented

    def writable(self):
        return False

    def writelines(self):
        raise NotImplemented

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
        """Read and return multiple events from the kernel"""
        events = self._events
        self._events = []
        if len(events) > 0:
            return events
        else:
            return self._read_events()

    def _read_events(self):
        if self.blocking:
            _select([self._fileno], [], [])
            buf_len = _get_buffered_length(self._fileno)
        else:
            buf_len = _get_buffered_length(self._fileno)
            assert buf_len > 0, "_read_event called in non blocking mode when nothing to read"
        raw_events = _read(self._fileno, buf_len)

        events = str_to_events(raw_events)

        return events

    def __repr__(self):
        return '<Fanotify fd={}>'.format(self._fileno)

    def __iter__(self):
        while True:
            yield self.read_event()

    
def fanotify_init(flags, event_flags=O_RDONLY):
    """Create a fanotify handle
    """
    fd = _C.fanotify_init(flags, event_flags)
    if fd < 0:
        err = _ffi.errno
        if err == _errno.EINVAL:
            raise ValueError("Invalid argument or flag")
        elif err == _errno.EMFILE:
            raise OSError("Maximum fanotify instances reached or cant Queue/Mark limits")
        elif err == _errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory avalible")
        elif err == _errno.EPERM:
            raise OSError("Operation not permitted")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))
                                            
    return fd

def fanotify_mark(fd, flags, mask, path, dfd=0):
    """Add a file to a fanotify context"""
    """
    EINVAL: an invalid flag or mask was passed in
    EBADF: an invalid fd was passed in
    ENOENT: directory is invalid or directory/mount not marked
    ENOMEM: no mem avalible
    ENOSPC: Too many marks
    """
    ret = _C.fanotify_mark(fd, flags, mask, dfd, path)
    if ret < 0:
        err = _ffi.errno
        if err == _errno.EINVAL:
            raise ValueError("Invalid flag or mask")
        elif err == _errno.EBADF:
            raise OSError("fd does not exist or was of the incorrect type")
        elif err == _errno.ENOENT:
            raise OSError("DIrectory is invalid of directory/mount not marked")
        elif err == _errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory avalible")
        elif err == _errno.ENOSPC:
            raise OSError("Too many marks")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))

class FanotifyEvent(object):
    _filename = None
    def __init__(self, version, mask, fd, pid):
        self.version = version
        self.mask = mask
        self.fd = fd
        self.pid = pid
                
    @property
    def filename(self):
        if not self._filename:
            try:
                name = _readlink(_path_join('/proc', str(_getpid()), 'fd', str(self.fd)))
                self._filename = name
            except OSError:
                self._filename = "<Unknown>"
    
        return self._filename
        
    def close(self):
        _close(self.fd)

    def __repr__(self):
        return "<FanotifyEvent filename={}, version={}, mask=0x{:X}, fd={}, pid={}>".format(
                self.filename, self.version, self.mask, self.fd, self.pid)

def str_to_events(str):
    event_struct_size = _ffi.sizeof('struct fanotify_event_metadata')

    events = []

    str_buf = _ffi.new('char[]', len(str))
    str_buf[0:len(str)] = str

    i = 0
    while i < len(str_buf):
        event = _ffi.cast('struct fanotify_event_metadata *', str_buf[i:i+event_struct_size])
        events.append(FanotifyEvent(event.vers, event.mask, event.fd, event.pid))

        i += event.event_len

    return events

    
def main():
    notifier = Fanotify(FAN_CLASS_NOTIF)
    FLAGS = FAN_MODIFY|FAN_ONDIR|FAN_ACCESS|FAN_EVENT_ON_CHILD|FAN_OPEN|FAN_CLOSE
    notifier.watch(0, FLAGS, '/tmp')

    for event in notifier:
        print "================================"
        print 'Version:        ', event.version
        print 'Mask:            0x{:08X}'.format(event.mask)
        print 'Writer PID:     ', event.pid
        print 'fd:             ', event.fd
        print 'filename:       ', event.filename
        event.close()

# Provide a nice ID to NAME mapping for debugging
signal_name = {}
# Make the fanotify flags more easily accessible by hoisting them out of the _C object
l = locals()
for key, value in _C.__dict__.iteritems():
    if key.startswith("FAN_"):
        signal_name[value] = key
        l[key] = value
# <_<
# >_>
# -_- <(This never happened, what you just saw was light reflecting off Venus)
del l
del key, value # python 2.x has vars escape from the scope of the loop, clean this up

if __name__ == "__main__":
    main()

