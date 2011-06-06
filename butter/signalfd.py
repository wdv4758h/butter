#!/usr/bin/env pypy
"""SignalFD: Recive signal notifcations over a file descriptor

Normmaly used with poll/select to handle signal notifcation in the main loop
instead of in callback functions
"""
from ctypes import c_ubyte, c_int, c_uint, c_ulong, c_ulonglong, c_void_p
from ctypes.util import find_library
import errors
import ctypes
import signal
import sys
import os

class signalfd_siginfo(ctypes.Structure):
	"""A signalfd_siginfo block as defined by the signalfd man page ("man 2 signalfd")

	This is a 128 byte structure read from the file descriptor opened with signalfd
	"""
	_defined = "/usr/include/sys/signalfd.h"
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
				# pad is used to pad the structure out to 128 bytes for future expansion
				("pad", c_ubyte * (128-80)))

	def __repr__(self):
		return "<signalfd_siginfo signal={0}, pid={1}, uid={2}>".format(self.ssi_signo, self.ssi_pid, self.ssi_uid)

	def __str__(self):
		signal_names = [x for x in signal.__dict__ if x.startswith("SIG")]
		signal_name = [x for x in signal_names if getattr(signal, x) == self.ssi_signo][0]
		return signal_name

class sigset_t(ctypes.Structure):
	"""A sigset_t structure for masking signals and marking them as blocked"""
	_defined = "/usr/include/bits/sigset.h"
	## 32 chosen by calculating by hand the code in 
	## /usr/include/bits/sigset.h
	## unsigned long int assumed to be 64 bits
	_fields_ = (("__val", c_ulong * 32),)

libc = ctypes.CDLL(find_library("c"))

_signalfd = ctypes.CFUNCTYPE(c_int, c_int, ctypes.POINTER(sigset_t), c_int)
__param_flags = ((0, "fd"), (0, "mask"), (0, "flags", 0))
_signalfd = _signalfd(("signalfd", libc), __param_flags)
_signalfd.restype = c_int

# Taken from /usr/include/sys/signalfd.h
SFD_CLOEXEC = 0x2000000
SFD_NONBLOCK = 0x4000

SIG_BLOCK = 0
SIG_UNBLOCK = 1
SIG_SETMASK = 2

def signalfd_error(val, func, args):
	"""Error wrapper for signalfd"""
	errors.check_error(val)	
# Set the error handler
_signalfd.errcheck = signalfd_error

def signalfd(fd, signals, flags=0):
	"""A wrapper for signalfd that handles pretty error printing

	Note: it is recomended to use the SignalFD object instead of this
	function
	"""
	# Make signals "Blocked"
	sigset = make_sigset_t(signals)
	libc.sigprocmask(SIG_BLOCK, sigset, None)

	fd = _signalfd(fd, sigset, flags)
	return fd

def make_sigset_t(signals):
	"""Add Signals to a sigset_t structure and return the new structure"""
	sigset = sigset_t()
	libc.sigemptyset(sigset)

	for sig in signals:
		libc.sigaddset(sigset, sig)

	return sigset

sigprocmask = libc.sigprocmask
sigprocmask.argtypes = [c_int, ctypes.POINTER(sigset_t), c_void_p]
sigprocmask.restype = c_int

sigemptyset = libc.sigemptyset
sigemptyset.argtypes = [ctypes.POINTER(sigset_t)]
sigemptyset.restype = c_int

sigaddset = libc.sigaddset
sigaddset.argtypes = [ctypes.POINTER(sigset_t), c_int]
sigaddset.restype = c_int

######################
# Event-like objects #
######################
class SignalFDError(errors.CError):
	"""Represents the return value from signalfd is val < 0

	see "man 2 signalfd" for a more detailed version of error messages
	"""
	def __repr__(self):
		return "<SignalFDException err_num={0}>".format(self.name)

class SignalFD(file):
	"""An Event like object that represents a file like object"""
	closed = False
	def __init__(self, mask, flags=0):
		fd = self.fdopen(1, mask=mask, flags=flags)
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

		returns a list of signalfd_siginfo objects
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
	sigmask = (signal.SIGUSR1, signal.SIGUSR2)

	signal.signal(signal.SIGUSR1, signal.SIG_IGN)
	signal.signal(signal.SIGUSR2, signal.SIG_IGN)

	s = SignalFD(sigmask)

	print "-------"
	# test if we actually wait on fd or if signal module kicks in
	for sig in (signal.SIGUSR1, signal.SIGUSR2):
		os.kill(os.getpid(), sig)
		print("Waiting on event:")
		sig = s.getevent()
		print("Event Recived: " + str(sig))
		print(repr(sig))
		print "-------"
