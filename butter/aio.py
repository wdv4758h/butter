#!/usr/bin/env python
"""AIO implementation for POSIX OSs

TODO:
fill in fields in Structures
struure for sigevent
work out wtf a size_t is
# detect and handle xxx64 func calls and padding
"""

from ctypes.util import find_library
from ctypes import c_int, c_char c_void_p
import cytpes

_ARCH_SIGEV_PREAMBLE_SIZE(len(c_int) * 2 + len(sigval))
_SIGEV_MAX_SIZE = 64
_SIGEV_PAD_VALUE = (SIGEV_MAX_SIZE - ARCH_SIGEV_PREAMBLE_SIZE) / len(c_int)

class sigval(ctypes.Union):
	_fields_ = (("sigval_int", c_int),
				("sigval_ptr", c_void_p))

class sigevent_sigev_thread(ctypes.Union):
	_fields_ = (("_function", c_void_p),
				("_attribute", c_void_p))

class sigevent_sigev_un(ctypes.Union):
	_fields_ = (("_pad", c_int * _SIGEV_PAD_VALUE), # Dont ask
				("_tid", c_int),
				("_sigev_thread", sigevent_sigev_thread)

#class sigevent(ctypes.Structure):
#	"""man sigevent"""
#	_fields_ = (("sigev_notify", c_int),
#				("sigev_signo", c_int),
#				("sigev_value", sigval), # see above union
#				# These map onto sigevent_sigev_un
#				("sigev_notify_function", c_void_p), # maps to sigevent_sigev_un._sigev_thread._function
#				("sigev_notify_attributes", c_void_p), # maps to same as above but _attribute
#				("sigev_notify_thread_id", c_int)) # maps to _tid in sigevent_sigev_un

class sigevent(ctypes.Structure):
	_fields_ = (("sigev_value", sigval), 
				("sigev_signo", c_int),
				("sigev_notfiy", c_int),
				("_sigev_un", sigevent_sigev_un))

# Taken from /usr/include/asm-generic/siginfo.h
SIGEV_NONE = 0
SIGEV_SIGNAL = 1
SIGEV_THREAD = 2
SIGEV_THREAD_ID = 4


class aiocb(cytpes.Structure):
	_fields_ = (("aio_fildes", c_int),
				("aio_lio_opcode", c_int),
				("aio_reqprio", c_int),
				("aio_buf", c_void_p) # volitile mutable buffer
				("aio_nbytes", c_int),
				("aio_sigevent", sigevent) # sigevent struct
				# Kernel internal accounting
				("__next_prio", c_void_p)#pointer to next block
				("__abs_prio", c_int),
				("__policy", c_int),
				("__error_code", c_int),
				("__return_value", )#__size_t
				("aio_offset",)#__off_t (or __off_t64)
				# Padding
				("__unused", c_char * 32))

class aioinit(ctypes.Structure):
	_fields_ = (("aio_threads", c_int), # Maximum number of threads
				("aio_num", c_int), # Number of concurrent accesesses
				("aio_locks", c_int), # Unused
				("aio_usedba", c_int), # Unused
				("aio_debug", c_int), # Unused
				("aio_numusers", c_int), # Unused
				("aio_idle_time", c_int), # number of seconds before idle thread
				("aio_reserved", c_int)) # for future use

libc = ctypes.CDLL(find_library("c"))

_lio_listio = libc.lio_listio
_lio_listio.argtypes = ()
_lio_listio.restypr = c_int

_aio_read = libc.aio_read
_aio_read.argtypes = ()
_aio_write.restype = c_int

_aio_write = libc.aio_write
_aio_write.argtypes = ()
_aio_write.restype = c_int 

_aio_error = libc.aio_error
_aio_error.argtypes = ()
_aio_error.restype = c_int

_aio_return = libc.aio_return
_aio_return.argtypes = ()
_aio_return.restype = c_int

_aio_cancel = libc.aio_cancel
_aio_cancel.argtypes = ()
_aio_cancel.restype = c_int

_aio_suspend = libc.aio_suspend
_aio_suspend.argtypes = ()
_aio_cancel.restype = c_int

_aio_fsync = aio.fsync
_aio_fsync.argtypes = ()
_aio_fsync.restype = c_int

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
