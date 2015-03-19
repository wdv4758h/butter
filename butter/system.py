#!/usr/bin/env python
"""system: syscalls for system managment

This module includes a number of helpful functions for managing and maintaing 
a system. These were orignially created to support a Linux contaienrs solution 
written in python but may be genrally useful and have been broken off and 
intergrarated into butter in this module


* mount: Mount filesystems using the `man 2 mount` syscall (simmilar to 
         /sbin/mount)
* umount: Unmount filesystems in the system
* pivot_root: Exchange the filesystem at 'new' with '/' and mount the old 
              filesystem at 'old'
* sethostname: Set the hostname of the system
* gethostname: Retrvie the current system hostname (identical to 
              :py:func:`socket.gethostname`)
* getpid: Call the syscall `getpid` directly, bypassing glibc and any caching 
          it performs
* getppid: Call the syscall `getppid` directly, bypassing glibc and any caching 
           it performs
"""

from __future__ import print_function

from .utils import PermissionError, InternalError, UnknownError
from os.path import isdir as _isdir
from cffi import FFI as _FFI
import errno as _errno

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
""", libraries=[], ext_package="butter")

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

class Retry(Exception):
    """Filesystem now marked as expired"""


def mount(src, target, fs, flags=0, data=""):
    """Mount the specified filesystem at `target`

    Arguments
    ----------
    :param str src: Filesystem dependent string specifing the source of the mount
                    eg for nfs this would be <ip>:/remote/path or a block device 
                    dev for a normal filesystem
    :param str target: The path to mount the filesystem on
    :param str fs: The type of filesystem to mount on `target`
    :param int flags: Extra conditions on the mount (see flags below)
    :param str data: Additinal data to pass to the filesystem driver

    Flags
    ------
    :py:const:`MS_BIND`: Make mount a bind mount, `fs` is ignored with this option
    :py:const:`MS_DIRSYNC`: Perform all directory operations synchronously
    :py:const:`MS_MANDLOCK`: Enable Mandatory locking for the filesystem
    :py:const:`MS_MOVE`: Move a mountpoint to a new location atomically without unmounting
    :py:const:`MS_NOATIME`: Dont update atime on file access
    :py:const:`MS_NODEV`: Prevent device nodes from ebing created on the filesystem
    :py:const:`MS_NODIRATIME`: Dont update Directory atime on file access
    :py:const:`MS_NOEXEC`: Prevent files from being exected on the filesystem via `exec()`
    :py:const:`MS_NOSUID`: Disable SUID flag on files in this filesystem
    :py:const:`MS_RDONLY`: Mount filesystem Read Only
    :py:const:`MS_RELATIME`: only update atime if ctime or mtime have been updated
    :py:const:`MS_REMOUNT`: Remount the filesystem in place
    :py:const:`MS_SILENT`: Disable printing messages to dmesg for the mount
    :py:const:`MS_STRICTATIME`: Always update atime on file access
    :py:const:`MS_SYNCHRONOUS`: Mount the filesystem in synchronous mode (same as passing 
                                O_SYNC to :py:func:`os.open()`

    Returns
    --------
    No return value

    Exceptions
    -----------
    :raises ValueError: Attempt to mount a Read only filesystem without specifing MS_RDONLY as a flag
    :raises ValueError: `src` or `target` contain a component that does not exist or was not searchable
    :raises ValueError: `src` is already mounted
    :raises ValueError: Filesystem cannot be mounted read only as it still holds files open for writing
    :raises ValueError: Target is busy (it is the working directory of some thread, the mount point of another device, has open files, etc.)
    :raises OSError: `src` has an invalid superblock
    :raises OSError: MS_REMOUNT was attempted but `src` is not mounted on `target`
    :raises OSError: MS_MOVE attempted but `src` is not a mount point or is '/'
    :raises OSError: Filesystem not available in the kernel
    :raises ValueError: Too many links encountered during pathname resolution
    :raises ValueError: MS_MOVE attempted while `target` is a descendent of `src`
    :raises ValueError: `src` or `target` longer than MAXPATHLEN
    :raises ValueError: `src` or `target` contains an empty or non existent component
    :raises ValueError: `src` is nto a valid block device and a block device is required by this filesystem
    :raises ValueError: `target` or prefix of `src` is nto a directory
    :raises OSError: The major number of `src` is out of the range for valid block devices
    :raises MemoryError: Kernel could not allocate enough memory to handle the request
    :raises PermissionError: No permission to mount filesystem
    """
    assert 0 < len(src) < MAXPATHLEN, "src is too long in length"
    assert 0 < len(target) < MAXPATHLEN, "target is too long in length"
    
    assert isinstance(src,    (str, bytes)), "src must be a string"
    assert isinstance(target, (str, bytes)), "target must be a string"
    assert isinstance(fs,     (str, bytes)), "fs must be a string"
    assert isinstance(flags,   int        ), "flags must be a integer"
    assert isinstance(data,   (str, bytes)), "data must be a string"

    if isinstance(src, str):
        src = src.encode()

    if isinstance(target, str):
        target = target.encode()

    if isinstance(fs, str):
        fs = fs.encode()

    if isinstance(data, str):
        data = data.encode()
    
    err = _C.mount(src, target, fs, flags, data)

    if err < 0:
        err = _ffi.errno
        if err == _errno.EACCES:
            raise PermissionError("A component of a path was not searchable. (See also path_resolution(7).) Or, mounting a read-only filesystem was attempted without giving the MS_RDONLYflag. Or, the block device source is located on a filesystem mounted with the MS_NODEV option")
        elif err == _errno.EBUSY:
            raise ValueError("source is already mounted. Or, it cannot be remounted read-only, because it still holds files open for writing. Or, it cannot be mounted on target because target is still busy (it is the working directory of some thread, the mount point of another device, has open files, etc.)")
        elif err == _errno.EFAULT:
            # In practice this should not be raised as it means this lib has passed in invalid 
            # data, this is a bug so report it if you can
            raise ValueError("One of the pointer arguments points outside the user address space")
        elif err == _errno.EINVAL:
            raise ValueError("source had an invalid superblock. Or, a remount (MS_REMOUNT) was attempted, but source was not already mounted on target. Or, a move (MS_MOVE) was attempted, but source was not a mount point, or was '/'")
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
            raise MemoryError("The kernel could not allocate a free page to copy filenames or data into")
        elif err == _errno.ENOTBLK:
            raise ValueError("source is not a block device and a device was required")
        elif err == _errno.ENOTDIR:
            raise ValueError("target, or a prefix of source, is not a directory")
        elif err == _errno.ENXIO:
            raise OSError("The major number of the block device source is out of range")
        elif err == _errno.EPERM:
            raise PermissionError("Permission denied, CAP_SYS_ADMIN not in capability bits")
        else:
            # If you are here, its a bug. send us the traceback
            raise UnknownError(err)


def umount(target, flags=0):
    """Unmount the specified filesystem

    Arguments
    ----------
    :param str target: The path to the filesystem to unmount
    :param int flags: Extra options to use to unmount the filesystem

    Flags
    ------
    :py:const:`MNT_FORCE`: Forcibly detach the filesystem, even if busy (NFS only)
    :py:const:`MNT_DETACH`: Lazily detach the filesystem (filesystem will be detached
                            when there are no more consumers of the filesystem). This
                            will cause the mount to appear unmounted to processes that
                            are not using the detached mount point
    :py:const:`MNT_EXPIRE`: Mark the mountpoint as expired and trigger an EAGAIN. any
                            access by a program will mark the filesystem as active
                            again. if a filesystem is marked as expired, then another
                            umount call will unmount the filesystem normmaly
    :py:const:`UMOUNT_NOFOLLOW`: Do not derefrence any symlinks when unmounting the 
                                 filesystem

    Returns
    --------
    No return value

    Exceptions
    -----------
    :raises Retry: Filesystem now marked as expired, call again to unmount
    :raises ValueError: Could not unount filesystema s it is currently in use
    :raises OSError: Target is not a mount point
    :raises OSError: umount called with MNT_EXPIRE and ethier MNT_DETACH or MNT_FORCE
    :raises ValueError: Supplied path is too long
    :raises ValueError: Supplied path has an empty or non-existent component
    :raises MemoryError: Kernel could not allocate enough memory to handle the request
    :raises PermissionError: No permission to pivot_root to new location
    """
    assert 0 < len(target) < MAXPATHLEN, "target is too long in length"

    assert isinstance(target, (str, bytes)), "target must be a string"
    assert isinstance(flags, int), "flags must be a integer"

    if isinstance(target, str):
        target = target.encode()

    err = _C.umount2(target, flags)

    if err < 0:
        err = _ffi.errno
        if err == _errno.EAGAIN:
            raise Retry("Filesystem marked as expired, call again to unmount filesystem")
        elif err == _errno.EBUSY:
            raise ValueError("target could not be unmounted because it is busy")
        elif err == _errno.EFAULT:
            raise ValueError("target points outside the user address space")
        elif err == _errno.EINVAL:
            raise ValueError("target is not a mount point. Or, umount2() was called with MNT_EXPIRE and either MNT_DETACH or MNT_FORCE")
        elif err == _errno.ENAMETOOLONG:
            raise ValueError("A pathname was longer than MAXPATHLEN")
        elif err == _errno.ENOENT:
            raise ValueError("A pathname was empty or had a nonexistent component")
        elif err == _errno.ENOMEM:
            raise MemoryError("The kernel could not allocate a free page to copy filenames or data into")
        elif err == _errno.EPERM:
            raise PermissionError("Permission denied, CAP_SYS_ADMIN not in capability bits")
        else:
            # If you are here, its a bug. send us the traceback
            raise UnknownError(err)


def pivot_root(new, old):
    """Move the filesystem specfied by `new` and mount it at '/' and move the old '/' to `old`

    Arguments
    ----------
    :param str new: Path to a mounted filesystem to make the new '/'
    :param str old: Location where current '/' should be mounted

    Returns
    --------
    No return value

    Exceptions
    -----------
    :raises ValueError: `new` or `old` does not refer to a directory
    :raises ValueError: `new` or `old` are on the current root filesystem or filesystem already mounted on `old`
    :raises ValueError: `old` is not a folder underneath `new`
    :raises PermissionError: No permission to pivot_root to new location
    """
    assert len(new) > 0
    assert len(old) > 0

    assert isinstance(new, (str, bytes)), "new must be a string"
    assert isinstance(old, (str, bytes)), "old must be a string"

    if isinstance(new, str):
        new = new.encode()

    if isinstance(old, str):
        old = old.encode()

    err = _C.pivot_root(new, old)

    if err < 0:
        err = _ffi.errno
        if err == _errno.EINVAL:
            raise ValueError("{} is not a sub-directory of {}".format(old, new))
        elif err == _errno.EBUSY:
            raise ValueError("old or new are on the current root filesystem or filesystem already mounted on {}".format(old))
        elif err == _errno.ENOTDIR:
            if _isdir(new):
                raise ValueError("{} is not a Directory".format(new))
            elif _isdir(old):
                raise ValueError("{} is not a Directory".format(old))
            else:
                # this is a bug but testing for this case just in case, let us know if you
                # hit it
                raise ValueError("old or new is not a dir but could not work out which one")
        elif err == _errno.EPERM:
            raise PermissionError("Permission denied, CAP_SYS_ADMIN not in capability bits")
        else:
            # If you are here, its a bug. send us the traceback
            raise UnknownError(err)


def sethostname(hostname):
    """Set the hostname for they system

    Arguments
    ----------
    :param str hostname: The hostname to set

    Returns
    --------
    No return value

    Exceptions
    -----------
    :raises ValueError: Hostname too long
    :raises PermissionError: No permission to set hostname
    """
    assert len(hostname) < HOST_NAME_MAX, "Specified hostname too long"

    assert isinstance(hostname, (str, bytes)), "Hostname must be a string"

    if isinstance(hostname, str):
        hostname = hostname.encode()

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
        elif err == _errno.EPERM:
            raise PermissionError("Permission denied, CAP_SYS_ADMIN not in capability bits")
        else:
            # If you are here, its a bug. send us the traceback
            raise UnknownError(err)

def gethostname():
    """Retrive the specified hostname of the system

    Returns
    --------
    :return: The hostname of the system
    :rtype: str
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
            # this is internal and is a bug in out code if reached
            # we allocated HOST_NAME_MAX for the length above so this should
            # be impossible to hit, using InternalError rather than ValueError as the
            # caller of this code did not provide an incorrect value but instead
            # the platform/OS provided an invalid value
            raise InternalError("Supplied buffer not long enough")
        elif err == _errno.EPERM:
            raise PermissionError("Permission denied, CAP_SYS_ADMIN not in capability bits")
        else:
            # If you are here, its a bug. send us the traceback
            raise UnknownError(err)
    
    hostname = _ffi.string(hostname, HOST_NAME_MAX)

    return hostname
