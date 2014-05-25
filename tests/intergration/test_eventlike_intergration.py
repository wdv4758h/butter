from butter.eventfd import Eventfd
from butter.fanotify import Fanotify
from butter.inotify import Inotify
from butter.signalfd import Signalfd
from butter.timerfd import Timerfd
import pytest


@pytest.mark.intergration
def test_eventfd_intergration():
    """End to end testing and example of eventfd usage"""
    test_val = 36
    ev = Eventfd(test_val)

    assert int(ev) == test_val, "Inital value did not match expected"

    ev.increment(test_val)
    assert int(ev) == test_val, "Inital value did not match expected"

    [ev.increment(test_val) for i in range(5)]
    assert int(ev) == test_val * 5, "Inital value did not match expected"

    ev.close()
