#!/usr/bin/env python
"""Simple example showing how to transfer from socket to socket using a Pipe
as an intermediate buffer

Things to note:
* sockets cant be spliced directly (pipe is required)
* len is more of a hint, splicing may return less than specified
* splice only transfers whats currently in the buffer, it will not
  wait until len bytes are transferred
* Data does not get flushed out automatically, hence TCP_NODELAY to
  flush data out
* :py:func:`.splice` will be called once per packet
"""
from select import select
import socket
import os

in_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
out_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

out_pipe, in_pipe = os.pipe()

in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
in_sock.bind(('::', 8090))
in_sock.listen(1)
conn, addr = in_sock.accept()

print('Accepted connection from {}'.format(addr))

print('Connecting to (::1, 8091)')
out_sock.connect(('::1', 8091))

max_segment = 2**24 # chosen arbitrarily
bytes = True

try:
    while True:
        rd, wr, err = select([conn], [], [conn])
        if err:
            print('Connection error')
            break

        print('Splicing')
        bytes = splice(conn, in_pipe, len=max_segment, flags=SPLICE_F_MOVE)
        if bytes == 0:
            break

        print("Read {} Bytes".format(bytes))
        bytes = splice(out_pipe, out_sock, len=max_segment)
        out_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_CORK, 0)
        print("Wrote {} Bytes".format(bytes))
except KeyboardInterrupt:
    pass

print("Exiting")

