#!/usr/bin/env python
from cffi import FFI as _FFI
import fcntl
import array

_ffi = _FFI()
_ffi.cdef("""
#define FIONREAD ...
""")

_C = _ffi.verify("""
#include <sys/ioctl.h>
""", libraries=[])

def get_buffered_length(fd):
    buf = array.array("I", [0])
    fcntl.ioctl(fd, _C.FIONREAD, buf)
    return buf[0]
            
