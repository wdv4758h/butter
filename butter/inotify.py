#!/usr/bin/env python
"""inotify: Wrapper around the inotify syscalls providing both a function based and file like interface"""

from utils import get_buffered_length as _get_buffered_length
from select import select as _select
from collections import namedtuple
from os import read as _read
from cffi import FFI as _FFI
import errno as _errno

_ffi = _FFI()
_ffi.cdef("""
/*
 * struct inotify_event - structure read from the inotify device for each event
 *
 * When you are watching a directory, you will receive the filename for events
 * such as IN_CREATE, IN_DELETE, IN_OPEN, IN_CLOSE, ..., relative to the wd.
 */
struct inotify_event {
        int           wd;
        uint32_t      mask;
        uint32_t      cookie;
        uint32_t      len;
//        char          name[0];
};

/* the following are legal, implemented events that user-space can watch for */
#define IN_ACCESS        ...  /* File was accessed */
#define IN_MODIFY        ...  /* File was modified */
#define IN_ATTRIB        ...  /* Metadata changed */
#define IN_CLOSE_WRITE   ...  /* Writtable file was closed */
#define IN_CLOSE_NOWRITE ...  /* Unwrittable file closed */
#define IN_OPEN          ...  /* File was opened */
#define IN_MOVED_FROM    ...  /* File was moved from X */
#define IN_MOVED_TO      ...  /* File was moved to Y */
#define IN_CREATE        ...  /* Subfile was created */
#define IN_DELETE        ...  /* Subfile was deleted */
#define IN_DELETE_SELF   ...  /* Self was deleted */
#define IN_MOVE_SELF     ...  /* Self was moved */

/* the following are legal events.  they are sent as needed to any watch */
#define IN_UNMOUNT       ...  /* Backing fs was unmounted */
#define IN_Q_OVERFLOW    ...  /* Event queued overflowed */
#define IN_IGNORED       ...  /* File was ignored */

/* helper events */
#define IN_CLOSE         ...  /* close */
#define IN_MOVE          ...  /* moves */

/* special flags */
#define IN_ONLYDIR       ...  /* only watch the path if it is a directory */
#define IN_DONT_FOLLOW   ...  /* don't follow a sym link */
#define IN_EXCL_UNLINK   ...  /* exclude events on unlinked objects */
#define IN_MASK_ADD      ...  /* add to the mask of an already existing watch */
#define IN_ISDIR         ...  /* event occurred against dir */
#define IN_ONESHOT       ...  /* only send event once */

/*
 * All of the events - we build the list by hand so that we can add flags in
 * the future and not break backward compatibility.  Apps will get only the
 * events that they originally wanted.  Be sure to add new events here!
 */
#define IN_ALL_EVENTS  ...

/* Flags for sys_inotify_init1.  */
#define IN_CLOEXEC  ...
#define IN_NONBLOCK ...

int inotify_init(void);
int inotify_init1(int flags);
int inotify_add_watch(int fd, const char *pathname, uint32_t mask);
int inotify_rm_watch(int fd, int wd);
""")

_C = _ffi.verify("""
#include <sys/inotify.h>
#include <sys/ioctl.h>
""", libraries=[])

def inotify_init(flags=0):
    """Initialise an inotify instnace and return a File Descriptor to refrence is
    
    Arguments:
    -----------
    Flags:
    -------
    IN_CLOEXEC: Automatically close the inotify handle on exec()
    IN_NONBLOCK: Place the file descriptor in non blocking mode
    """
    fd = _C.inotify_init1(flags)
    
    if fd < 0:
        err = _ffi.errno
        if err == _errno.EINVAL:
            raise ValueError("Invalid argument or flag")
        elif err == _errno.EMFILE:
            raise OSError("Maximum inotify instances reached")
        elif err == _errno.ENFILE:
            raise OSError("File descriptor limit hit")
        elif err == _errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory avalible")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))

    return fd
    
def inotify_add_watch(fd, path, mask):
    """Start watching a filepath for events
    
    Arguments:
    -----------
    fd:    The inotify file descriptor to attach the watch to
    path:  The path to the file/directory to be monitored for events
    mask:  The events to listen for
    
    Flags:
    -------
    IN_ACCESS:        File was accessed
    IN_MODIFY:        File was modified
    IN_ATTRIB:        Metadata changed
    IN_CLOSE_WRITE:   Writtable file was closed
    IN_CLOSE_NOWRITE: Unwrittable file closed
    IN_OPEN:          File was opened
    IN_MOVED_FROM:    File was moved from X
    IN_MOVED_TO:      File was moved to Y
    IN_CREATE:        Subfile was created
    IN_DELETE:        Subfile was deleted
    IN_DELETE_SELF:   Self was deleted
    IN_MOVE_SELF:     Self was moved

    IN_ONLYDIR:      only watch the path if it is a directory
    IN_DONT_FOLLOW:  don't follow a sym link
    IN_EXCL_UNLINK:  exclude events on unlinked objects
    IN_MASK_ADD:     add to the mask of an already existing watch
    IN_ISDIR:        event occurred against dir
    IN_ONESHOT:      only send event once
    
    Returns:
    ---------
    int: A watch descriptor that can be passed to inotify_rm_watch
    
    Exceptions:
    ------------
    ValueError:
    * No valid events in the event mask
    * fd is not an inotify file descriptor
    OSError:
    * fd is not a valid file descriptor
    * Process has no access to specified file
    * File/Folder specified does not exist
    * Maximum number of watches hit
    MemoryError:
    * Raised if the kernel cannot allocate sufficent resources to handle the watch (eg kernel memory)
    """
    if hasattr(fd, "fileno"):
        fd = fd.fileno()
    assert isinstance(fd, int), "fd must by an integer"
    assert isinstance(path, basestring), "path is not a string"
    assert isinstance(mask, int), "mask must be an integer"
    
    wd = _C.inotify_add_watch(fd, path, mask)

    if wd < 0:
        err = _ffi.errno
        if err == _errno.EINVAL:
            raise ValueError("The event mask contains no valid events; or fd is not an inotify file descriptor")
        elif err == _errno.EACCES:
            raise OSError("You do not have permission to read the specified path")
        elif err == _errno.EBADF:
            raise OSError("fd is not a valid file descriptor")
        elif err == _errno.EFAULT:
            raise OSError("path points to a file/folder outside the processes accessible address space")
        elif err == _errno.ENOENT:
            raise OSError("File/Folder pointed to by path does not exist")
        elif err == _errno.ENOSPC:
            raise OSError("Maximum number of watches hit or insufficent kernel resources")
        elif err == _errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory avalible")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))
            
    return wd
    
def inotify_rm_watch(fd, wd):
    """Stop watching a path for events
    
    Arguments:
    -----------
    fd: The inotify file descriptor to remove the watch from
    wd: The Watch to be removed
    
    Returns:
    ---------
    None
    
    Exceptions:
    ------------
    ValueError: Returned if supplied watch is not valid or if the file descriptor is not an inotify file descriptor
    OSError: File descriptor is invalid
    """
    ret = _C.inotify_rm_watch(fd, wd)

    if ret < 0:
        err = _ffi.errno
        if err == _errno.EINVAL:
            raise ValueError("wd is invalid or fd is not an inotify File Descriptor")
        elif err == _errno.EBADF:
            raise OSError("fd is not a valid file descriptor")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))


def str_to_events(str):
    event_struct_size = _ffi.sizeof('struct inotify_event')

    events = []

    str_buf = _ffi.new('char[]', len(str))
    str_buf[0:len(str)] = str

    i = 0
    while i < len(str_buf):
        event = _ffi.cast('struct inotify_event *', str_buf[i:i+event_struct_size])

        filename_start = i + event_struct_size
        filename_end = filename_start + event.len
        filename = _ffi.string(str_buf[filename_start:filename_end])
        
        events.append(InotifyEvent(event.wd, event.mask, event.cookie, filename))
        
        i += event_struct_size + event.len

    return events


class Inotify(object):
    _closed = True
    _fileno = None
    blocking = True
    def __init__(self, flags=0):
        fd = inotify_init(flags)
        self._closed = True
        self._fileno = fd
        
        self._events = []

        if flags & IN_NONBLOCK:
            self.blocking = false
        
    def watch(self, path, events):
        wd = inotify_add_watch(self._fileno, path, events)
        
        return wd
        
    def del_watch(self, wd):
        inotify_rm_watch(self._fileno, wd)
        
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
        return "<inotify fd:{}>".format(self._fileno)
        
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
        return '<Inotify fd={}>'.format(self._fileno)

    def __iter__(self):
        while True:
            yield self.read_event()

InotifyEvent = namedtuple("InotifyEvent", "wd mask cookie filename")

# Provide a nice ID to NAME mapping for debugging
signal_name = {}
# Make the inotify flags more easily accessible by hoisting them out of the _C object
l = locals()
for key, value in _C.__dict__.iteritems():
    if key.startswith("IN_"):
        signal_name[value] = key
        l[key] = value
# <_<
# >_>
# -_- <(This never happened, what you just saw was light reflecting off Venus)
del l
del key, value # python 2.x has vars escape from the scope of the loop, clean this up

def main():
    import sys
    import os
    
    dir = (sys.argv + ["/tmp"])[1]
    
    notifier = Inotify()
    notifier.watch(dir, IN_ALL_EVENTS)
    
    print "Watching {} for file changes".format(dir)
    
    for event in notifier:
        print 'The following file has been modified: "{}" mask=0x{:04X} cookie={}'.format(
                    os.path.join(dir, event.filename), event.mask, event.cookie)

if __name__ == "__main__":
    main()
