#!/usr/bin/env python
"""eventfd: maintain an atomic counter inside a file descriptor"""

from __future__ import print_function

from .utils import Eventlike as _Eventlike

from os import write as _write, read as _read, close as _close
from cffi import FFI as _FFI
import errno as _errno

_ffi = _FFI()
_ffi.cdef("""
#define EFD_CLOEXEC ...
#define EFD_NONBLOCK ...
#define EFD_SEMAPHORE ...

int eventfd(unsigned int initval, int flags);
""")

_C = _ffi.verify("""
#include <sys/eventfd.h>
#include <stdint.h> /* Definition of uint64_t */
""", libraries=[])

def eventfd(inital_value=0, flags=0):
    """Create a new eventfd
    
    Arguments
    ----------
    :param int inital_value: The inital value to set the eventfd to
    :param int flags: Flags to specify extra options
    
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
    fd = _C.eventfd(inital_value, flags)
    
    if fd < 0:
        err = _ffi.errno
        if err == _errno.EINVAL:
            raise ValueError("Invalid value in flags")
        elif err == _errno.EMFILE:
            raise OSError("Max per process FD limit reached")
        elif err == _errno.ENFILE:
            raise OSError("Max system FD limit reached")
        elif err == _errno.ENODEV:
            raise OsError("Could not mount (internal) anonymous inode device")
        elif err == _errno.ENOMEM:
            raise MemoryError("Insufficent kernel memory available")
        else:
            # If you are here, its a bug. send us the traceback
            raise ValueError("Unknown Error: {}".format(err))

    return fd

EFD_CLOEXEC = _C.EFD_CLOEXEC
EFD_NONBLOCK = _C.EFD_NONBLOCK
EFD_SEMAPHORE = _C.EFD_SEMAPHORE

class Eventfd(_Eventlike):
    def __init__(self, inital_value=0, flags=0):
        """Create a new Eventfd object

        Arguments
        ----------
        :param int inital_value: The inital value to set the eventfd to
        :param int flags: Flags to specify extra options
        
        Flags
        ------
        EFD_CLOEXEC: Close the eventfd when executing a new program
        EFD_NONBLOCK: Open the socket in non-blocking mode
        EFD_SEMAPHORE: Provide semaphore like semantics for read operations
        """
        super(self.__class__, self).__init__()
        self._fd = eventfd(inital_value, flags)
        
    def increment(self, value=1):
        """Increment the counter by the specified value
        
        :param int value: The value to increment the counter by (default=1)
        """
        packed_value = _ffi.new('uint64_t[1]', (value,))
        packed_value = _ffi.buffer(packed_value)[:]
        _write(self.fileno(), packed_value)

    def _read_events(self):
        """Read the current value of the counter and zero the counter

        Returns
        --------
        :return: The current count of the timer
        :rtype: int
        """
        data = _read(self.fileno(), 8)
        value = _ffi.new('uint64_t[1]')
        _ffi.buffer(value, 8)[0:8] = data

        return [value[0]] # this may seem redundent but the original
                          # container is not actually a list

    def __int__(self):
        return self.read_event()


def _main():
    ev = Eventfd(30)
    print(ev)
    
    print('First Read:', int(ev))
    # read blocks if 0
    #print('Second Read:', int(ev))
    
    print("Adding 30 to zero'd counter")
    ev.increment(30)
    
    print("Read value back:", int(ev))

    print("Incrementing value 5 times")
    ev.increment(30)
    ev.increment(30)
    ev.increment(30)
    ev.increment(30)
    ev.increment(30)
    
    print("Read value back:", int(ev))

    print("Closing FD")    
    ev.close()
    try:
        ev.close()
    except ValueError:
        print("Could not close closed FD, OK")
    else:
        print("Closed closed FD, this is bad")
    
    print(ev)
    
if __name__ == "__main__":
    _main()
