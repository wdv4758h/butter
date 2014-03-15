#!/usr/bin/env python
"""system: syscalls for system managment"""

from __future__ import print_function

from cffi import FFI as _FFI
import errno as _errno
from os.path import isdir as _isdir

_ffi = _FFI()
_ffi.cdef("""
# define MS_BIND ...
# define MS_DIRSYNC ...
# define MS_MANDLOCK ...
# define MS_MOVE ...
# define MS_NOATIME ...
# define MS_NODEV ...
# define MS_NODIRATIME ...
# define MS_NOEXEC ...
# define MS_NOSUID ...
# define MS_RDONLY ...
# define MS_RELATIME ...
# define MS_REMOUNT ...
# define MS_SILENT ...
# define MS_STRICTATIME ...
# define MS_SYNCHRONOUS ...

# define MNT_FORCE ...
# define MNT_DETACH ...
# define MNT_EXPIRE ...
# define UMOUNT_NOFOLLOW ...

# define HOST_NAME_MAX ...

int mount(const char *source, const char *target,
          const char *filesystemtype, unsigned long mountflags,
          const void *data);
int umount2(const char *target, int flags);
extern int pivot_root(const char * new_root, const char * put_old);

int gethostname(char *name, size_t len);
int sethostname(const char *name, size_t len);

// Muck with the types so cffi understands it
// normmaly pid_t (defined as int32_t in
// /usr/include/arm-linux-gnueabihf/bits/typesizes.h
int32_t getpid(void);
int32_t getppid(void);
""")

_C = _ffi.verify("""  
//#include <sched.h>
#include <sys/mount.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/syscall.h>
#include <sys/mount.h>

int32_t getpid(void){
    return syscall(SYS_getpid);
};

int32_t getppid(void){
    return syscall(SYS_getppid);
};
""", libraries=[])

MS_BIND = _C.MS_BIND
MS_DIRSYNC = _C.MS_DIRSYNC
MS_MANDLOCK = _C.MS_MANDLOCK
MS_MOVE = _C.MS_MOVE
MS_NOATIME = _C.MS_NOATIME
MS_NODEV = _C.MS_NODEV
MS_NODIRATIME = _C.MS_NODIRATIME
MS_NOEXEC = _C.MS_NOEXEC
MS_NOSUID = _C.MS_NOSUID
MS_RDONLY = _C.MS_RDONLY
MS_RELATIME = _C.MS_RELATIME
MS_REMOUNT = _C.MS_REMOUNT
MS_SILENT = _C.MS_SILENT
MS_STRICTATIME = _C.MS_STRICTATIME
MS_SYNCHRONOUS = _C.MS_SYNCHRONOUS

HOST_NAME_MAX = _C.HOST_NAME_MAX

# seems reasonable
MAXPATHLEN = 256

getpid = _C.getpid
getppid = _C.getppid


def mount(src, target, fs, flags=0, data=""):
    """Take data from fd_in and pass it to fd_out without going through userspace

    Arguments
    ----------
    :param file fd_in: File object or fd to splice from

    Flags
    ------
    SPLICE_F_GIFT: unused for splice() (vmsplice compatibility)

    Returns
    --------
    :return: Number of bytes written
    :rtype: int

    Exceptions
    -----------
    :raises ValueError: One of the file descriptors is unseekable
    :raises ValueError: Neither descriptor refers to a pipe
    """
    assert 0 < len(src) < MAXPATHLEN, "src is too long in length"
    assert 0 < len(target) < MAXPATHLEN, "target is too long in length"
    
    err = _C.mount(src, target, fs, flags, data)

    if err < 0:
        err = _ffi.errno
        if err == _errno.EACCES:
            raise ValueError("A component of a path was not searchable. (See also path_resolution(7).) Or, mounting a read-only filesystem was attempted without giving the MS_RDONLYflag. Or, the block device source is located on a filesystem mounted with the MS_NODEV option")
        elif err == _errno.EBUSY:
            raise ValueError("source is already mounted. Or, it cannot be remounted read-only, because it still holds files open for writing. Or, it cannot be mounted on target because target is still busy (it is the working directory of some thread, the mount point of another device, has open files, etc.)")
        elif err == _errno.EFAULT:
            # In practice this should not be raised as it means this lib has passed in invalid 
            # data, this is a bug so report it if you can
            raise ValueError("One of the pointer arguments points outside the user address space")
        elif err == _errno.EINVAL:
            raise OSError("source had an invalid superblock. Or, a remount (MS_REMOUNT) was attempted, but source was not already mounted on target. Or, a move (MS_MOVE) was attempted, but source was not a mount point, or was '/'")
        elif err == _errno.ELOOP:
            raise ValueError("Too many links encountered during pathname resolution. Or, a move was attempted, while target is a descendant of source")
        elif err == _errno.EMFILE:
            raise OSError("Table of dummy devices is full")
        elif err == _errno.ENAMETOOLONG:
            # This is checked in the assert above but check for it and report it corectly anyway
            raise ValueError("A pathname was longer than MAXPATHLEN ({})".format(MAXPATHLEN))
        elif err == _errno.ENODEV:
            raise OSError("filesystemtype not configured in the kernel")
        elif err == _errno.ENOENT:
            raise ValueError("A pathname was empty or had a nonexistent component")
        elif err == _errno.ENOMEM:
            raise MemError("The kernel could not allocate a free page to copy filenames or data into")
        elif err == _errno.ENOTBLK:
            raise ValueError("source is not a block device and a device was required")
        elif err == _errno.ENOTDIR:
            raise ValueError("target, or a prefix of source, is not a directory")
        elif err == _errno.ENXIO:
            raise IOError("The major number of the block device source is out of range")
        elif err == _errno.EPERM:
            raise OSError("Permission denied, SYS_CAP_ADMIN not in capability bits")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))


def umount(target, flags=0):
    """Take data from fd_in and pass it to fd_out without going through userspace

    Arguments
    ----------
    :param file fd_in: File object or fd to splice from

    Flags
    ------
    SPLICE_F_GIFT: unused for splice() (vmsplice compatibility)

    Returns
    --------
    :return: Number of bytes written
    :rtype: int

    Exceptions
    -----------
    :raises ValueError: One of the file descriptors is unseekable
    :raises ValueError: Neither descriptor refers to a pipe
    :raises ValueError: Target filesystem does not support splicing
    :raises OSError: supplied fd does not refer to a file
    :raises OSError: Incorrect mode for file
    :raises MemoryError: Insufficient kernel memory
    :raises IOError: No writers waiting on fd_in
    :raises IOError: one or both fd's are in blocking mode and SPLICE_F_NONBLOCK specified
    """
    assert 0 < len(target) < MAXPATHLEN, "target is too long in length"

    err = _C.umount2(target, flags)

    if err < 0:
        err = _ffi.errno
        if err == _errno.EAGAIN:
            raise ValueError("A call to umount2() specifying MNT_EXPIRE successfully marked an unbusy filesystem as expired")
        elif err == _errno.EBUSY:
            raise ValueError("target could not be unmounted because it is busy")
        elif err == _errno.EFAULT:
            raise ValueError("target points outside the user address space")
        elif err == _errno.EINVAL:
            raise OSError("target is not a mount point. Or, umount2() was called with MNT_EXPIRE and either MNT_DETACH or MNT_FORCE")
        elif err == _errno.ENAMETOOLONG:
            raise ValueError("A pathname was longer than MAXPATHLEN")
        elif err == _errno.ENOENT:
            raise ValueError("A pathname was empty or had a nonexistent component")
        elif err == _errno.ENOMEM:
            raise MemError("The kernel could not allocate a free page to copy filenames or data into")
        elif err == _errno.EPERM:
            raise OSError("Permission denied, SYS_CAP_ADMIN not in capability bits")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))


def pivot_root(new, old):
    """Take data from fd_in and pass it to fd_out without going through userspace

    Arguments
    ----------
    :param file fd_in: File object or fd to splice from

    Flags
    ------
    SPLICE_F_GIFT: unused for splice() (vmsplice compatibility)

    Returns
    --------
    :return: Number of bytes written
    :rtype: int

    Exceptions
    -----------
    :raises ValueError: One of the file descriptors is unseekable
    :raises ValueError: Neither descriptor refers to a pipe
    :raises ValueError: Target filesystem does not support splicing
    :raises OSError: supplied fd does not refer to a file
    :raises OSError: Incorrect mode for file
    :raises MemoryError: Insufficient kernel memory
    :raises IOError: No writers waiting on fd_in
    :raises IOError: one or both fd's are in blocking mode and SPLICE_F_NONBLOCK specified
    """
    assert len(new) > 0
    assert len(old) > 0

    err = _C.pivot_root(new, old)

    if err < 0:
        err = _ffi.errno
        if err == _errno.EINVAL:
            raise ValueError("{} does not refer to a directory under {}".format(old, new))
        elif err == _errno.EBUSY:
            raise ValueError("old or new are on the current root filesystem or filesystem already mounted on {}".format(old))
        elif err == _errno.ENOTDIR:
            if _isdir(new):
                raise OSError("{} is not a Directory".format(new))
            elif _isdir(old):
                raise OSError("{} is not a Directory".format(old))
            else:
                # this is a bug but testing for this case just in case, let us know if you
                # hit it
                raise OSError("old or new is not a dir but could not work out which one")
        elif err == _errno.EPERM:
            raise OSError("Permission denied, SYS_CAP_ADMIN not in capability bits")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))


def sethostname(hostname):
    """Take data from fd_in and pass it to fd_out without going through userspace

    Arguments
    ----------
    :param file fd_in: File object or fd to splice from

    Flags
    ------
    SPLICE_F_GIFT: unused for splice() (vmsplice compatibility)

    Returns
    --------
    :return: Number of bytes written
    :rtype: int

    Exceptions
    -----------
    :raises ValueError: One of the file descriptors is unseekable
    :raises ValueError: Neither descriptor refers to a pipe
    :raises ValueError: Target filesystem does not support splicing
    :raises OSError: supplied fd does not refer to a file
    :raises OSError: Incorrect mode for file
    :raises MemoryError: Insufficient kernel memory
    :raises IOError: No writers waiting on fd_in
    :raises IOError: one or both fd's are in blocking mode and SPLICE_F_NONBLOCK specified
    """
    assert len(hostname) < HOST_NAME_MAX, "Specified hostname too long"

    err = _C.sethostname(hostname, len(hostname))

    if err < 0:
        err = _ffi.errno
        if err == _errno.EFAULT:
            # in practice this should never be raised as it means this function is broken
            raise ValueError("Name is an invalid address")
        elif err == _errno.EINVAL:
            # same as above, we check values and supply the right ones but just in case we 
            # handle the error case
            raise ValueError("length is negative or hostname is longer than allowed value")
        elif err == _errno.ENAMETOOLONG:
            # great, for some reason we did not allocate a long enough buffer
            raise OSError("Supplied buffer not long enough")
        elif err == _errno.EPERM:
            raise OSError("Permission denied, SYS_CAP_ADMIN not in capability bits")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))

def gethostname():
    """Take data from fd_in and pass it to fd_out without going through userspace

    Arguments
    ----------
    :param file fd_in: File object or fd to splice from

    Flags
    ------
    SPLICE_F_GIFT: unused for splice() (vmsplice compatibility)

    Returns
    --------
    :return: Number of bytes written
    :rtype: int

    Exceptions
    -----------
    :raises ValueError: One of the file descriptors is unseekable
    :raises ValueError: Neither descriptor refers to a pipe
    :raises ValueError: Target filesystem does not support splicing
    :raises OSError: supplied fd does not refer to a file
    :raises OSError: Incorrect mode for file
    :raises MemoryError: Insufficient kernel memory
    :raises IOError: No writers waiting on fd_in
    :raises IOError: one or both fd's are in blocking mode and SPLICE_F_NONBLOCK specified
    """
    hostname = _ffi.new('char[]', HOST_NAME_MAX)
    err = _C.gethostname(hostname, len(hostname))

    if err < 0:
        err = _ffi.errno
        if err == _errno.EFAULT:
            # in practice this should never be raised as it means this function is broken
            raise ValueError("Name is an invalid address")
        elif err == _errno.EINVAL:
            # same as above, we check values and supply the right ones but just in case we 
            # handle the error case
            raise ValueError("length is negative or hostname is longer than allowed value")
        elif err == _errno.ENAMETOOLONG:
            # great, for some reason we did not allocate a long enough buffer
            raise OSError("Supplied buffer not long enough")
        elif err == _errno.EPERM:
            raise OSError("Permission denied, SYS_CAP_ADMIN not in capability bits")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))
    
    hostname = _ffi.string(hostname, HOST_NAME_MAX)

    return hostname
    

def main():
    import os
    
    path = "/tmp/test"
    print("Mounting temp filesystem at {}".format(path))
    try:
        os.mkdir(path)
    except OSError:
        pass
    mount('tmpfs-testing', path, 'tmpfs')
    
    #print("Pivoting to temp filesystem")
    #pivot_root('/tmp', '/tmp')
    
    print("Unmounting temp filesystem")
    umount(path)
    
    hostname = gethostname()
    print("Old Hostname:", hostname)
    try:
        sethostname('dsadsa')
    except OSError:
        print("Error: Could not set hostname")
    print("New Hostname:", gethostname())
    print("Resorting old hostname")
    try:
        sethostname(hostname)
    except OSError:
        print("Error: Could not restore hostname")
    
    print()
    
    print("{}".format("Syscall PID:"), getpid())
    print("os PID: ", os.getpid())
    print("Syscall PPID: ", _C.getppid())
    print("os PPID: ", os.getppid())

if __name__ == "__main__":
    main()
