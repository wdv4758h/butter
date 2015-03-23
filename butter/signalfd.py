#!/usr/bin/env python
"""signalfd: Recive signals over a file descriptor"""

from .utils import Eventlike as _Eventlike
from .utils import CLOEXEC_DEFAULT as _CLOEXEC_DEFAULT
from ._signalfd import SFD_CLOEXEC, SFD_NONBLOCK, NEW_SIGNALFD
from ._signalfd import SIG_BLOCK, SIG_UNBLOCK, SIG_SETMASK
from ._signalfd import SIGINFO_LENGTH as _SIGINFO_LENGTH
from ._signalfd import signalfd, pthread_sigmask
from ._signalfd import signum_to_signame
from ._signalfd import ffi as _ffi, C as _C
import os as _os


class Signalfd(_Eventlike):
    def __init__(self, sigmask=set(), flags=0, closefd=_CLOEXEC_DEFAULT):
        """Create a new Signalfd object

        Arguments
        ----------
        :param int sigmask: Set of signals to respond on
        :param int flags: Flags to open the signalfd with
        
        Flags
        ------
        SFD_CLOEXEC: Close the signalfd when executing a new program
        SFD_NONBLOCK: Open the socket in non-blocking mode
        """
        super(self.__class__, self).__init__()
        
        self._flags = flags

        self._sigmask = sigmask = _ffi.new('sigset_t[1]')

        self._fd = signalfd(sigmask, NEW_SIGNALFD, flags)
        
    def __contains__(self, signal):
        val = _C.sigismember(self._sigmask, signal)
        
        if val < 0:
            raise ValueError('Signal is not a valid signal number')
        
        return bool(val)
    
    def _update(self):
        return signalfd(self._sigmask, self.fileno(), self._flags)

    def enable(self, signals):
        """Mark signals as active on signalfd
        
        :param int signals: A single signal to listen for
        :param list signals: A list of signals to listen for
        
        enable will mark all signals passed in on signalfd and takes
        ethier a signal integer representing the signal to add or an
        iterable if signals to (bulk) add
        
        The latter for is used for more efficent updates of signal masks
        """
        # if we have multipel signals then all is good
        try:
            signals = iter(signals)
        except TypeError:
        # if not make the value iterable
            signals = [signals]

        for signal in signals:
            _C.sigaddset(self._sigmask, signal)
            
        self._update()

    def enable_all(self):
        _C.sigfillset(self._sigmask)
        self._update()
        
    def disable(self, signal):
        _C.sigdelset(self._sigmask, signal)
        self._update()
        
    def disable_all(self):
        _C.sigemptyset(self._sigmask)
        self._update()
        
    def _read_events(self):
        buf = _os.read(self.fileno(), _SIGINFO_LENGTH)
        siginfo = _ffi.new('struct signalfd_siginfo *')

        _ffi.buffer(siginfo)[0:_SIGINFO_LENGTH] = buf
        
        return [Signal(siginfo)]


class Signal(object):
    """Proxy object for data returned by signalfd when a signal is recived
    
    Maps to most fields in a signalfd_siginfo
    
    Ommited mappings are ones that deal with traps and SIGQUEUE
    """
    def __init__(self, siginfo):
        self._siginfo = siginfo

    @property
    def signal(self):
        """The number of the signal being sent"""
        return self._siginfo.ssi_signo

    @property
    def signal_code(self):
        """The signal code"""
        return self._siginfo.ssi_code

    @property
    def pid(self):
        """PID of the sender of the signal"""
        return self._siginfo.ssi_pid

    @property
    def uid(self):
        """UID of the sender of the signal"""
        return self._siginfo.ssi_uid

    @property
    def sigio_fd(self):
        """FD that triggered the SIGIO signal"""
        return self._siginfo.ssi_fd

    @property
    def timer_id(self):
        """Kernel timer ID (POSIX Timers)"""
        return self._siginfo.ssi_tid
        
    @property
    def sigio_band(self):
        """SIGIO Band event"""
        return self._siginfo.ssi_band
        
    @property
    def overrun(self):
        """POSIX timer overrun count"""
        return self._siginfo.ssi_overrun
        
    @property
    def trapno(self):
        """Trap number that caused the signal"""
        return self._siginfo.trapno

    @property
    def child_status(self):
        """The return code of the exiting child process"""
        return self._siginfo.ssi_status
        
    @property
    def child_user_time(self):
        """The ammount of user time used by the exiting child process"""
        return self._siginfo.ssi_utime
        
    @property
    def child_system_time(self):
        """The ammount of system time used by the exiting child process"""
        return self._siginfo.ssi_stime

    def __repr__(self):
        # convert to Alpha name, else just return the int
        signame = signum_to_signame.get(self.signal, self.signal)
        return "<{} signal={} uid={} pid={}>".format(self.__class__.__name__, signame, self.uid, self.pid)
