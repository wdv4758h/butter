#!/usr/bin/env python

from butter import eventfd, _eventfd
from butter import fanotify, _fanotify
from butter import inotify, _inotify
from butter import signalfd, _signalfd
from butter.signalfd import SFD_CLOEXEC, SFD_NONBLOCK
from butter import timerfd, _timerfd
from butter._timerfd import PointerError, TimerSpec
from butter.utils import PermissionError
from pytest import raises
from signal import SIGKILL
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

 ('butter._inotify.C.inotify_init1', _inotify, _inotify.inotify_init, (), errno.EINVAL, ValueError),
 ('butter._inotify.C.inotify_init1', _inotify, _inotify.inotify_init, (), errno.EMFILE, OSError),
 ('butter._inotify.C.inotify_init1', _inotify, _inotify.inotify_init, (), errno.ENFILE, OSError), # errno is diffrent to above
 ('butter._inotify.C.inotify_init1', _inotify, _inotify.inotify_init, (), errno.ENOMEM, MemoryError),
 ('butter._inotify.C.inotify_init1', _inotify, _inotify.inotify_init, (), errno.EHOSTDOWN, ValueError), # errno chosen as unused in our code

 ('butter._inotify.C.inotify_add_watch', _inotify, _inotify.inotify_add_watch, (0, '', 0), errno.EINVAL, ValueError), 
 ('butter._inotify.C.inotify_add_watch', _inotify, _inotify.inotify_add_watch, (0, '', 0), errno.EACCES, OSError), 
 ('butter._inotify.C.inotify_add_watch', _inotify, _inotify.inotify_add_watch, (0, '', 0), errno.EBADF, OSError), 
 ('butter._inotify.C.inotify_add_watch', _inotify, _inotify.inotify_add_watch, (0, '', 0), errno.EFAULT, OSError), 
 ('butter._inotify.C.inotify_add_watch', _inotify, _inotify.inotify_add_watch, (0, '', 0), errno.ENOENT, OSError), 
 ('butter._inotify.C.inotify_add_watch', _inotify, _inotify.inotify_add_watch, (0, '', 0), errno.ENOSPC, OSError), 
 ('butter._inotify.C.inotify_add_watch', _inotify, _inotify.inotify_add_watch, (0, '', 0), errno.ENOMEM, MemoryError), 
 ('butter._inotify.C.inotify_add_watch', _inotify, _inotify.inotify_add_watch, (0, '', 0), errno.EHOSTDOWN, ValueError), # errno chosen as unused in our code

 ('butter._inotify.C.inotify_rm_watch', _inotify, _inotify.inotify_rm_watch, (0, 0), errno.EINVAL, ValueError),
 ('butter._inotify.C.inotify_rm_watch', _inotify, _inotify.inotify_rm_watch, (0, 0), errno.EBADF, OSError),
 ('butter._inotify.C.inotify_rm_watch', _inotify, _inotify.inotify_rm_watch, (0, 0), errno.EHOSTDOWN, ValueError), # errno chosen as unused in our code

 ('butter._signalfd.C.signalfd', _signalfd, _signalfd.signalfd, ([], 0, 0xffff ^ (SFD_CLOEXEC|SFD_NONBLOCK)),  errno.EINVAL, ValueError),
 ('butter._signalfd.C.signalfd', _signalfd, _signalfd.signalfd, ([], 0, SFD_CLOEXEC|SFD_NONBLOCK),  errno.EINVAL, OSError), # FD is invalid (set flags just to ensure nothing blows up)
 ('butter._signalfd.C.signalfd', _signalfd, _signalfd.signalfd, ([],), errno.EBADF,  ValueError),
 ('butter._signalfd.C.signalfd', _signalfd, _signalfd.signalfd, ([],), errno.ENFILE, OSError),
 ('butter._signalfd.C.signalfd', _signalfd, _signalfd.signalfd, ([],), errno.EMFILE, OSError),
 ('butter._signalfd.C.signalfd', _signalfd, _signalfd.signalfd, ([],), errno.ENODEV, OSError),
 ('butter._signalfd.C.signalfd', _signalfd, _signalfd.signalfd, ([],), errno.ENOMEM, MemoryError),
 ('butter._signalfd.C.signalfd', _signalfd, _signalfd.signalfd, ([],), errno.EHOSTDOWN, ValueError), # errno chosen as unused in our code

 ('butter._signalfd.C.pthread_sigmask', _signalfd, _signalfd.pthread_sigmask, (0, SIGKILL), errno.EMFILE, ValueError),
 ('butter._signalfd.C.pthread_sigmask', _signalfd, _signalfd.pthread_sigmask, (0, SIGKILL), errno.EMFILE, ValueError),
 ('butter._signalfd.C.pthread_sigmask', _signalfd, _signalfd.pthread_sigmask, (0, SIGKILL), errno.EHOSTDOWN, ValueError),

 ('butter._timerfd.C.timerfd_create', _timerfd, _timerfd.timerfd, (), errno.EINVAL, ValueError),
 ('butter._timerfd.C.timerfd_create', _timerfd, _timerfd.timerfd, (), errno.EMFILE, OSError),
 ('butter._timerfd.C.timerfd_create', _timerfd, _timerfd.timerfd, (), errno.ENFILE, OSError),
 ('butter._timerfd.C.timerfd_create', _timerfd, _timerfd.timerfd, (), errno.ENODEV, OSError),
 ('butter._timerfd.C.timerfd_create', _timerfd, _timerfd.timerfd, (), errno.ENOMEM, MemoryError),
 ('butter._timerfd.C.timerfd_create', _timerfd, _timerfd.timerfd, (), errno.EHOSTDOWN, ValueError),

 ('butter._timerfd.C.timerfd_gettime', _timerfd, _timerfd.timerfd_gettime, (0,), errno.EBADF, ValueError),
 ('butter._timerfd.C.timerfd_gettime', _timerfd, _timerfd.timerfd_gettime, (0,), errno.EFAULT, PointerError),
 ('butter._timerfd.C.timerfd_gettime', _timerfd, _timerfd.timerfd_gettime, (0,), errno.EINVAL, ValueError),
 ('butter._timerfd.C.timerfd_gettime', _timerfd, _timerfd.timerfd_gettime, (0,), errno.EHOSTDOWN, ValueError),

 ('butter._timerfd.C.timerfd_settime', _timerfd, _timerfd.timerfd_settime, (0, TimerSpec()), errno.EINVAL, ValueError),
 ('butter._timerfd.C.timerfd_settime', _timerfd, _timerfd.timerfd_settime, (0, 0), errno.EFAULT, PointerError),
 ('butter._timerfd.C.timerfd_settime', _timerfd, _timerfd.timerfd_settime, (0, 0), errno.EMFILE, OSError),
 ('butter._timerfd.C.timerfd_settime', _timerfd, _timerfd.timerfd_settime, (0, 0), errno.ENFILE, OSError),
 ('butter._timerfd.C.timerfd_settime', _timerfd, _timerfd.timerfd_settime, (0, 0), errno.ENODEV, OSError),
 ('butter._timerfd.C.timerfd_settime', _timerfd, _timerfd.timerfd_settime, (0, 0), errno.ENOMEM, MemoryError),
 ('butter._timerfd.C.timerfd_settime', _timerfd, _timerfd.timerfd_settime, (0, 0), errno.EHOSTDOWN, ValueError),
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
