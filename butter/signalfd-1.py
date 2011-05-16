#!/usr/bin/env python

from time import sleep
import select
import signal
import fcntl
import os

pipe_r, pipe_w = os.pipe()
flags = fcntl.fcntl(pipe_w, fcntl.F_GETFL, 0)
flags = flags | os.O_NONBLOCK
flags = fcntl.fcntl(pipe_w, fcntl.F_SETFL, flags)

signal.set_wakeup_fd(pipe_w)
# Mask out signal handler
signal.signal(signal.SIGALRM, lambda x,y: None)
# Set up a signal to repeat every 2 seconds
signal.setitimer(signal.ITIMER_REAL, 2, 2)

poller = select.epoll()
poller.register(pipe_r, select.EPOLLIN)

# Begin Bad joke
print "Main screen turn on"
while True:
	try:
		events = poller.poll()
		for fd, flags in events:
			print "We get Signal"
			# read a single event
			os.read(pipe_r, 1)
	except IOError:
		pass
