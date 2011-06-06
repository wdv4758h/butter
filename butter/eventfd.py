#!/usr/bin/env pypy
"""Module for creating and manipulating an eventfd fd

TODO:
* Filelike object (unbuffered)
"""
import ctypes
import struct
import os

llong = struct.Struct("Q")

libc = ctypes.CDLL("libc.so.6")
_eventfd = libc.eventfd
_eventfd.argtypes = (ctypes.c_int, ctypes.c_int)
_eventfd.restype = ctypes.c_int

def eventfd(count=0, flags=0):
	"""open and return a file discriptor refering to a new eventfd interface

	to convert to a normal file, use os.fdopen(). at this time it is recomended
	to use os.write and os.read instead of the file object

	please ensure all reads and writes are 8bytes in length and in machine endian
	for formatting the long long (64bit)
	"""
	return _eventfd(count, flags)

class EventFD(file):
	def __init__(self, count=0, flags=0):
		self._fileno = eventfd(count, flags)
		self.closed = False

	def fileno(self):
		return self._fileno

	def close(self):
		self.closed = True
		os.close(self.fileno())

	def read(self):
		val = os.read(self.fileno(), 8)
		return llong.unpack(val)[0]

	def readlines(self):
		return (self.read(),)

	def write(self, val):
		val = llong.pack(int(val))
		os.write(self.fileno(), val)

	def writelines(self, lines):
		for i in lines:
			self.write(i)

	def tell(self):
		return 0

	def isatty(self):
		return False

	def seek(self):
		pass

if __name__ == "__main__":
	import sys

	event = eventfd(flags=os.O_NONBLOCK)

	pid = os.fork()
	if pid == 0:
		# Child
		for i in range(1, 21): # sum(range(1,21) = 210)
			data = llong.pack(i)
			fragment = data
			sent = 0
			# Whole writes are not
			while sent < len(data):
				count = os.write(event, data)
				sent += count
				fragment = data[sent:]
				print("Write {0}".format(i))
		print("Child Done")
		sys.exit(0)
	else:
		# Parent
		os.wait()
		events = 0

		# There could be multiple items in the queue (i have seen this happen
		# if the process writing is the same as the process reading)
		# in this case, exaust the queue before continuing
		try:
			while True:
				events += llong.unpack(os.read(event, 8))[0]
		except OSError:
			pass

		print("All children have returned")
		print("events = {0}".format(events))
	sys.exit(0)
