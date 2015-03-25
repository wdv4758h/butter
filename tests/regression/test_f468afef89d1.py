#!/usr/bin/env python
"""when seconds or nano_seconds was set to 0 rather than None (the default) the
value would not be reset to 0 but instead the previous value would remain in 
place

this was only visible if a user had previously set a value
"""
from butter.timerfd import Timer
from select import select

def test_f468afef89dTEST_PERIOD():
    TEST_PERIOD = 1
    TIMEOUT = TEST_PERIOD * 2
    
    # create a timer
    timer = Timer()

    # set the timer
    timer.offset(seconds=TEST_PERIOD, nano_seconds=TEST_PERIOD)
    timer.repeats(seconds=TEST_PERIOD, nano_seconds=TEST_PERIOD)
    timer.update()

    # ensure it fires
    r_fd, _, _ = select([timer], [], [])

    # reset and update the timer
    timer.offset(seconds=0, nano_seconds=0)
    timer.repeats(seconds=0, nano_seconds=0)
    timer.update()
    # we set this twice to get the value we set the timer to
    new_val = timer.update()
    
    assert new_val.next_event == (0, 0), 'Timer offset did not get reset'
    assert new_val.period == (0, 0), 'Timer period did not get reset'
    
    # ensure it does not fire
    select([timer], [], [], TIMEOUT)
