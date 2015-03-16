#!/usr/bin/env python
"""inotify: Wrapper around the inotify syscalls providing both a function based and file like interface"""

from collections import namedtuple
from cffi import FFI
import errno


ffi = FFI()
ffi.cdef("""
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
//        char          name[0]; # we calculate this manually in str_to_event
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

C = ffi.verify("""
#include <sys/inotify.h>
#include <sys/ioctl.h>
""", libraries=[], ext_package="butter")

def inotify_init(flags=0):
    """Initialise an inotify instnace and return a File Descriptor to refrence is
    
    Arguments:
    -----------
    Flags:
    -------
    IN_CLOEXEC: Automatically close the inotify handle on exec()
    IN_NONBLOCK: Place the file descriptor in non blocking mode
    """
    fd = C.inotify_init1(flags)
    
    if fd < 0:
        err = ffi.errno
        if err == errno.EINVAL:
            raise ValueError("Invalid argument or flag")
        elif err == errno.EMFILE:
            raise OSError("Maximum inotify instances reached")
        elif err == errno.ENFILE:
            raise OSError("File descriptor limit hit")
        elif err == errno.ENOMEM:
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
    assert isinstance(path, (str, bytes)), "path is not a string"
    assert isinstance(mask, int), "mask must be an integer"
    
    if isinstance(path, str):
        path = path.encode()
    
    wd = C.inotify_add_watch(fd, path, mask)

    if wd < 0:
        err = ffi.errno
        if err == errno.EINVAL:
            raise ValueError("The event mask contains no valid events; or fd is not an inotify file descriptor")
        elif err == errno.EACCES:
            raise OSError("You do not have permission to read the specified path")
        elif err == errno.EBADF:
            raise OSError("fd is not a valid file descriptor")
        elif err == errno.EFAULT:
            raise OSError("path points to a file/folder outside the processes accessible address space")
        elif err == errno.ENOENT:
            raise OSError("File/Folder pointed to by path does not exist")
        elif err == errno.ENOSPC:
            raise OSError("Maximum number of watches hit or insufficent kernel resources")
        elif err == errno.ENOMEM:
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
    ret = C.inotify_rm_watch(fd, wd)

    if ret < 0:
        err = ffi.errno
        if err == errno.EINVAL:
            raise ValueError("wd is invalid or fd is not an inotify File Descriptor")
        elif err == errno.EBADF:
            raise OSError("fd is not a valid file descriptor")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))


def str_to_events(str):
    event_struct_size = ffi.sizeof('struct inotify_event')

    events = []

    str_buf = ffi.new('char[]', len(str))
    str_buf[0:len(str)] = str

    i = 0
    while i < len(str_buf):
        event = ffi.cast('struct inotify_event *', str_buf[i:i+event_struct_size])

        filename_start = i + event_struct_size
        filename_end = filename_start + event.len
        filename = ffi.string(str_buf[filename_start:filename_end])
        
        events.append(InotifyEvent(event.wd, event.mask, event.cookie, filename))
        
        i += event_struct_size + event.len

    return events


InotifyEvent = namedtuple("InotifyEvent", "wd mask cookie filename")
class InotifyEvent(InotifyEvent):
    __slots__ = []
    @property
    def access_event(self):
        return True if self.mask & IN_ACCESS else False

    @property
    def modify_event(self):
        return True if self.mask & IN_MODIFY else False

    @property
    def attrib_event(self):
        return True if self.mask & IN_ATTRIB else False

    @property
    def close_write_event(self):
        return True if self.mask & IN_CLOSE_WRITE else False

    @property
    def close_nowrite_event(self):
        return True if self.mask & IN_CLOSE_NOWRITE else False

    @property
    def close_event(self):
        return True if self.mask & (IN_CLOSE_NOWRITE|IN_CLOSE_WRITE) else False

    @property
    def open_event(self):
        return True if self.mask & IN_OPEN else False

    @property
    def moved_from_event(self):
        return True if self.mask & IN_MOVED_FROM else False

    @property
    def moved_to_event(self):
        return True if self.mask & IN_MOVED_TO else False

    @property
    def create_event(self):
        return True if self.mask & IN_CREATE else False

    @property
    def delete_event(self):
        return True if self.mask & IN_DELETE else False

    @property
    def delete_self_event(self):
        return True if self.mask & IN_DELETE_SELF else False

    @property
    def move_self_event(self):
        return True if self.mask & IN_MOVE_SELF else False

    @property
    def is_dir_event(self):
        return True if self.mask & IN_ISDIR else False

# update the local namespace with flags and provide
# a handy dict for reversable lookups
event_name = {}
_l = locals()
for key in dir(C):
    if key.startswith('IN_'):
        val = getattr(C, key)
        _l[key] = val
        event_name[key] = val
        event_name[val] = key
