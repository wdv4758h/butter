#!/usr/bin/env python
"""when seconds or nano_seconds was set to 0 rather than None (the default) the
value would not be reset to 0 but instead the previous value would remain in 
place

this was only visible if a user had previously set a value
"""
from butter.timerfd import Timer, TimerVal
from butter.utils import TimeoutError
from select import select
from pytest import raises, fail

def test_f468afef89d():
    TEST_PERIOD = 1
    TIMEOUT = TEST_PERIOD * 2
    
    # create a timer
    timer = Timer()

    # set the timer
    timer.offset(seconds=TEST_PERIOD, nano_seconds=TEST_PERIOD)
    timer.repeats(seconds=TEST_PERIOD, nano_seconds=TEST_PERIOD)
    timer.update()

    # ensure it fires
    try:
        timer.wait(TIMEOUT)
    except TimeoutError:
        fail("Timer did not fire")
    
    # drain the event list
    timer.read_event()

    # reset and update the timer
    timer.disable()
    timer.update()

    new_val = timer.get_current()
    assert new_val.next_event == (0, 0), 'Timer offset did not get reset'
    
    with raises(TimeoutError):
        "Timer fired when is should have been disabled"
        timer.wait(TIMEOUT)
