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



class aiocb(cytpes.Structure):
	_fields_ = (("aio_fildes", c_int),
				("aio_lio_opcode", c_int),
				("aio_reqprio", c_int),
				("aio_buf",) # volitile mutable buffer
				("aio_nbytes", c_int),
				("aio_sigevent",) #sigevent struct
				# Kernel internal accounting
				("__next_prio", c_void_p)#pointer to next block
				("__abs_prio", c_int),
				("__policy", c_int),
				("__error_code", c_int),
				("__return_value", )#__size_t
				("aio_offset",)#__off_t (or __off_t64)
				# padding
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
