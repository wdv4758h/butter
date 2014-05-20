#!/usr/bih/env python
from os import read as _read, write as _write, close as _close
from ..eventfd import eventfd, _ffi
from collections import deque
import asyncio


class Eventfd:
    def __init__(self, inital_value=0, flags=0, *, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._fd = eventfd(inital_value, flags)
        self._getters = deque()
        self._value = inital_value
        
    def increment(self, value=1):
        """Increment the counter by the specified value

        :param int value: The value to increment the counter by (default=1)
        """
        packed_value = _ffi.new('uint64_t[1]', (value,))
        packed_value = _ffi.buffer(packed_value)[:]
        _write(self._fd, packed_value)

    @asyncio.coroutine
    def read(self):
        """Read the current value of the counter and zero the counter

        Returns
        --------
        :return: The current count of the timer
        :rtype: int
        """
        self._loop.add_reader(self._fd, self._read_event)

        waiter = asyncio.Future(loop=self._loop)

        self._getters.append(waiter)

        return (yield from waiter)

    def read_nowait(self):
        return self._value

    def _consume_done_getters(self):
        # Delete waiters at the head of the get() queue who've timed out.
        while self._getters and self._getters[0].done():
            self._getters.popleft()

    def _read_event(self):
        data = _read(self._fd, 8)
        value = _ffi.new('uint64_t[1]')
        _ffi.buffer(value, 8)[0:8] = data

        self._put_event(value[0])
    
    def _put_event(self, value):
        """Put an item into the queue without blocking.

        If no free slot is immediately available, raise QueueFull.
        """
        self._loop.remove_reader(self._fd)

        self._consume_done_getters()

        for getter in self._getters:
            getter.set_result(value)

        self._value = value

    def close(self):
        _close(self._fd)

def watcher(loop):
    ev = Eventfd(10)
    print('Waiting read:', (yield from ev.read()))
    ev.increment(2)
    ev.increment(2)
    print('Waiting read:', (yield from ev.read()))
    print('No wait read:', ev.read_nowait())
    print('done')

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
