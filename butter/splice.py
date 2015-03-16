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
    :raises IOError: No writers waiting on fd_in
    :raises IOError: one or both fd's are in blocking mode and SPLICE_F_NONBLOCK specified
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


def _main():
    """Simple test to confirm that splice works and can handle short reads
    where we write less than len that we dont block and wait but get the exact
    same data out the other end
    """
    import sys
    import os

    val = 'thisisatest'
    
    fd1_ingress, fd1_egress = os.pipe()
    fd2_ingress, fd2_egress = os.pipe()

    print('writing')
    os.write(fd1_egress, val)

    print('splicing')
    # Make sure we are splicing() more than the buffer of data we have chosen as a 
    # sentinal value to ensure that nothing blocks unexpectly (hard coded magic values
    # lead to chaos)
    splice(fd1_ingress, fd2_egress, flags=SPLICE_F_NONBLOCK, len=len(val)*2)

    print('reading')
    buf = os.read(fd2_ingress, len(val)+5) # this works as pipes can give a short read
    
    print('verifing ("{}" == "{}")'.format(buf, val))
    assert buf == val, 'value transformed through pipe transistion'

    print('all ok')


def _socket_main():
    """Simple example showing how to transfer from socket to socket using a Pipe
    as an intermediate buffer
    
    Things to note:
    * sockets cant be spliced directly (pipe is required)
    * len is more of a hint, splicing may return less than specified
    * splice only transfers whats currently in the buffer, it will not
      wait until len bytes are transferred
    * Data does not get flushed out automatically, hence TCP_NODELAY to
      flush data out
    * :py:func:`.splice` will be called once per packet
    """
    from select import select
    import socket
    import os

    in_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    out_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

    out_pipe, in_pipe = os.pipe()

    in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    in_sock.bind(('::', 8090))
    in_sock.listen(1)
    conn, addr = in_sock.accept()

    print('Accepted connection from {}'.format(addr))
    
    print('Connecting to (::1, 8091)')
    out_sock.connect(('::1', 8091))

    max_segment = 2**24 # chosen arbitrarily
    bytes = True
    
    try:
        while True:
            rd, wr, err = select([conn], [], [conn])
            if err:
                print('Connection error')
                break
                
            print('Splicing')
            bytes = splice(conn, in_pipe, len=max_segment, flags=SPLICE_F_MOVE)
            if bytes == 0:
                break
                
            print("Read {} Bytes".format(bytes))
            bytes = splice(out_pipe, out_sock, len=max_segment)
            out_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_CORK, 0)
            print("Wrote {} Bytes".format(bytes))
    except KeyboardInterrupt:
        pass
        
    print("Exiting")


def _tee_main():
    """An example showing off using tee in production use
    pipes data from stdin to stdout but looks for the magic 'exit' command
    in the stream and exit when it sees it
    
    Known Bugs:
    * Partial reads of 'exit' command where a command may be read partially over
      multiple reads() will not exit correctly
    
    to run:
    $ alias dog=cat
    $ cat | python splice.py | dog
    
    type 'exit' to cause the pipeline to exit, any other typed data will pass through the 
    pipeline uneditied
    """
    import sys
    import os
    
    # gets arg 1 of sys.argv if set otherwise falls back to 'exit' as argv will be too
    # short and 'exit' will be on the end (in pos 1)
    command = (sys.argv + ['exit'])[1]
    
    max_len = 2**24 # chosen arbitrarily
    
    while True:
        bytes = tee(sys.stdin, sys.stdout, max_len)
        print("tee'd {} bytes".format(bytes))
        sys.stdout.flush()
        if command in sys.stdin.read(bytes):
            print("Exit command ({}) found, exiting".format(command))
            break

def _vmsplice_main():
    import sys
    import os

    r_fd, w_fd = os.pipe()
    
    buf = ["this is a test",
           " and this should be on the same line",
           "\nsupprise, newline this time\n"
          ]
    bytes = vmsplice(w_fd, buf)
    print('vmspliced {} bytes'.format(bytes))
    splice(r_fd, sys.stdout, len=bytes)
    print('spliced {} bytes'.format(bytes))

if __name__ == "__main__":
    _socket_main()
    #_main()
