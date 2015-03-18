.. :changelog:

Release History
---------------

0.9.3 (2015-03-10)
++++++++++++++++++

- errno to Exception mapping became a fixed part of the API (and unit tested)
- timerfd is now CLOCK_MONOTONIC by default
- Added Simplier TimerVal to replace Timerspec for timerfd
- Deprecated TimerStruct (will print a DeprecationWarning if such warnings have been turned on)
- OSError now returned instead of IOError. on python3 IOError = OSError so identical behavior will be observed

**Bug Fixes**

- C code now gets compiled at installation rather then first use
- Fixed up the name of an exception in error handling code leading to double exception
- pivot_root would return OSError rather than ValueError when incorect arguments were provided
- system.py was using its own definition of PermissionError, unify this with utils.py
- fanotify now raises PermissionError on EPERM instead of OSError (of which it is a subclass)

0.9.2 (2015-03-10)
++++++++++++++++++

- Deprecating seccomp support in favour of official libseccomp python bindings

**Bug Fixes**

- Add __init__.py to asyncio dir so that async methods can be imported

0.9.1 (2015-01-05)
++++++++++++++++++

**Bug Fixes**

- read_events was passing an undefined variable to actual implementations

0.9 (2014-05-24)
++++++++++++++++

- Added eventfd support
- Added eventfd AsyncIO support
- Added timerfd support
- Added timerfd AsyncIO support
- Added Signalfd
- Added Signalfd AsyncIO support
- Added pthread_sigmask
- AsyncIO objects now have a close() method
- Converted all high level event objects to Eventlike objects
- Inotify events now have an is_dir_event property
- Added test suite

**Bug Fixes**

- Fixed issue with circular imports preventing python3.4 from working
- Fixed issue with python2.7 returning floats where python3 returned ints


0.8 (2014-05-17)
++++++++++++++++

- Now works with python3.4 and higher
- 'from butter import \*' now imports the system module
- Added trove classification
- Added friendly properties to inotify event object
- Added friendly properties to fanotify event object
- FanotifyEvents now use less memory
- AsyncIO support for inotify on supported platforms
- AsyncIO support for fanotify on supported platforms

0.7 (2014-03-16)
++++++++++++++++

- Added system.py module
- Added gethostname syscall
- Added sethostname syscall
- Added mount syscall
- Added umount syscall
- Added pivot_root syscall
- Added getpid syscall
- Added getppid syscall
- Documented all new syscalls

0.6 (2014-03-12)
++++++++++++++++

- splice syscall documentation
- Added tee() syscall
- Added tee() example
- Added vmsplice() syscall
- Added vmsplice() example
- Updated setup.py to newer auto detecting version
- hide 'main' functions in splice module

0.5 (2014-03-11)
++++++++++++++++

- Added splice() syscall

0.4 (2013-12-12)
++++++++++++++++

- Refactor fanotify
- Refactor inotify
- Provide fanotify.str_to_events()
- Provide inotify.str_to_events()
- Add int to signal name mapping for inotify

0.3 (2013-11-20)
++++++++++++++++

- Support for inotify
- Initial support for fanotify
- Initial support for seccomp
- Add function to peer inside kernel buffer and get amount of available bytes to read
  
**API Changes**

- removed unused old (non working) signalfd, eventfd, aio

0.2 (2013-11-20)
++++++++++++++++

- Initial support for signalfd
- Initial support for eventfd
- Initial support for aio

