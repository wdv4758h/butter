#!/usr/bih/env python
from butter.inotify import inotify_init, inotify_add_watch, inotify_rm_watch, str_to_events, IN_ALL_EVENTS
from butter.utils import get_buffered_length
from collections import deque
from os import read
from os import O_RDONLY
import asyncio


class Inotify:
    def __init__(self, flags=0, *, loop=None, maxsize=0):
        self._loop = loop or asyncio.get_event_loop()
        self._maxsize = maxsize
        self._fd = inotify_init(flags)
        self._getters = deque()
        self._events = deque()
        
    def watch(self, path, mask):
        return inotify_add_watch(self._fd, path, mask)

    def ignore(self, wd):
        inotify_rm_watch(self._fd, wd)
         
    @asyncio.coroutine
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
            self._loop.add_reader(self._fd, self._read_event)

            waiter = asyncio.Future(loop=self._loop)

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
        buf_len = get_buffered_length(self._fd)
        raw_events = read(self._fd, buf_len)
                
        events = str_to_events(raw_events)

        for event in events:
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
            self.loop.remove_reader(self._fd)
            raise QueueFull
        else:
            # No listeners so queue up the data and stop 
            # listening for events on the FD
            self._put(event)
            self._loop.remove_reader(self._fd)

    def qsize(self):
        """Returns the current size of the Queue
        
        Returns
        --------
        int: The current length of the queue
        """
        return len(self._events)
        

def watcher(loop):
    inotify = Inotify(loop=loop)
    wd = inotify.watch('/tmp', IN_ALL_EVENTS)

    for i in range(5):
        event = yield from inotify.get_event()
        print(event)

    inotify.ignore(wd)
    print('done')

    event = yield from inotify.get_event()
    print(event)


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
