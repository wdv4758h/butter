#!/usr/bin/env python
"""fanotify: wrapper aroudn the fanotify family of syscalls for watching for file modifcation"""

from cffi import FFI as _FFI
from os import O_RDONLY, O_WRONLY, O_RDWR
from os import fdopen
import errno as _errno

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

typedef struct fanotify_event_metadata { ...; };
typedef struct fanotify_response { ...; };

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
    
def fanotify_mark():
    """Add a file to a fanotify context"""
    """
    EBADF: an invalid fd was passed in
    EINVAL: an invalid flag or mask was passed in
    ENOENT: directory is invalid or directory/mount not marked
    ENOMEM: no mem avalible
    ENOSPC: Too many marks
    """
    pass
    
def main():
    print _ffi.new('struct fanotify_event_metadata *')
    print _ffi.new('struct fanotify_response *')
    fd = _C.fanotify_init(_C.FAN_CLASS_NOTIF, O_RDONLY)
    if fd < 0:
        print 'fd error'
        exit(1)
    f = fdopen(fd)
    err = _C.fanotify_mark(f.fileno(), _C.FAN_MARK_ADD, _C.FAN_MODIFY, 0, '/tmp/testing')
    print err
    f.read(60)
    print 'recived write event'

# make things a tiny bit more accsessable rather than going via the '__C' object
import fanotify
for key, val in _C.__dict__.iteritems():
    if key.startswith('FAN_'):
        fanotify.__dict__[key] = val
del fanotify

if __name__ == "__main__":
    main()
