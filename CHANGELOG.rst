.. :changelog:

Release History
---------------

0.9 (2014-05-24)
++++++++++++++++

- Add eventfd support
- Add eventfd asyncio support
- asyncio objects now have a close() method
- eventfd now has a close() method
- eventfd now has a fileno() method
- Add timerfd support
- Add timerfd asyncio support
- Added pthread_sigmask
- Added Signalfd
- Added Signalfd asyncio support

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

