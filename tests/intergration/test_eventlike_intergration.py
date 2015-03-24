from butter.eventfd import Eventfd
from butter.fanotify import FAN_MODIFY, FAN_ONDIR, FAN_ACCESS, FAN_EVENT_ON_CHILD, FAN_OPEN, FAN_CLOSE
from butter.fanotify import Fanotify, FAN_CLASS_NOTIF
from butter.inotify import Inotify, IN_ALL_EVENTS
from butter.signalfd import Signalfd, pthread_sigmask
from butter.timerfd import Timer

from tempfile import TemporaryDirectory
from time import time, sleep
import subprocess
import signal
import os

import pytest


@pytest.mark.intergration
@pytest.mark.eventfd
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

@pytest.mark.skipif(os.getuid() != 0, reason="fanotify can only be used by root")
@pytest.mark.intergration
@pytest.mark.fanotify
def test_fanotify_intergration():
    with TemporaryDirectory() as tmpdir:
        notifier = Fanotify(FAN_CLASS_NOTIF)
        FLAGS = FAN_MODIFY|FAN_ONDIR|FAN_ACCESS|FAN_EVENT_ON_CHILD|FAN_OPEN|FAN_CLOSE
        notifier.watch(0, FLAGS, tmpdir)
        
        count = 5
        
        os.listdir(tmpdir)

        for i, event in zip(range(count), notifier):
            assert event.pid == os.getpid()
            assert event.filename.startswith(tmpdir)
            event.close()
            os.listdir(tmpdir)
        
        notifier.close()

@pytest.mark.intergration
@pytest.mark.inotify
def test_inotify_intergration():
    with TemporaryDirectory() as tmpdir:
        notifier = Inotify()
        wd = notifier.watch(tmpdir, IN_ALL_EVENTS)
    
        count = 5
        
        os.listdir(tmpdir)

        for i, event in zip(range(count), notifier):
            assert event.filename.decode() == '' # inotify does not keep the prefix
                                                 # you have to keep track of it via
                                                 # the wd
            assert event.wd == wd
            assert event.is_dir_event
            assert event.open_event or event.close_nowrite_event
                
            os.listdir(tmpdir)
    
        notifier.close()

    
@pytest.mark.intergration
@pytest.mark.signalfd
def test_signalfd_intergration():
    test_signal = signal.SIGUSR1

    sfd = Signalfd()
    sfd.enable(test_signal)

    pthread_sigmask(signal.SIG_BLOCK, [test_signal])
    os.kill(os.getpid(), test_signal)

    s = sfd.wait()
    assert s.signal == test_signal, "Did not recive expected signal"

    sfd.close()


@pytest.mark.intergration
@pytest.mark.timerfd
def test_timerfd_intergration():
    "Check and confirm that a 0.5s timer fires roughly every 0.5s as a smoke test"
    INTERVAL = 1
    UPPER_BOUND = INTERVAL * 1.1
    LOWER_BOUND = INTERVAL * 0.9
    DELAY = 0.3
    NANO_SECONDS_TO_SECONDS = 1000000000.0
    
    t = Timer()
    t.repeats(seconds=INTERVAL).update()

    for i in range(5):
        old_time = time()
        num_events = t.wait()
        new_time = time()

        assert num_events == 1, "Too many events"
        period = new_time - old_time
        assert LOWER_BOUND < period < UPPER_BOUND, "timer fired too late or too early"

    # Wait a bit and ensure that the remaining time on the timerfd gets updated
    sleep(DELAY)
    expected_value = INTERVAL - DELAY
    
    next_event = t.get_current().next_event
    next_event = next_event.seconds + (next_event.nano_seconds/NANO_SECONDS_TO_SECONDS)
    
    LOWER_BOUND = expected_value * 0.9
    UPPER_BOUND = expected_value * 1.1

    assert LOWER_BOUND < next_event < UPPER_BOUND, "current timer does not match what we expect after a (known) time delay"

    t.close()
