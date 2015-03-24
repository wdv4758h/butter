from butter.eventfd import Eventfd
from butter.fanotify import Fanotify
from butter.inotify import Inotify
from butter.signalfd import Signalfd
from butter.timerfd import Timer
import pytest


@pytest.fixture(params=[Eventfd, Fanotify, Inotify, Signalfd, Timer])
def obj(Obj):
    o = Obj.__new__(Obj)
    
    return o

@pytest.mark.parametrize('obj1,obj2', [
                         (obj(Eventfd),  obj(Eventfd)  ),
                         (obj(Fanotify), obj(Fanotify) ),
                         (obj(Inotify),  obj(Inotify)  ),
                         (obj(Signalfd), obj(Signalfd) ),
                         (obj(Timer),    obj(Timer)    ),
                         ])
@pytest.mark.unit
def test_equals_same(obj1, obj2):
    obj1._fd = 1
    obj2._fd = 1

    assert obj1 == obj2, '2 Identical objects are comparing as diffrent'


@pytest.mark.parametrize('obj1,obj2', [
                         (obj(Eventfd),  obj(Eventfd)  ),
                         (obj(Fanotify), obj(Fanotify) ),
                         (obj(Inotify),  obj(Inotify)  ),
                         (obj(Signalfd), obj(Signalfd) ),
                         (obj(Timer),    obj(Timer)    ),
                         ])
def test_equals_diffrent(obj1, obj2):
    obj1._fd = 1
    obj2._fd = 2

    assert obj1 != obj2, '2 Diffrent objects are comparing as equivlent'

@pytest.mark.parametrize('obj1,obj2', [
                         (obj(Eventfd),  obj(Eventfd)  ),
                         (obj(Fanotify), obj(Fanotify) ),
                         (obj(Inotify),  obj(Inotify)  ),
                         (obj(Signalfd), obj(Signalfd) ),
                         (obj(Timer),    obj(Timer)    ),
                         ])
def test_hashable(obj1, obj2):
    obj1._fd = 1
    obj2 = None # we are not using this
    assert isinstance(hash(obj), int), 'hash of object is not an int'
    assert {obj1: None}, 'Object cant be used as a key in a dict (not hashable)'
