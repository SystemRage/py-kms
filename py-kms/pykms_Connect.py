#!/usr/bin/env python3

import os
import socket
import selectors
import ipaddress
import logging
from pykms_Format import pretty_printer
loggersrv = logging.getLogger('logsrv')

# https://github.com/python/cpython/blob/master/Lib/socket.py
def has_dualstack_ipv6():
        """ Return True if the platform supports creating a SOCK_STREAM socket
            which can handle both AF_INET and AF_INET6 (IPv4 / IPv6) connections.
        """
        if not socket.has_ipv6 or not hasattr(socket._socket, 'IPPROTO_IPV6') or not hasattr(socket._socket, 'IPV6_V6ONLY'):
                return False
        try:
                with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
                        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                        return True
        except socket.error:
                return False

def create_server_sock(address, *, family = socket.AF_INET, backlog = None, reuse_port = False, dualstack_ipv6 = False):
        """ Convenience function which creates a SOCK_STREAM type socket
            bound to *address* (a 2-tuple (host, port)) and return the socket object.
            Internally it takes care of choosing the right address family (IPv4 or IPv6),depending on
            the host specified in *address* tuple. 
        
            *family*          should be either AF_INET or AF_INET6.
            *backlog*         is the queue size passed to socket.listen().
            *reuse_port*      if True and the platform supports it, we will use the SO_REUSEPORT socket option.
            *dualstack_ipv6*  if True and the platform supports it, it will create an AF_INET6 socket able to accept both IPv4 or IPv6 connections;
                              when False it will explicitly disable this option on platforms that enable it by default (e.g. Linux).
        """
        if reuse_port and not hasattr(socket._socket, "SO_REUSEPORT"):
                pretty_printer(log_obj = loggersrv.warning, put_text = "{reverse}{yellow}{bold}SO_REUSEPORT not supported on this platform - ignoring socket option.{end}")
                reuse_port = False
        
        if dualstack_ipv6:
                if not has_dualstack_ipv6():
                        raise ValueError("dualstack_ipv6 not supported on this platform")
                if family != socket.AF_INET6:
                        raise ValueError("dualstack_ipv6 requires AF_INET6 family")
                        
        sock = socket.socket(family, socket.SOCK_STREAM)
        try:
                # Note about Windows. We don't set SO_REUSEADDR because:
                # 1) It's unnecessary: bind() will succeed even in case of a
                # previous closed socket on the same address and still in
                # TIME_WAIT state.
                # 2) If set, another socket is free to bind() on the same
                # address, effectively preventing this one from accepting
                # connections. Also, it may set the process in a state where
                # it'll no longer respond to any signals or graceful kills.
                # See: msdn2.microsoft.com/en-us/library/ms740621(VS.85).aspx
                if os.name not in ('nt', 'cygwin') and hasattr(socket._socket, 'SO_REUSEADDR'):
                        try:
                                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        except socket.error:
                                # Fail later on bind(), for platforms which may not
                                # support this option.
                                pass
                if reuse_port:
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                if socket.has_ipv6 and family == socket.AF_INET6:
                        if dualstack_ipv6:
                                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                        elif hasattr(socket._socket, "IPV6_V6ONLY") and hasattr(socket._socket, "IPPROTO_IPV6"):
                                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
                try:
                        sock.bind(address)
                except socket.error as err:
                        msg = '%s (while attempting to bind on address %r)' %(err.strerror, address)
                        raise socket.error(err.errno, msg) from None

                if backlog is None:
                        sock.listen()
                else:
                        sock.listen(backlog)
                return sock
        except socket.error:
                sock.close()
                raise

# Giampaolo Rodola' class (license MIT) revisited for py-kms.
# http://code.activestate.com/recipes/578504-server-supporting-ipv4-and-ipv6/
class MultipleListener(object):
        """ Listen on multiple addresses specified as a list of
            (`host`, `port`, `backlog`, `reuse_port`) tuples.
            Useful to listen on both IPv4 and IPv6 on those systems where a dual stack
            is not supported natively (Windows and many UNIXes).

            Calls like settimeout() and setsockopt() will be applied to all sockets.
            Calls like gettimeout() or getsockopt() will refer to the first socket in the list.
        """
        def __init__(self, addresses = [], want_dual = False):
                self.socks, self.sockmap = [], {}
                completed = False
                self.cant_dual = []

                try:
                        for addr in addresses:
                                addr = self.check(addr)
                                ip_ver = ipaddress.ip_address(addr[0])
                                
                                if ip_ver.version == 4 and want_dual:
                                        self.cant_dual.append(addr[0])                                

                                sock = create_server_sock((addr[0], addr[1]),
                                                          family = (socket.AF_INET if ip_ver.version == 4 else socket.AF_INET6),
                                                          backlog = addr[2],
                                                          reuse_port = addr[3],
                                                          dualstack_ipv6 = (False if ip_ver.version == 4 else want_dual))
                                self.socks.append(sock)
                                self.sockmap[sock.fileno()] = sock

                        completed = True
                finally:
                        if not completed:
                                self.close()
                        
        def __enter__(self):
                return self

        def __exit__(self):
                self.close()

        def __repr__(self):
                addrs = []
                for sock in self.socks:
                        try:
                                addrs.append(sock.getsockname())
                        except socket.error:
                                addrs.append(())
                return "<%s(%r) at %#x>" %(self.__class__.__name__, addrs, id(self))

        def filenos(self):
                """ Return sockets' file descriptors as a list of integers. """
                return list(self.sockmap.keys())

        def register(self, pollster):
                for fd in self.filenos():
                        pollster.register(fileobj = fd, events = selectors.EVENT_READ)

        def multicall(self, name, *args, **kwargs):
                for sock in self.socks:
                        meth = getattr(sock, name)
                        meth(*args, **kwargs)

        def poll(self):
                """ Return the first readable fd. """
                if hasattr(selectors, 'PollSelector'):
                        pollster = selectors.PollSelector
                else:
                        pollster = selectors.SelectSelector
                        
                timeout = self.gettimeout()
                
                with pollster() as pollster:
                        self.register(pollster)
                        fds = pollster.select(timeout)
                        
                        if timeout and fds == []:
                                raise socket.timeout('timed out')
                        try:
                                return fds[0][0].fd
                        except IndexError:
                                # non-blocking socket
                                pass

        def accept(self):
                """ Accept a connection from the first socket which is ready to do so. """
                fd = self.poll()
                sock = (self.sockmap[fd] if fd else self.socks[0])
                return sock.accept()

        def getsockname(self):
                """ Return first registered socket's own address. """
                return self.socks[0].getsockname()

        def getsockopt(self, level, optname, buflen = 0):
                """ Return first registered socket's options. """
                return self.socks[0].getsockopt(level, optname, buflen)

        def gettimeout(self):
                """ Return first registered socket's timeout. """
                return self.socks[0].gettimeout()

        def settimeout(self, timeout):
                """ Set timeout for all registered sockets. """
                self.multicall('settimeout', timeout)

        def setblocking(self, flag):
                """ Set non-blocking mode for all registered sockets. """
                self.multicall('setblocking', flag)

        def setsockopt(self, level, optname, value):
                """ Set option for all registered sockets. """
                self.multicall('setsockopt', level, optname, value)

        def shutdown(self, how):
                """ Shut down all registered sockets. """
                self.multicall('shutdown', how)

        def close(self):
                """ Close all registered sockets. """
                self.multicall('close')
                self.socks, self.sockmap = [], {}

        def check(self, address):
                if len(address) == 1:
                        raise socket.error("missing `host` or `port` parameter.")
                if len(address) == 2:
                        address += (None, True,)
                elif len(address) == 3:
                        address += (True,)
                return address
