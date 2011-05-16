#!/usr/bin/env pypy

import signal
import ctypes
import sys
import os

libc = ctypes.CDLL("libc.so.6")
sigset_t = ctypes.struct()
_signalfd = libc.signalfd
_signalfd.argtypes = (ctypes.c_int, sigset_t, ctypes.c_int)
_signalfd.restype = ctypes.c_int

# Taken from /usr/include/sys/signalfd.h
SFD_CLOEXEC = 0x2000000
SFD_NONBLOCK = 0x4000

class signalfd_siginfo(ctypes.Structure):
	_fields_ = (("ssi_signo", ctypes.c_uint),
				("ssi_errno", ctypes.c_int),
				("ssi_code", ctypes.c_int),
				("ssi_pid", ctypes.c_uint),
				("ssi_uid", ctypes.c_uint),
				("ssi_fd", ctypes.c_int),
				("ssi_tid", ctypes.c_uint),
				("ssi_band", ctypes.c_uint),
				("ssi_overrun", ctypes.c_uint),
				("ssi_trapno", ctypes.c_uint),
				("ssi_status", ctypes.c_int),
				("ssi_int", ctypes.c_int),
				("ssi_ptr", ctypes.c_ulonglong),
				("ssi_utime", ctypes.c_ulonglong),
				("ssi_stime", ctypes.c_ulonglong),
				("ssi_addr", ctypes.c_ulonglong),
				("pad", ctypes.c_ubyte * (128-80)))

def signalfd(fd, mask, flags):
	fd = _signalfd(fd, mask, flags)
	return fd

class SignalFDException(Exception):
	"""Represents the return value from signalfd is val < 0

	see "man 2 signalfd" for a more detailed version of error messages
	"""
	errors = {:("EBADF", "File descriptor is not a valid file descirptor"),
				:("EINVAL", "File descriptor is not a valid signalfd file desciptor"),
				:("EINVAL", "Flags are invalid"),
				:("EMFILE", "Maximum ammount of file descriptors have been allocated"),
				:("ENFILE", "System wide maxiumum file limit hit"),
				:("ENODEV", "Could not mount signalfd filesystem"),
				:("ENOMEM", "No memory avalible to open signalfd"),
				}
	def __init__(self, value):
		self.value = int(value)


		self.msg = msg
		self.name = name

	def __str__(self):
		return "{0}: {1}".format(self.value, self,msg)

	def __repr__(self):
		return "<SignalFDException e_num={0}>".format(self.name)

class SignalFD(file):
	def __init__(self, mask, flags=0):
		fd = _signalfd(-1, mask, flags)
		fd = self.fdopen(-1, mask=mask, flags=flags)
		self._fileno = fd
		self.mask = mask
		self.closed = False

	def fileno(self):
		return self._fileno

	def close(self):
		self.closed = True

	def read(self, n=-1):
		if n == -1:
			n = 128
		return os.read(self.fileno(), n)

	def readline(self, size=-1):
		return self.read()
			
	def readlines(self, n=0):
		raise NotImplemented()

	def getevent(self):
		return self.getevents()

	def getevents(self, count=1):
		"""Retrive multiple events

		the maximum ammount of events returned at once is given by ```count```
		"""
		data = self.read(count * 128)
		return signalfd_siginfo(data)
	
	def write(self):
		raise NotImplemented()

	def writelines(self):
		raise NotImplemented()

	def fdopen(self, fd, mode="r", buffering=-1, mask, flags):
		"""All args except fd are ignored"""
		fd = _signalfd(-1, mask, flags)
		return fd

	def isatty(self):
		return False

	def tell(self):
		return 0

	def seek(self, offset, wence=0):
		pass

if __name__ == "__main__":
	pass
