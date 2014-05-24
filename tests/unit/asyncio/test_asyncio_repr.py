from butter.asyncio.eventfd import Eventfd_async
from butter.asyncio.fanotify import Fanotify_async
from butter.asyncio.inotify import Inotify_async
from butter.asyncio.signalfd import Signalfd_async
from butter.asyncio.timerfd import Timerfd_async
from collections import namedtuple
import pytest
import sys

class Mock_fd_obj(object):
    def __init__(self, fd):
        self._fd = fd

@pytest.fixture(params=[(Eventfd_async,  '_eventfd' ),
                        (Fanotify_async, '_fanotify'), 
                        (Inotify_async,  '_inotify' ),
                        (Signalfd_async, '_signalfd'), 
                        (Timerfd_async,  '_timerfd' )])
def obj(request):
    Obj, sub_obj_name = request.param
    o = Obj.__new__(Obj)
    o._value = 3 # needed for eventfd
    
    sub_obj = Mock_fd_obj(1) #fd=1
    setattr(o, sub_obj_name, sub_obj)
    
    return o

@pytest.fixture(params=[(Eventfd_async,  '_eventfd' ),
                        (Fanotify_async, '_fanotify'), 
                        (Inotify_async,  '_inotify' ),
                        (Signalfd_async, '_signalfd'), 
                        (Timerfd_async,  '_timerfd' )])
def obj_closed(request):
    Obj, sub_obj_name = request.param
    o = Obj.__new__(Obj)
    o._value = 3 # needed for eventfd
    
    sub_obj = Mock_fd_obj(None)
    setattr(o, sub_obj_name, sub_obj)
    
    return o

@pytest.mark.skipif(sys.version_info < (3,4), reason="requires python3.4/asyncio")
@pytest.mark.repr
@pytest.mark.unit
@pytest.mark.asyncio
def test_repr_name(obj):
    assert obj.__class__.__name__ in repr(obj), "Instance's representation does not contain its own name"

@pytest.mark.skipif(sys.version_info < (3,4), reason="requires python3.4/asyncio")
@pytest.mark.repr
@pytest.mark.unit
@pytest.mark.asyncio
def test_repr_fd(obj):
    assert 'fd=1' in repr(obj), "Instance does not list its own fd (used for easy identifcation)"
    

@pytest.mark.skipif(sys.version_info < (3,4), reason="requires python3.4/asyncio")
@pytest.mark.repr
@pytest.mark.unit
@pytest.mark.asyncio
def test_repr_fd_closed(obj_closed):
    assert 'fd=closed' in repr(obj_closed), "Instance does not indicate it is closed"
