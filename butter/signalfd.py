#!/usr/bin/env pypy

from errors import get_error
from ctypes import c_ubyte, c_int, c_uint, c_ulong, c_ulonglong, c_void_p
import ctypes
import signal
import sys
import os

class signalfd_siginfo(ctypes.Structure):
	_fields_ = (("ssi_signo", c_uint),
				("ssi_errno", c_int),
				("ssi_code", c_int),
				("ssi_pid", c_uint),
				("ssi_uid", c_uint),
				("ssi_fd", c_int),
				("ssi_tid", c_uint),
				("ssi_band", c_uint),
				("ssi_overrun", c_uint),
				("ssi_trapno", c_uint),
				("ssi_status", c_int),
				("ssi_int", c_int),
				("ssi_ptr", c_ulonglong),
				("ssi_utime", c_ulonglong),
				("ssi_stime", c_ulonglong),
				("ssi_addr", c_ulonglong),
				("pad", c_ubyte * (128-80)))

class sigset_t(ctypes.Structure):
	## 32 chosen by calculating by hand the code in 
	## /usr/include/bits/sigset.h
	_fields_ = (("__val", c_ulong * 32),)

libc = ctypes.CDLL("libc.so.6")
#_signalfd = ctypes.CFUNCTYPE(c_int, c_int, sigset_t, c_int, use_errno=True)
_signalfd = ctypes.CFUNCTYPE(c_int, c_int, c_void_p, c_int, use_errno=True)
#_signalfd = ctypes.CFUNCTYPE(c_int, c_int, c_void_p, c_int)
#__param_flags = ((1, "fd", -1), (2, "mask"), (1, "flags", 0))
__param_flags = ((0,), (0,), (0,))
_signalfd = _signalfd(("signalfd", libc), __param_flags)
#_signalfd = libc.signalfd
#_signalfd.argtypes = (c_int, sigset_t, c_int)
#_signalfd.restype = c_int

# Taken from /usr/include/sys/signalfd.h
SFD_CLOEXEC = 0x2000000
SFD_NONBLOCK = 0x4000

def signalfd(fd, mask, flags):
	fd = _signalfd(fd, mask, flags)
	if fd < 0:
		errnum = c_int.in_dll(libc, "errno").value
		raise SignalFDError(errnum)
	return fd

def make_sigset_t(signals):
	sigset = sigset_t()
	ad_sigset = ctypes.addressof(sigset)
	libc.sigemptyset(ad_sigset)

	for sig in signals:
		libc.sigaddset(ad_sigset, sig)

	return sigset

######################
# Event-like objects #
######################
class SignalFDError(Exception):
	"""Represents the return value from signalfd is val < 0

	see "man 2 signalfd" for a more detailed version of error messages
	"""
	def __init__(self, value):
		self.value, self.name, self.msg = get_error(value)

	def __str__(self):
		return "{0} {1}: {2}".format(self.value, self.name, self.msg)

	def __repr__(self):
		return "<SignalFDException err_num={0}>".format(self.name)

class SignalFD(file):
	closed = False
	def __init__(self, mask, flags=0):
		fd = self.fdopen(-1, mask=mask, flags=flags)
		self._fileno = fd
		self.mask = mask

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
		return self.getevents()[0]

	def getevents(self, count=1):
		"""Retrive multiple events

		the maximum ammount of events returned at once is given by ```count```
		"""
		data = self.read(count * 128)

		l = []
		for i in range(len(data) / 128):
			i *= 128
			buf = ctypes.create_string_buffer(data[i:i+128], 128)
			event = signalfd_siginfo.from_address(ctypes.addressof(buf))
			l.append(event)
			
		return l
	
	def write(self):
		raise NotImplemented()

	def writelines(self):
		raise NotImplemented()

	@staticmethod
	def fdopen(fd, mode="r", buffering=-1, mask=0, flags=0):
		"""All args except fd are ignored"""
		fd = signalfd(fd, mask, flags)
		return fd

	def isatty(self):
		return False

	def tell(self):
		return 0

	def seek(self, offset, wence=0):
		pass

if __name__ == "__main__":
	sigusr = signal.SIGUSR1

	signal.signal(sigusr, signal.SIG_IGN)

	mask = make_sigset_t((sigusr,))
	libc.sigprocmask(0, ctypes.byref(mask), None)
	s = SignalFD(ctypes.byref(mask))

#	os.kill(os.getpid(), sigusr)
	print("Waiting on event:")
	s.getevent()
	print("Event Recived")
