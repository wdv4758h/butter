#!/usr/bin/env python

import os

path = "/tmp/test"
print("Mounting temp filesystem at {}".format(path))
try:
    os.mkdir(path)
except OSError:
    pass
mount('tmpfs-testing', path, 'tmpfs')

#print("Pivoting to temp filesystem")
#pivot_root('/tmp', '/tmp')

print("Unmounting temp filesystem")
umount(path)

hostname = gethostname()
print("Old Hostname:", hostname)
try:
    sethostname('dsadsa')
except OSError:
    print("Error: Could not set hostname")
print("New Hostname:", gethostname())
print("Resorting old hostname")
try:
    sethostname(hostname)
except OSError:
    print("Error: Could not restore hostname")

print()

print("{}".format("Syscall PID:"), getpid())
print("os PID: ", os.getpid())
print("Syscall PPID: ", _C.getppid())
print("os PPID: ", os.getppid())

