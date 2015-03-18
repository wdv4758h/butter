#!/usr/bin/env python
"""splice: wrapper around the splice() syscall"""

from __future__ import print_function

from cffi import FFI as _FFI
import errno as _errno

_ffi = _FFI()
_ffi.cdef("""
#define SPLICE_F_MOVE     ... /* This is a noop in modern kernels and is left here for compatibility */
#define SPLICE_F_NONBLOCK ... /* Make splice operations Non blocking (as long as the fd's are non blocking) */
#define SPLICE_F_MORE     ... /* After splice() more data will be sent, this is a hint to add TCP_CORK like buffering */
#define SPLICE_F_GIFT     ... /* unused for splice() (vmsplice compatibility) */

#define IOV_MAX ... /* Maximum ammount of vectors that can be written by vmsplice in one go */

struct iovec {
    void *iov_base; /* Starting address */
    size_t iov_len; /* Number of bytes */
};

ssize_t splice(int fd_in, signed long long *off_in, int fd_out, signed long long *off_out, size_t len, unsigned int flags);
ssize_t tee(int fd_in, int fd_out, size_t len, unsigned int flags);
ssize_t vmsplice(int fd, const struct iovec *iov, unsigned long nr_segs, unsigned int flags);

char * convert_str_to_void(char * buf);
""")

_C = _ffi.verify("""
#include <limits.h> /* used to define IOV_MAX */
#include <fcntl.h>
#include <sys/uio.h>

/* Its really hard in cffi to convert a python string to a char * WITHOUT using a function
   so instead lets just make a dummy function and use that. while we are at it, lets do
   the conversion to a void pointer as well so we dont need to much with types
*/
void * convert_str_to_void(char * buf){
    /* Take a string and convert it over to a void pointer */
    /* While simple, this is a work around for the cffi lib in python */
    return (void *)buf;
};
""", libraries=[], ext_package="butter")

def splice(fd_in, fd_out, in_offset=0, out_offset=0, len=0, flags=0):
    """Take data from fd_in and pass it to fd_out without going through userspace
    
    Arguments
    ----------
    :param file fd_in: File object or fd to splice from
    :param file fd_out: File object or fd to splice to
    :param int in_offset: Offset inside fd_in to read from
    :param int out_offset: Offset inside fd_out to write to
    :param int len: Ammount of data to transfer
    :param int flags: Flags to specify extra options
    
    Flags
    ------
    SPLICE_F_MOVE: This is a noop in modern kernels and is left here for compatibility
    SPLICE_F_NONBLOCK: Make splice operations Non blocking (as long as the fd's are non blocking)
    SPLICE_F_MORE: After splice() more data will be sent, this is a hint to add TCP_CORK like buffering
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
    :raises OSError: No writers waiting on fd_in
    :raises OSError: one or both fd's are in blocking mode and SPLICE_F_NONBLOCK specified
    """
    fd_in = getattr(fd_in, 'fileno', lambda: fd_in)()
    fd_out = getattr(fd_out, 'fileno', lambda: fd_out)()
    
    in_offset = _ffi.cast("long long *", in_offset)
    out_offset = _ffi.cast("long long *", out_offset)

    size = _C.splice(fd_in, in_offset, fd_out, out_offset, len, flags)
    
    if size < 0:
        err = _ffi.errno
        if err == _errno.EINVAL:
            if in_offset or out_offset:
                raise ValueError("fds may not be seekable")
            else:
                raise ValueError("Target filesystem does not support slicing or file may be in append mode")
        elif err == _errno.EBADF:
            raise OSError("fds are invalid or incorrect mode for file")
        elif err == _errno.EPIPE:
            raise OSError("offset specified but one of the fds is a pipe")
        elif err == _errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory available")
        elif err == _errno.EAGAIN:
            raise OSError("No writers on fd_in or a fd is open in BLOCKING mode and NON_BLOCK specified to splice()")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))

    return size


def tee(fd_in, fd_out, len=0, flags=0):
    """Splice data like the :py:func:`.splice` but also leave a copy of the data in the original fd's buffers
    
    Arguments
    ----------
    :param file fd_in: File object or fd to splice from
    :param file fd_out: File object or fd to splice to
    :param int len: Ammount of data to transfer
    :param int flags: Flags to specify extra options
    
    Flags
    ------
    SPLICE_F_MOVE: This is a noop in modern kernels and is left here for compatibility
    SPLICE_F_NONBLOCK: Make tee operations Non blocking (as long as the fd's are non blocking)
    SPLICE_F_MORE: unused for tee()
    SPLICE_F_GIFT: unused for tee() (:py:func:`.vmsplice` compatibility)
    
    Returns
    --------
    :return: Number of bytes written
    :rtype: int
    
    Exceptions
    -----------
    :raises ValueError: One of the file descriptors is not a pipe
    :raises ValueError: Both file descriptors refer to the same pipe
    :raises MemoryError: Insufficient kernel memory
    """
    fd_in = getattr(fd_in, 'fileno', lambda: fd_in)()
    fd_out = getattr(fd_out, 'fileno', lambda: fd_out)()
    
    size = _C.tee(fd_in, fd_out, len, flags)
    
    if size < 0:
        err = _ffi.errno
        if err == _errno.EINVAL:
            raise ValueError("fd_in or fd_out are not a pipe or refer to the same pipe")
        elif err == _errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory available")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))

    return size


def vmsplice(fd, vec, flags=0):
    """Write a list strings or byte buffers to the specified fd
    
    Arguments
    ----------
    :param file fd: File object or fd to write to
    :param list vec: A list of strings to write to the pipe
    :param int flags: Flags to specify extra options
    
    Flags
    ------
    SPLICE_F_MOVE: This is a noop in modern kernels and is left here for compatibility
    SPLICE_F_NONBLOCK: Make vmsplice operations Non blocking (as long as the fd is non blocking)
    SPLICE_F_MORE: unused for vmsplice()
    SPLICE_F_GIFT: Pass ownership of the pages to the kernel. You must not modify data in place
                   if using this option as the pages now belong to the kernel and bad things (tm)
                   will happen
                   if used, pages must be page alighned in both length and position
    Returns
    --------
    :return: Number of bytes written
    :rtype: int
    
    Exceptions
    -----------
    :raises ValueError: One of the file descriptors is not a pipe
    :raises ValueError: Both file descriptors refer to the same pipe
    :raises MemoryError: Insufficient kernel memory
    """
    fd = getattr(fd, 'fileno', lambda: fd)()
    n_vec =_ffi.new('struct iovec[]', len(vec))
    for str, v in zip(vec, n_vec) :
        v.iov_base = _C.convert_str_to_void(str)
        v.iov_len = len(str)
    
    size = _C.vmsplice(fd, n_vec, len(vec), flags)

    if size < 0:
        err = _ffi.errno
        if err == _errno.EBADF:
            raise ValueError("fd is not valid or does not refer to a pipe")
        if err == _errno.EINVAL:
            raise ValueError("nr_segs is 0 or greater than IOV_MAX; or memory not aligned if SPLICE_F_GIFT set")
        elif err == _errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory available")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))

    return size


SPLICE_F_MOVE = _C.SPLICE_F_MOVE    
SPLICE_F_NONBLOCK = _C.SPLICE_F_NONBLOCK
SPLICE_F_MORE = _C.SPLICE_F_MORE    
SPLICE_F_GIFT = _C.SPLICE_F_GIFT    

IOV_MAX = _C.IOV_MAX
