#!/usr/bin/env python

from butter import eventfd, _eventfd
from butter import fanotify, _fanotify
from butter.utils import PermissionError
from pytest import raises
import pytest
import errno

@pytest.mark.parametrize('path,module,func,args,errno,exception', [
                         ('butter._eventfd.C.eventfd', _eventfd, _eventfd.eventfd, (), errno.EINVAL, ValueError),
                         ('butter._eventfd.C.eventfd', _eventfd, _eventfd.eventfd, (), errno.EMFILE, OSError),
                         ('butter._eventfd.C.eventfd', _eventfd, _eventfd.eventfd, (), errno.ENFILE, OSError), # errno is diffrent to above
                         ('butter._eventfd.C.eventfd', _eventfd, _eventfd.eventfd, (), errno.ENODEV, OSError),
                         ('butter._eventfd.C.eventfd', _eventfd, _eventfd.eventfd, (), errno.ENOMEM, MemoryError),
                         ('butter._eventfd.C.eventfd', _eventfd, _eventfd.eventfd, (), errno.EHOSTDOWN, ValueError), # errno chosen as unused in our code

                         ('butter._fanotify.C.fanotify_init', _fanotify, _fanotify.fanotify_init, (0,), errno.EINVAL, ValueError),
                         ('butter._fanotify.C.fanotify_init', _fanotify, _fanotify.fanotify_init, (0,), errno.EMFILE, OSError),
                         ('butter._fanotify.C.fanotify_init', _fanotify, _fanotify.fanotify_init, (0,), errno.ENOMEM, MemoryError),
                         ('butter._fanotify.C.fanotify_init', _fanotify, _fanotify.fanotify_init, (0,), errno.EPERM,  PermissionError),
                         ('butter._fanotify.C.fanotify_init', _fanotify, _fanotify.fanotify_init, (0,), errno.EHOSTDOWN, ValueError), # errno chosen as unused in our code

                         ('butter._fanotify.C.fanotify_mark', _fanotify, _fanotify.fanotify_mark, (0, 0, 0, ''), errno.EINVAL, ValueError),
                         ('butter._fanotify.C.fanotify_mark', _fanotify, _fanotify.fanotify_mark, (0, 0, 0, ''), errno.EBADF,  OSError),
                         ('butter._fanotify.C.fanotify_mark', _fanotify, _fanotify.fanotify_mark, (0, 0, 0, ''), errno.ENOENT, OSError),
                         ('butter._fanotify.C.fanotify_mark', _fanotify, _fanotify.fanotify_mark, (0, 0, 0, ''), errno.ENOMEM, MemoryError),
                         ('butter._fanotify.C.fanotify_mark', _fanotify, _fanotify.fanotify_mark, (0, 0, 0, ''), errno.ENOSPC, OSError),
                         ('butter._fanotify.C.fanotify_mark', _fanotify, _fanotify.fanotify_mark, (0, 0, 0, ''), errno.EHOSTDOWN, ValueError), # errno chosen as unused in our code
                         ])
@pytest.mark.unit
def test_exception(mocker, path, module, func, args, errno, exception):
    """Test the mapping of kernel returned error codes to python Exceptions"""
    # patch the underlying function as exposed by cffi
    m = mocker.patch(path)
    # -1 forces most of our code to check ffi.errno
    m.return_value = -1
    
    # Make the C level errno the val we want
    module.ffi.errno = errno
    
    # Call the same function as the user and wait for it to blow up
    with raises(exception):
        func(*args)
