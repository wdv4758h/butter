from butter.eventfd import Eventfd
from butter.fanotify import Fanotify
from butter.inotify import Inotify
from butter.signalfd import Signalfd
from butter.timerfd import Timerfd
import pytest


@pytest.fixture(params=[Eventfd, Fanotify, Inotify, Signalfd, Timerfd])
def obj(request):
    Obj = request.param
    o = Obj.__new__(Obj)
    
    return o

@pytest.mark.repr
@pytest.mark.unit
def test_repr_name(obj):
    obj._fd = 1
    assert obj.__class__.__name__ in repr(obj), "Instance's representation does not contain its own name"

@pytest.mark.repr
@pytest.mark.unit
def test_repr_fd(obj):
    obj._fd = 1
    assert 'fd=1' in repr(obj), "Instance does not list its own fd (used for easy identifcation)"
    

@pytest.mark.repr
@pytest.mark.unit
def test_repr_fd_closed(obj):
    obj._fd = None
    assert 'fd=closed' in repr(obj), "Instance does not indicate it is closed"
