#!/usr/bin/env python
"""AIO implementation for POSIX OSs

TODO:
work out wtf a size_t is
detect and handle xxx64 func calls and padding
"""

from ctypes.util import find_library
from ctypes import c_int, c_int64, c_long, c_char, c_char, c_void_p, POINTER, sizeof
# Pre 2.7 did not have this defined
try:
	from ctypes import c_ssize_t
except ImportError:
	c_ssize_t = c_int
import ctypes
import errors

class sigval(ctypes.Union):
	_defined = "/usr/include/asm-generic/siginfo.h"
	_fields_ = (("sigval_int", c_int),
				("sigval_ptr", c_void_p))

# Calculated in /usr/include/asm-generic/siginfo.h
ARCH_SIGEV_PREAMBLE_SIZE = sizeof(c_int) * 2 + sizeof(sigval)
SIGEV_MAX_SIZE = 64
SIGEV_PAD_VALUE = (SIGEV_MAX_SIZE - ARCH_SIGEV_PREAMBLE_SIZE) / sizeof(c_int)

class sigevent_sigev_thread(ctypes.Union):
	_defined = "/usr/include/asm-generic/siginfo.h"
	_fields_ = (("_function", POINTER(sigval)),
				("_attribute", c_void_p))

class sigevent_sigev_un(ctypes.Union):
	_defined = "/usr/include/asm-generic/siginfo.h"
	_fields_ = (("_pad", c_int * SIGEV_PAD_VALUE), # Dont ask
				("_tid", c_int),
				("_sigev_thread", sigevent_sigev_thread))

#class sigevent(ctypes.Structure):
#	"""man sigevent"""
#	_defined = "/usr/include/asm-generic/siginfo.h"
#	_fields_ = (("sigev_notify", c_int),
#				("sigev_signo", c_int),
#				("sigev_value", sigval), # see above union
#				# These map onto sigevent_sigev_un
#				("sigev_notify_function", c_void_p), # maps to sigevent_sigev_un._sigev_thread._function
#				("sigev_notify_attributes", c_void_p), # maps to same as above but _attribute
#				("sigev_notify_thread_id", c_int)) # maps to _tid in sigevent_sigev_un

class sigevent(ctypes.Structure):
	_defined_ = "/usr/include/asm-generic/siginfo.h"
	_fields_ = (("sigev_value", sigval), 
				("sigev_signo", c_int),
				("sigev_notfiy", c_int),
				("_sigev_un", sigevent_sigev_un))

class timespec(ctypes.Structure):
	_defined = ""
	_fileds_ = ()

# Taken from /usr/include/asm-generic/siginfo.h
SIGEV_NONE = 0
SIGEV_SIGNAL = 1
SIGEV_THREAD = 2
SIGEV_THREAD_ID = 4

# Subtle api changes
USE_FILE_OFFSET64 = True
off64_t = c_int64
if USE_FILE_OFFSET64 == True:
	off_t = off64_t
else:
	off_t = c_long

class aiocb(ctypes.Structure):
	_defined = "/usr/include/aio.h"
	_fields_ = (("aio_fildes", c_int),
				("aio_lio_opcode", c_int),
				("aio_reqprio", c_int),
				("aio_buf", c_void_p), # volitile mutable buffer
				("aio_nbytes", c_int),
				("aio_sigevent", sigevent), # sigevent struct
				# Kernel internal accounting
				("__next_prio", c_void_p), #pointer to next block
				("__abs_prio", c_int),
				("__policy", c_int),
				("__error_code", c_int),
				("__return_value", c_ssize_t), #__size_t
				("aio_offset", off_t), #__off_t (or __off_t64)
				# Check this, may need to provide 2 _field_ versions
				# that are called depending on OFFSET64
				("__pad", c_char * (sizeof(off64_t) - sizeof(off_t))),
				# Padding
				("__unused", c_char * 32))


class aioinit(ctypes.Structure):
	_defined = "/usr/include/aio.h"
	_fields_ = (("aio_threads", c_int), # Maximum number of threads
				("aio_num", c_int), # Number of concurrent accesesses
				("aio_locks", c_int), # Unused
				("aio_usedba", c_int), # Unused
				("aio_debug", c_int), # Unused
				("aio_numusers", c_int), # Unused
				("aio_idle_time", c_int), # number of seconds before idle thread
				("aio_reserved", c_int)) # for future use

class AIOErrror(errors.CError):
	def __repr__(self):
		return "<AIOError {0}: {1}>".format(self.name, sel.msg)

def aio_error(val, func, args):
	"""Generic AIO Error handling"""
	errors.check_error(val, AIOError)

def aio_error_error(val, func, args):
	"""Error handling for the aio_error function"""
	if val < 0:
		num, name, msg = get_error(val)
		raise AIOError(num, name, msg)

# Enums
# Taken from /usr/include/aio.h
AIO_CANCELED, AIO_NOTCANCELED, AIO_ALLDONE = range(3)
LIO_READ, LIO_WRITE, LIO_NOP = range(3)
LIO_WAIT, LIO_NOWAIT = range(2)

libc = ctypes.CDLL(find_library("c"))
librt = ctypes.CDLL(find_library("rt"))

_aio_init = librt.aio_init
_aio_init.argtypes = (POINTER(aioinit),)
_aio_init.restype = None # XXX is this alright?
_aio_init.errcheck = aio_error

_lio_listio = librt.lio_listio
_lio_listio.argtypes = ()
_lio_listio.restypr = c_int
_lio_listio.errcheck = aio_error

_aio_read = librt.aio_read
_aio_read.argtypes = (POINTER(aiocb),)
_aio_read.restype = c_int
_aio_read.errcheck = aio_error

_aio_write = librt.aio_write
_aio_write.argtypes = (POINTER(aiocb),)
_aio_write.restype = c_int 
_aio_write.errcheck = aio_error

_aio_error = librt.aio_error
_aio_error.argtypes = (POINTER(aiocb),)
_aio_error.restype = c_int
_aio_error.errcheck = aio_error_error

_aio_return = librt.aio_return
_aio_return.argtypes = (POINTER(aiocb),)
_aio_return.restype = c_ssize_t
_aio_init.errcheck = aio_error

_aio_cancel = librt.aio_cancel
# args: fd, aiocb block
_aio_cancel.argtypes = (c_int, POINTER(aiocb))
_aio_cancel.restype = c_int
_aio_cancel.errcheck = aio_error

_aio_suspend = librt.aio_suspend
# first arg is complex, arg is a list of pointers of type aiocb, pointers can be None
_aio_suspend.argtypes = (POINTER(aiocb), c_int, POINTER(timespec))
_aio_suspend.restype = c_int
_aio_suspend.errcheck = aio_error

_aio_fsync = librt.aio_fsync
_aio_fsync.argtypes = (c_int, aiocb)
_aio_fsync.restype = c_int
_aio_fsync.errcheck = aio_error

from os import O_SYNC, O_DSYNC

class AIORequest(object):
	def init(self, fd, offset, data="", size=4096):
		self.data = data
		data_len = len(data)
		if data_len > 0:
			self.size = data_len
			self.operation = "write"
			# Suppress trailing "\n" (try and fit in 4k where avalible)
			self.buffer = ctypes.create_string_buffer(data, data_len)
		else:
			self.size = size
			self.operation = "read"
			self.buffer = ctypes.create_string_buffer(size)


	def __repr__(self):
		return "<AIORequest fd={0}, type={1}, offset={2}, size={3}>".format(self.fd, self.operation, self.offset, self.size)

class AIOManager(object):
	def __init__(self):
		pass

# manager class has instances such as open()
# open returns a channel not a file, a file is
# returned on the chanel when open completes

# fsync on the file object calls the proxy which 
# returns a channel, the proxy registers an event 
# and a callback channel 
# for sync operation block on channel for async 
# behavior contiue work and let GC do all the 
# work of removing

if __name__ == "__main__":
	pass
