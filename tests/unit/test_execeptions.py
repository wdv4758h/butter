#!/usr/bin/env python

from butter import eventfd, _eventfd
from pytest import raises
import pytest
import errno

@pytest.mark.parametrize('path,module,func,errno,exception', [
                         ('butter._eventfd.C.eventfd', _eventfd, _eventfd.eventfd, errno.EINVAL, ValueError),
                         ('butter._eventfd.C.eventfd', _eventfd, _eventfd.eventfd, errno.EMFILE, OSError),
                         ('butter._eventfd.C.eventfd', _eventfd, _eventfd.eventfd, errno.ENFILE, OSError), # errno is diffrent to above
                         ('butter._eventfd.C.eventfd', _eventfd, _eventfd.eventfd, errno.ENODEV, OSError),
                         ('butter._eventfd.C.eventfd', _eventfd, _eventfd.eventfd, errno.ENOMEM, MemoryError),
                         ('butter._eventfd.C.eventfd', _eventfd, _eventfd.eventfd, errno.EHOSTDOWN, ValueError), # errno chosen as unused in our code
                         ])
@pytest.mark.unit
def test_exception(mocker, path, module, func, errno, exception):
    # patch the underlying function as exposed by cffi
    m = mocker.patch(path)
    # -1 forces most of our code to check ffi.errno
    m.return_value = -1
    
    # Make the C level errno the val we want
    module.ffi.errno = errno
    
    # Call the same function as the user and wait for it to blow up
    with raises(exception):
        func()
