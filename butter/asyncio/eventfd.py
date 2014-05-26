#!/usr/bih/env python
from ..eventfd import Eventfd as _Eventfd
from collections import deque as _deque
import asyncio as _asyncio


class Eventfd_async:
    def __init__(self, inital_value=0, flags=0, *, loop=None):
        self._loop = loop or _asyncio.get_event_loop()
        self._eventfd = _Eventfd(inital_value, flags)
        self._getters = _deque()
        self._value = inital_value
        
    def increment(self, value=1):
        """Increment the counter by the specified value

        :param int value: The value to increment the counter by (default=1)
        """
        self._eventfd.increment(value)

    @_asyncio.coroutine
    def wait(self):
        """Read the current value of the counter and zero the counter

        Returns
        --------
        :return: The current count of the timer
        :rtype: int
        """
        self._loop.add_reader(self._eventfd.fileno(), self._read_event)

        waiter = _asyncio.Future(loop=self._loop)

        self._getters.append(waiter)

        return (yield from waiter)

    def get_last(self):
        return self._value

    def _consume_done_getters(self):
        # Delete waiters at the head of the get() queue who've timed out.
        while self._getters and self._getters[0].done():
            self._getters.popleft()

    def _read_event(self):
        value = self._eventfd.read_event()
        self._put_event(value)
    
    def _put_event(self, value):
        """Put an item into the queue without blocking.

        If no free slot is immediately available, raise QueueFull.
        """
        self._loop.remove_reader(self._eventfd.fileno())

        self._consume_done_getters()

        for getter in self._getters:
            getter.set_result(value)

        self._value = value

    def close(self):
        self._eventfd.close()

    def __repr__(self):
        fd = self._eventfd._fd or 'closed'
        return "<{} fd={} value={}>".format(self.__class__.__name__, fd, self._value)

def _watcher(loop):
    ev = Eventfd_async(10)
    print(ev)
    print('Waiting read:', (yield from ev.wait()))
    ev.increment(2)
    ev.increment(2)
    print('Waiting read:', (yield from ev.wait()))
    print('No wait read:', ev.get_last())
    ev.close()
    print(ev)
    print('done')

def _main():
    import logging
    import asyncio
    
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())
    
    loop = asyncio.get_event_loop()
    
    from asyncio import Task
    task = Task(_watcher(loop))
    
    loop.run_until_complete(task)
    

if __name__ == "__main__":
    _main()
