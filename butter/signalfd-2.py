#!/usr/bin/env python
"""A set_wakeup_fd clone with slightly more functionality than offered by the standard library"""

from time import sleep
import select
import signal
import fcntl
import os

def handle_signal(sig, fd, func=lambda x,y: False):
	"""Automatically send the signal number down a pipe when a signal occurs

	This function will automatically change the write end to non blocking mode
	and set up the signal handler for you

	If your signal handler (optionally passed in as func) returns True then the
	write to the pipe will be suppressed
	"""
	flags = fcntl.fcntl(fd, fcntl.F_GETFL, 0)
	flags = flags | os.O_NONBLOCK
	flags = fcntl.fcntl(fd, fcntl.F_SETFL, flags)
	def signalfd_handler(signal, frame):
		"""Defined inside handle_signal"""
		val = func(signal, frame)
		if not val:
			os.write(fd, chr(signal))

	signal.signal(sig, signalfd_handler)

pipe_r, pipe_w = os.pipe()

handle_signal(signal.SIGALRM, pipe_w)
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
			print "We get Signal:", ord(os.read(pipe_r, 1))
	except IOError:
		pass
