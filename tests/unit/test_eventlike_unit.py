from butter.eventfd import Eventfd
from butter.fanotify import Fanotify
from butter.inotify import Inotify
from butter.signalfd import Signalfd
from butter.timerfd import Timerfd
import pytest
import os

@pytest.fixture(params=[Eventfd, Fanotify, Inotify, Signalfd, Timerfd])
def obj(request):
    Obj = request.param
    o = Obj.__new__(Obj)
    
    return o

@pytest.mark.eventlike
@pytest.mark.unit
def test_fd_closed(obj):
    """Ensure you cant close the same fd twice (as it may be reused)"""
    old_close = os.close
    os.close = lambda fd: None
    obj._fd = 1
    
    obj.close()
    with pytest.raises(ValueError):
        obj.close()


    os.close = old_close
