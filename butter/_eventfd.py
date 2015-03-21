#!/usr/bin/env python
"""eventfd: maintain an atomic counter inside a file descriptor"""
from .utils import UnknownError, CLOEXEC_DEFAULT
from cffi import FFI
import errno

ffi = FFI()
ffi.cdef("""
#define EFD_CLOEXEC ...
#define EFD_NONBLOCK ...
#define EFD_SEMAPHORE ...

int eventfd(unsigned int initval, int flags);
""")

C = ffi.verify("""
#include <sys/eventfd.h>
#include <stdint.h> /* Definition of uint64_t */
""", libraries=[], ext_package="butter")

EFD_CLOEXEC = C.EFD_CLOEXEC
EFD_NONBLOCK = C.EFD_NONBLOCK
EFD_SEMAPHORE = C.EFD_SEMAPHORE

def eventfd(inital_value=0, flags=0, closefd=CLOEXEC_DEFAULT):
    """Create a new eventfd
    
    Arguments
    ----------
    :param int inital_value: The inital value to set the eventfd to
    :param int flags: Flags to specify extra options
    :param bool closefd: Close the fd when a new process is exec'd
        
    Flags
    ------
    EFD_CLOEXEC: Close the eventfd when executing a new program
    EFD_NONBLOCK: Open the socket in non-blocking mode
    EFD_SEMAPHORE: Provide semaphore like semantics for read operations
    
    Returns
    --------
    :return: The file descriptor representing the eventfd
    :rtype: int
    
    Exceptions
    -----------
    :raises ValueError: Invalid value in flags
    :raises OSError: Max per process FD limit reached
    :raises OSError: Max system FD limit reached
    :raises OSError: Could not mount (internal) anonymous inode device
    :raises MemoryError: Insufficient kernel memory
    """
    assert isinstance(inital_value, int), "Inital value must be an integer"
    assert inital_value >= 0, "Inital value must be a positive number"
    assert isinstance(flags, int), "Flags must be an integer"
    
    if closefd:
        flags |= EFD_CLOEXEC
        
    fd = C.eventfd(inital_value, flags)
    
    if fd < 0:
        err = ffi.errno
        if err == errno.EINVAL:
            raise ValueError("Invalid value in flags")
        elif err == errno.EMFILE:
            raise OSError("Max per process FD limit reached")
        elif err == errno.ENFILE:
            raise OSError("Max system FD limit reached")
        elif err == errno.ENODEV:
            raise OSError("Could not mount (internal) anonymous inode device")
        elif err == errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory available")
        else:
            # If you are here, its a bug. send us the traceback
            raise UnknownError(err)

    return fd

def str_to_events(str):
    value = ffi.new('uint64_t[1]')
    ffi.buffer(value, 8)[0:8] = str

    return [value[0]] # this may seem redundent but the original
                      # container is not actually a list

def event_to_str(event):
    # We use ffi rather than the array module as
    # python2.7 does not have an unsigned 64 bit in type
    event = ffi.new('uint64_t[1]', (event,))
    packed_event = ffi.buffer(event)[:]
    
    return packed_event
