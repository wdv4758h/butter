#!/usr/bih/env python
from ..timerfd import Timerfd as _Timerfd, _ffi, CLOCK_REALTIME
from collections import deque
import asyncio

class Timerfd_async:
    def __init__(self, clock_type=CLOCK_REALTIME, flags=0, *, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._timerfd = _Timerfd(clock_type, flags)
        self._getters = deque()
        
        self.set_one_off = self._timerfd.set_one_off
        self.set_reoccuring = self._timerfd.set_reoccuring
        self.enabled = self._timerfd.__class__.__dict__['enabled']
        self.disabled = self._timerfd.__class__.__dict__['disabled']
        self.disable = self._timerfd.disable
        self.get_current = self._timerfd.get_current
        
    @asyncio.coroutine
    def wait(self):
        """Wait for the timer to expire, returning how many events have 
        elappsed since the last call to wait()

        Returns
        --------
        :return: The current count of the timer
        :rtype: int
        """
        self._loop.add_reader(self._timerfd.fileno(), self._read_event)

        waiter = asyncio.Future(loop=self._loop)

        self._getters.append(waiter)

        return (yield from waiter)

    def _consume_done_getters(self):
        # Delete waiters at the head of the get() queue who've timed out.
        while self._getters and self._getters[0].done():
            self._getters.popleft()

    def _read_event(self):
        value = self._timerfd._read()
        self._put_event(value)
    
    def _put_event(self, value):
        """Put an item into the queue without blocking.

        If no free slot is immediately available, raise QueueFull.
        """
        self._loop.remove_reader(self._timerfd.fileno())

        self._consume_done_getters()

        for getter in self._getters:
            getter.set_result(value)

    def close(self):
        self._timerfd.close()

def watcher(loop):
    from asyncio import sleep
    from time import time
    
    t = Timerfd_async()

    time_val = 0.5
    t.set_reoccuring(time_val)
    print("Setting time interval to {:.2f} seconds".format(time_val))

    for i in range(5):
        old_time = time()
        num_events = yield from t.wait()
        new_time = time()
        assert num_events == 1, "Too many events"
        print("Woke up after {:.2f} seconds".format(new_time - old_time))

    print("Got all 5 events")

    print("Sleeping for 0.3s")
    yield from sleep(0.3)
    print("Next event:", t.get_current())
    

def main():
    import logging
    
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())
    
    loop = asyncio.get_event_loop()
    
    from asyncio import Task
    task = Task(watcher(loop))
    
    loop.run_forever()


if __name__ == "__main__":
    main()
