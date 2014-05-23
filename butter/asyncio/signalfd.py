#!/usr/bih/env python
from ..signalfd import Signalfd as _Signalfd
from collections import deque as _deque
import asyncio as _asyncio

class Signalfd_async:
    def __init__(self, signals=[], flags=0, *, loop=None):
        self._loop = loop or _asyncio.get_event_loop()
        self._signalfd = _Signalfd(signals, flags)
        self._getters = _deque()
        self.enable = self._signalfd.enable
        self.enable_all = self._signalfd.enable_all
        self.disable = self._signalfd.disable
        self.disable_all = self._signalfd.disable_all
            
    @_asyncio.coroutine
    def wait(self):
        """Wait for the timer to expire, returning how many events have 
        elappsed since the last call to wait()

        Returns
        --------
        :return: The current count of the timer
        :rtype: int
        """
        self._loop.add_reader(self._signalfd.fileno(), self._read_event)

        waiter = _asyncio.Future(loop=self._loop)

        self._getters.append(waiter)

        return (yield from waiter)

    def _consume_done_getters(self):
        # Delete waiters at the head of the get() queue who've timed out.
        while self._getters and self._getters[0].done():
            self._getters.popleft()

    def _read_event(self):
        value = self._signalfd._read_signal()
        self._put_event(value)
    
    def _put_event(self, value):
        """Put an item into the queue without blocking.

        If no free slot is immediately available, raise QueueFull.
        """
        self._loop.remove_reader(self._signalfd.fileno())

        self._consume_done_getters()

        for getter in self._getters:
            getter.set_result(value)

    def close(self):
        self._signalfd.close()

def watcher(loop):
    from asyncio import sleep
    from ..signalfd import pthread_sigmask, SIG_BLOCK
    import signal
    import os
    
    sfd = Signalfd_async(signal.SIGUSR1)
    pthread_sigmask(SIG_BLOCK, signal.SIGUSR1)
    sfd.enable(signal.SIGUSR1)
    
    count = 5
    
    for i in range(count):
        os.kill(os.getpid(), signal.SIGUSR1)
        sig = yield from sfd.wait()
        print(sig)

    print("Got all 5 signals")


def main():
    import logging
    import asyncio

    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())
    
    loop = asyncio.get_event_loop()
    
    from asyncio import Task
    task = Task(watcher(loop))
    
    loop.run_until_complete(task)


if __name__ == "__main__":
    main()
