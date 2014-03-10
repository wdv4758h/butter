#!/usr/bin/env python
"""splice: wrapper around the splice() syscall"""

from __future__ import print_function

from select import select as _select
from collections import namedtuple
from cffi import FFI as _FFI
import errno as _errno

_ffi = _FFI()
_ffi.cdef("""
#define SPLICE_F_MOVE     ... /* This is a noop in modern kernels and is left here for compatibility */
#define SPLICE_F_NONBLOCK ... /* Make splice operations Non blocking (as long as the fd's are non blocking) */
#define SPLICE_F_MORE     ... /* After splice() more data will be sent, this is a hint to add TCP_CORK like buffering */
#define SPLICE_F_GIFT     ... /* unused for splice() (vmsplice compatibility) */

ssize_t splice(int fd_in, signed long long *off_in, int fd_out, signed long long *off_out, size_t len, unsigned int flags);
""")

_C = _ffi.verify("""
#include <fcntl.h>
""", libraries=[])

def splice(fd_in, fd_out, in_offset=0, out_offset=0, len=0, flags=0):
    """Take data from fd_in and pass it to fd_out without going through userspace
    
    Arguments:
    -----------
    Flags:
    -------
    SPLICE_F_MOVE: This is a noop in modern kernels and is left here for compatibility
    SPLICE_F_NONBLOCK: Make splice operations Non blocking (as long as the fd's are non blocking)
    SPLICE_F_MORE: After splice() more data will be sent, this is a hint to add TCP_CORK like buffering
    SPLICE_F_GIFT: unused for splice() (vmsplice compatibility)
    
    Returns:
    ---------
    int: Number of bytes written
    
    Exceptions:
    ------------
    EBADF   One or both file descriptors are not valid, or do not have proper read-write mode.
    EINVAL  Target filesystem doesn't support splicing; target file is opened in append mode; neither of the descriptors refers to a pipe; or offset given for
            nonseekable device.
    ENOMEM  Out of memory.
    ESPIPE  Either off_in or off_out was not NULL, but the corresponding file descriptor refers to a pipe.

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
        elif err == _errno.ESPIPE:
            raise OSError("offset specified but one of the fds is a pipe")
        elif err == _errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory avalible")
        elif err == _errno.EAGAIN:
            raise IOError("No writers on fd_in or a fd is open in BLOCKING mode and NON_BLOCK specified to splice()")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))

    return size

SPLICE_F_MOVE = _C.SPLICE_F_MOVE    
SPLICE_F_NONBLOCK = _C.SPLICE_F_NONBLOCK
SPLICE_F_MORE = _C.SPLICE_F_MORE    
SPLICE_F_GIFT = _C.SPLICE_F_GIFT    

def main():
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


def socket_main():
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

    max_segment = 2**24
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


if __name__ == "__main__":
    socket_main()
    #main()
