#!/usr/bih/env python
from ..fanotify import FAN_CLASS_NOTIF as _FAN_CLASS_NOTIF
from ..fanotify import Fanotify as _Fanotify
from collections import deque as _deque
from os import O_RDONLY as _O_RDONLY
import asyncio as _asyncio

class Fanotify_async:
    def __init__(self, flags=_FAN_CLASS_NOTIF, event_flags=_O_RDONLY, *, loop=None, maxsize=0):
        self._loop = loop or _asyncio.get_event_loop()
        self._maxsize = maxsize

        self._fanotify = fanotify = _Fanotify(flags, event_flags)

        self._getters = _deque()
        self._events = _deque()
        
    def watch(self, path, event_mask, flags=0, dfd=0):
        self._fanotify.watch(flags, event_mask, path, dfd)

    def ignore(self, path, event_mask, flags=0, dfd=0):
        self._fanotify.ignore(flags, event_mask, path, dfd)
         
    @_asyncio.coroutine
    def get_event(self):
        """Remove and return an item from the queue.

        If you yield from get(), wait until a item is available.
        """
        # if event then consume it
        # otherwise register for fd callback
        #   add self to callback queue
        if self._events:
            return self._get()
        else:
            self._loop.add_reader(self._fanotify.fileno(), self._read_event)

            waiter = _asyncio.Future(loop=self._loop)

            self._getters.append(waiter)

            return (yield from waiter)

    def get_event_nowait(self):
        """Remove and return an item from the queue.

        Return an item if one is immediately available, else raise QueueEmpty.
        """
        self._consume_done_putters()
        if self._events:
            return self._get()
        else:
            raise QueueEmpty

    @property
    def maxsize(self):
        """Number of items allowed in the queue."""
        return self._maxsize

    def _consume_done_getters(self):
        # Delete waiters at the head of the get() queue who've timed out.
        while self._getters and self._getters[0].done():
            self._getters.popleft()

    def _get(self):
        return self._events.popleft()

    def _put(self, item):
        self._events.append(item)

    def _read_event(self):
        """Read an event from the inotify fd and place it in the queue"""
        for event in self._fanotify.read_events():
            self._put_event(event)
        
    def _put_event(self, event):
        """Put an item into the queue without blocking.

        If no free slot is immediately available, raise QueueFull.
        """
        self._consume_done_getters()
        if self._getters:
            assert not self._events, ('queue non-empty, why are getters waiting?')

            getter = self._getters.popleft()

            # Use _put and _get instead of passing item straight to getter, in
            # case a subclass has logic that must run (e.g. JoinableQueue).
            self._put(event)
            getter.set_result(self._get())
        elif self._maxsize > 0 and self._maxsize == self.qsize():
            self.loop.remove_reader(self._fanotify.fileno())
            raise QueueFull
        else:
            # No listeners so queue up the data and stop 
            # listening for events on the FD
            self._put(event)
            self._loop.remove_reader(self._fanotify.fileno())

    def qsize(self):
        """Returns the current size of the Queue
        
        Returns
        --------
        int: The current length of the queue
        """
        return len(self._events)
    
    def close(self):
        self._fanotify.close()

    def __repr__(self):
        fd = self._fanotify._fd or "closed"
        return "<{} fd={}>".format(self.__class__.__name__, fd)

def _watcher(loop):
    from ..fanotify import FAN_MODIFY, FAN_ONDIR, FAN_ACCESS, FAN_EVENT_ON_CHILD, FAN_OPEN, FAN_CLOSE
    
    fanotify = Fanotify_async(loop=loop)
    event_mask = FAN_MODIFY|FAN_ONDIR|FAN_ACCESS|FAN_EVENT_ON_CHILD|FAN_OPEN|FAN_CLOSE
    wd = fanotify.watch('/tmp', event_mask)

    print(fanotify)

    print("Listening for events on /tmp")
    for i in range(5):
        event = yield from fanotify.get_event()
        print(event)
        event.close()

    fanotify.ignore('/tmp', event_mask)
    print('done')

    event = yield from fanotify.get_event()
    print(event)
    event.close()

    fanotify.close()
    print(fanotify)

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
