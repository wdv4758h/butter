from butter.eventfd import Eventfd
from butter.fanotify import Fanotify
from butter.inotify import Inotify
from butter.signalfd import Signalfd
from butter.timerfd import Timer, TimerVal
import pytest


@pytest.fixture(params=[Eventfd, Fanotify, Inotify, Signalfd, Timer])
def obj(mocker, request):
    # fanotify needs root to run, mock it so it just fakes it
    m = mocker.patch('butter._fanotify.C.fanotify_init')
    m.return_value = 5
    
    Obj = request.param
    o = Obj(flags=0)
    
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

@pytest.mark.repr
@pytest.mark.unit
@pytest.mark.parametrize('time_obj', [TimerVal, Timer])
def test_timerval(time_obj):
    t = time_obj().offset(1, 2).repeats(3, 4)
    r = repr(t)
    assert t.__class__.__name__ in r, 'Does not contain its own name'
    assert '1' in r, 'Value not in output'
    assert '1s' in r, 'Value does not have units'
    assert '2' in r, 'Value not in output'
    assert '2ns' in r, 'Value does not have units'
    assert '3' in r, 'Value not in output'
    assert '3s' in r, 'Value does not have units'
    assert '4' in r, 'Value not in output'
    assert '4ns' in r, 'Value does not have units'
