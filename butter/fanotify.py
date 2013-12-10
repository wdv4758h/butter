#!/usr/bin/env python
"""fanotify: wrapper around the fanotify family of syscalls for watching for file modifcation"""

from utils import get_buffered_length as _get_buffered_length
from os import getpid as _getpid, readlink as _readlink
from os import fdopen as _fdopen, close as _close
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

class FANotify(object):
    def __init__(self, flags=0, mode='r'):
        """Create a new fanotify context to track file modification/creation/deleteion
        
        :param integer flags: Define what type of fanotify context you wish to open, can be a mix of the following
                      FAN_CLOEXEC, FAN_NONBLOCK, FAN_CLASS_NOTIF, FAN_CLASS_CONTENT, FAN_CLASS_PRE_CONTENT
                      FAN_UNLIMITED_QUEUE, FAN_UNLIMITED_MARKS
        :param integer mode: str or int. when used with a str, behaves identically to the 'mode' keyword in open()
        
        :raises ValueError: If ethier flags or mode contains an invalid value, this will be raised
        :raises IOError: Raised for any of the following conditions:
                         Number of listeners exceeds FANOTIFY_DEFAULT_MAX_LISTENERS
                         flag FAN_UNLIMITED_QUEUE was set without the CAP_SYS_ADMIN capability
                         flag FAN_UNLIMITED_MARKS was set without the CAP_SYS_ADMIN capability
        :raises OSError: Raised on permissions issue or Non memory avalible
        
        """
        if isinstance(mode, str):
            if '+' in mode:
                mode = O_RDWR
            elif 'w' in mode:
                mode = O_WRONLY
            elif 'r' in mode:
                mode = O_RDONLY

        fd = _C.fanotify_init(flags, mode)

        if fd < 0:
            # handle error cases
            error = _ffi.errno
            if error == _errno.EINVAL:
                # EINVAL: Flags contains invalid options $FAN_ALL_INIT_FLAGS indicates valid flags
                raise ValueError('"flags" contains invalid values')
            elif error == _errno.EMFILE:
                # EMFILE: indicates one of the following situations:
                #         - The number of listeners exceeds FANOTIFY_DEFAULT_MAX_LISTENERS.
                #         - Flag FAN_UNLIMITED_QUEUE was set without owning the CAP_SYS_ADMIN capability.
                #         - Flag FAN_UNLIMITED_MARKS was set without owning the CAP_SYS_ADMIN capability.
                raise IOError('Max listeners exceeded or do not have CAP_SYS_ADMIN')
            elif error == _errno.ENOMEM:
                # ENOMEM: No mem avalible
                raise OSError('No Mem avalibel to service request')
            elif error == _errno.EPERM:
                # EPERM: Operation not permitted, may need root/CAP_SYS_ADMIN
                raise OSError('Operation not permitted')
            else:
                raise Exception('Unknown Error')
            
        self._fd = fd
        pass
    
    def fileno(self):
        """Returns the file descriptor associated with the fanotify handle
        
        :returns int: The file descriptor used for the fanotify handle
        """
        return self._fd
    
    def add_watch(self):
        pass

    def del_watch(self):
        pass

    def flush_watches(self):
        pass
    
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
    fd = fanotify_init(_C.FAN_CLASS_NOTIF)
    f = _fdopen(fd)
    FLAGS = FAN_MODIFY|FAN_ONDIR|FAN_ACCESS|FAN_EVENT_ON_CHILD|FAN_OPEN|FAN_CLOSE
    fanotify_mark(f.fileno(), FAN_MARK_ADD, FLAGS, '/')

#    read_size = READ_EVENTS_MAX * _ffi.sizeof('fanotify_event_metadata')
    read_size = 1 * _ffi.sizeof('struct fanotify_event_metadata')
    print 'Read size: {}'.format(read_size)

    while True:
        buf = f.read(read_size)
    
        str_buf = _ffi.new('char[]', len(buf))
        str_buf[0:len(buf)] = buf
                    
    #    events = _ffi.new('struct fanotify_event_metadata *',)
        events = _ffi.cast('struct fanotify_event_metadata *', str_buf)
        print "================================"
        print 'Event Length:   ', events.event_len
        print 'Version:        ', events.vers
        print 'Metadata Length:', events.metadata_len
        print 'Mask:           ', events.mask
        print 'Writer PID:     ', events.pid
        print 'fd:             ', events.fd
        import os
        print 'filename:       ', os.readlink(os.path.join('/proc', str(os.getpid()), 'fd', str(events.fd)))
        os.close(events.fd)


# Provide a nice ID to NAME mapping for debugging
signal_name = {}
# Make the inotify flags more easily accessible by hoisting them out of the _C object
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

