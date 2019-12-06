#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import binascii
import re
import sys
import socket
import uuid
import logging
import os
import threading

try:
        # Python 2 import.
        import SocketServer as socketserver
        import Queue as Queue
        import pykms_Selectors as selectors
        from pykms_Time import monotonic as time
except ImportError:
        # Python 3 import.
        import socketserver
        import queue as Queue
        import selectors
        from time import monotonic as time

import pykms_RpcBind, pykms_RpcRequest
from pykms_RpcBase import rpcBase
from pykms_Dcerpc import MSRPCHeader
from pykms_Misc import logger_create, check_logfile, check_lcid
from pykms_Misc import KmsParser, KmsException
from pykms_Format import enco, deco, ShellMessage, pretty_printer

srv_description = 'KMS Server Emulator written in Python'
srv_version = 'py-kms_2019-05-15'
srv_config = {}

##---------------------------------------------------------------------------------------------------------------------------------------------------------
class KeyServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        daemon_threads = True
        allow_reuse_address = True

        def __init__(self, server_address, RequestHandlerClass):
                socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass)
                self.__shutdown_request = False
                self.r_service, self.w_service = os.pipe()

                if hasattr(selectors, 'PollSelector'):
                        self._ServerSelector = selectors.PollSelector
                else:
                        self._ServerSelector = selectors.SelectSelector

        def pykms_serve(self):
                """ Mixing of socketserver serve_forever() and handle_request() functions,
                    without elements blocking tkinter.
                    Handle one request at a time, possibly blocking.
                    Respects self.timeout.
                """
                # Support people who used socket.settimeout() to escape
                # pykms_serve() before self.timeout was available.
                timeout = self.socket.gettimeout()
                if timeout is None:
                        timeout = self.timeout
                elif self.timeout is not None:
                        timeout = min(timeout, self.timeout)
                if timeout is not None:
                        deadline = time() + timeout

                try:
                        # Wait until a request arrives or the timeout expires.
                        with self._ServerSelector() as selector:
                                selector.register(fileobj = self, events = selectors.EVENT_READ)
                                # self-pipe trick.
                                selector.register(fileobj = self.r_service, events = selectors.EVENT_READ)

                                while not self.__shutdown_request:
                                        ready = selector.select(timeout)
                                        if self.__shutdown_request:
                                                break

                                        if ready == []:
                                                if timeout is not None:
                                                        timeout = deadline - time()
                                                        if timeout < 0:
                                                                return self.handle_timeout()
                                        else:
                                                for key, mask in ready:
                                                        if key.fileobj is self:
                                                                self._handle_request_noblock()
                                                        elif key.fileobj is self.r_service:
                                                                # only to clean buffer.
                                                                msgkill = os.read(self.r_service, 8).decode('utf-8')
                                                                sys.exit(0)
                finally:
                        self.__shutdown_request = False

        def shutdown(self):
                self.__shutdown_request = True

        def handle_timeout(self):
                pretty_printer(log_obj = loggersrv.error, to_exit = True,
                               put_text = "{reverse}{red}{bold}Server connection timed out. Exiting...{end}")

        def handle_error(self, request, client_address):
                pass


class server_thread(threading.Thread):
        def __init__(self, queue, name):
                threading.Thread.__init__(self)
                self.name = name
                self.queue = queue
                self.server = None
                self.is_running_server, self.with_gui = [False for _ in range(2)]
                self.is_running_thread = threading.Event()

        def terminate_serve(self):
                self.server.shutdown()
                self.server.server_close()

        def terminate_thread(self):
                self.is_running_thread.set()

        def terminate_eject(self):
                os.write(self.server.w_service, u'☠'.encode('utf-8'))

        def run(self):
                while not self.is_running_thread.is_set():
                        try:
                                item = self.queue.get(block = True, timeout = 0.1)
                                self.queue.task_done()
                        except Queue.Empty:
                                continue
                        else:
                                try:
                                        if item == 'start':
                                                self.eject = False
                                                self.is_running_server = True
                                                # Check options.
                                                server_check()
                                                # Create and run server.
                                                self.server = server_create()
                                                self.server.pykms_serve()
                                        elif item == 'stop':
                                                self.server = None
                                                self.is_running_server = False
                                        elif item == 'exit':
                                                self.terminate_thread()
                                except SystemExit as e:
                                        self.eject = True
                                        if not self.with_gui:
                                                raise
                                        else:
                                                continue

##---------------------------------------------------------------------------------------------------------------------------------------------------------

loggersrv = logging.getLogger('logsrv')

# 'help' string - 'default' value - 'dest' string.
srv_options = {
        'ip' : {'help' : 'The IP address to listen on. The default is \"0.0.0.0\" (all interfaces).', 'def' : "0.0.0.0", 'des' : "ip"},
        'port' : {'help' : 'The network port to listen on. The default is \"1688\".', 'def' : 1688, 'des' : "port"},
        'epid' : {'help' : 'Use this option to manually specify an ePID to use. If no ePID is specified, a random ePID will be auto generated.',
                  'def' : None, 'des' : "epid"},
        'lcid' : {'help' : 'Use this option to manually specify an LCID for use with randomly generated ePIDs. Default is \"1033\" (en-us)',
                  'def' : 1033, 'des' : "lcid"},
        'count' : {'help' : 'Use this option to specify the current client count. A number >=25 is required to enable activation of client OSes; \
for server OSes and Office >=5', 'def' : None, 'des' : "CurrentClientCount"},
        'activation' : {'help' : 'Use this option to specify the activation interval (in minutes). Default is \"120\" minutes (2 hours).',
                        'def' : 120, 'des': "VLActivationInterval"},
        'renewal' : {'help' : 'Use this option to specify the renewal interval (in minutes). Default is \"10080\" minutes (7 days).',
                     'def' : 1440 * 7, 'des' : "VLRenewalInterval"},
        'sql' : {'help' : 'Use this option to store request information from unique clients in an SQLite database. Desactivated by default.',
                 'def' : False, 'des' : "sqlite"},
        'hwid' : {'help' : 'Use this option to specify a HWID. The HWID must be an 16-character string of hex characters. \
The default is \"364F463A8863D35F\" or type \"RANDOM\" to auto generate the HWID.', 'def' : "364F463A8863D35F", 'des' : "hwid"},
        'time' : {'help' : 'Max time (in seconds) for server to generate an answer. If \"None\" (default) serve forever.', 'def' : None, 'des' : "timeout"},
        'llevel' : {'help' : 'Use this option to set a log level. The default is \"ERROR\".', 'def' : "ERROR", 'des' : "loglevel",
                    'choi' : ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "MINI"]},
        'lfile' : {'help' : 'Use this option to set an output log file. The default is \"pykms_logserver.log\". Type \"STDOUT\" to view \
log info on stdout. Type \"FILESTDOUT\" to combine previous actions.',
                   'def' : os.path.dirname(os.path.abspath( __file__ )) + "/pykms_logserver.log", 'des' : "logfile"},
        'lsize' : {'help' : 'Use this flag to set a maximum size (in MB) to the output log file. Desactivated by default.', 'def' : 0, 'des': "logsize"},
        }

def server_options():
        parser = KmsParser(description = srv_description, epilog = 'version: ' + srv_version)
        parser.add_argument("ip", nargs = "?", action = "store", default = srv_options['ip']['def'], help = srv_options['ip']['help'], type = str)
        parser.add_argument("port", nargs = "?", action = "store", default = srv_options['port']['def'], help = srv_options['port']['help'], type = int)
        parser.add_argument("-e", "--epid", dest = srv_options['epid']['des'], default = srv_options['epid']['def'], help = srv_options['epid']['help'], type = str)
        parser.add_argument("-l", "--lcid", dest = srv_options['lcid']['des'], default = srv_options['lcid']['def'], help = srv_options['lcid']['help'], type = int)
        parser.add_argument("-c", "--client-count", dest = srv_options['count']['des'] , default = srv_options['count']['def'],
                            help = srv_options['count']['help'], type = int)
        parser.add_argument("-a", "--activation-interval", dest = srv_options['activation']['des'], default = srv_options['activation']['def'],
                            help = srv_options['activation']['help'], type = int)
        parser.add_argument("-r", "--renewal-interval", dest = srv_options['renewal']['des'], default = srv_options['renewal']['def'],
                            help = srv_options['renewal']['help'], type = int)
        parser.add_argument("-s", "--sqlite", dest = srv_options['sql']['des'], action = "store_const", const = True, default = srv_options['sql']['def'],
                            help = srv_options['sql']['help'])
        parser.add_argument("-w", "--hwid", dest = srv_options['hwid']['des'], action = "store", default = srv_options['hwid']['def'],
                            help = srv_options['hwid']['help'], type = str)
        parser.add_argument("-t", "--timeout", dest = srv_options['time']['des'], action = "store", default = srv_options['time']['def'],
                            help = srv_options['time']['help'], type = int)
        parser.add_argument("-V", "--loglevel", dest = srv_options['llevel']['des'], action = "store", choices = srv_options['llevel']['choi'],
                            default = srv_options['llevel']['def'], help = srv_options['llevel']['help'], type = str)
        parser.add_argument("-F", "--logfile", nargs = "+", action = "store", dest = srv_options['lfile']['des'], default = srv_options['lfile']['def'],
                            help = srv_options['lfile']['help'], type = str)
        parser.add_argument("-S", "--logsize", dest = srv_options['lsize']['des'], action = "store", default = srv_options['lsize']['def'],
                            help = srv_options['lsize']['help'], type = float)

        try:
                srv_config.update(vars(parser.parse_args()))
                # Check logfile.
                srv_config['logfile'] = check_logfile(srv_config['logfile'], srv_options['lfile']['def'], where = "srv")
        except KmsException as e:
                pretty_printer(put_text = "{reverse}{red}{bold}%s. Exiting...{end}" %str(e), to_exit = True)

def server_check():
        # Check logfile (only for GUI).
        if serverthread.with_gui:
                srv_config['logfile'] = check_logfile(srv_config['logfile'], srv_options['lfile']['def'], where = "srv")

        # Setup hidden or not messages.
        ShellMessage.view = ( False if any(i in ['STDOUT', 'FILESTDOUT'] for i in srv_config['logfile']) else True )

        # Create log.        
        logger_create(loggersrv, srv_config, mode = 'a')

        # Random HWID.
        if srv_config['hwid'] == "RANDOM":
                randomhwid = uuid.uuid4().hex
                srv_config['hwid'] = randomhwid[:16]
           
        # Sanitize HWID.
        hexstr = srv_config['hwid'].strip('0x')
        hexsub = re.sub(r'[^0-9a-fA-F]', '', hexstr)
        diff = set(hexstr).symmetric_difference(set(hexsub))

        if len(diff) != 0:
                diff = str(diff).replace('{', '').replace('}', '')
                pretty_printer(log_obj = loggersrv.error, to_exit = True,
                               put_text = "{reverse}{red}{bold}HWID '%s' is invalid. Digit %s non hexadecimal. Exiting...{end}" %(hexstr.upper(), diff))
        else:
                lh = len(hexsub)
                if lh % 2 != 0:
                        pretty_printer(log_obj = loggersrv.error, to_exit = True,
                                       put_text = "{reverse}{red}{bold}HWID '%s' is invalid. Hex string is odd length. Exiting...{end}" %hexsub.upper())
                elif lh < 16:
                        pretty_printer(log_obj = loggersrv.error, to_exit = True,
                                       put_text = "{reverse}{red}{bold}HWID '%s' is invalid. Hex string is too short. Exiting...{end}" %hexsub.upper())
                elif lh > 16:
                        pretty_printer(log_obj = loggersrv.error, to_exit = True,
                                       put_text = "{reverse}{red}{bold}HWID '%s' is invalid. Hex string is too long. Exiting...{end}" %hexsub.upper())
                else:
                        srv_config['hwid'] = binascii.a2b_hex(hexsub)

        # Check LCID.
        srv_config['lcid'] = check_lcid(srv_config['lcid'], loggersrv.warning)
                                
        # Check sqlite.
        try:
                import sqlite3            
        except:
                pretty_printer(log_obj = loggersrv.warning,
                               put_text = "{reverse}{yellow}{bold}Module 'sqlite3' is not installed, database support disabled.{end}")
                srv_config['dbSupport'] = False
        else:
                srv_config['dbSupport'] = True

        # Check port.
        if not 1 <= srv_config['port'] <= 65535:
                pretty_printer(log_obj = loggersrv.error, to_exit = True,
                               put_text = "{red}{bold}Port number '%s' is invalid. Enter between 1 - 65535. Exiting...{end}" %srv_config['port'])

def server_create():
        server = KeyServer((srv_config['ip'], srv_config['port']), kmsServerHandler)
        server.timeout = srv_config['timeout']
        loggersrv.info("TCP server listening at %s on port %d." % (srv_config['ip'], srv_config['port']))
        loggersrv.info("HWID: %s" % deco(binascii.b2a_hex(srv_config['hwid']), 'utf-8').upper())
        return server

def srv_terminate(exit_server = False, exit_thread = False):
        if exit_server:
                serverthread.terminate_serve()
                serverqueue.put('stop')
        if exit_thread:
                serverqueue.put('exit')

def srv_main_without_gui():
        # Parse options.
        server_options()
        # Run threaded server.
        serverqueue.put('start')
        # Wait to finish.
        try:
                while serverthread.is_alive():
                        serverthread.join(timeout = 0.5)
        except (KeyboardInterrupt, SystemExit):
                srv_terminate(exit_server = True, exit_thread = True)

def srv_main_with_gui(width = 950, height = 660):
        import pykms_GuiBase

        root = pykms_GuiBase.KmsGui()
        root.title(pykms_GuiBase.gui_description + ' ' + pykms_GuiBase.gui_version)
        # Main window initial position.
        ## https://stackoverflow.com/questions/14910858/how-to-specify-where-a-tkinter-window-opens
        ws = root.winfo_screenwidth()
        hs = root.winfo_screenheight()
        x = (ws / 2) - (width / 2)
        y = (hs / 2) - (height / 2)
        root.geometry('+%d+%d' %(x, y))
        # disable maximize button.
        root.resizable(0, 0)
        root.mainloop()

class kmsServerHandler(socketserver.BaseRequestHandler):
        def setup(self):
                loggersrv.info("Connection accepted: %s:%d" % (self.client_address[0], self.client_address[1]))

        def handle(self):
                while True:
                        # self.request is the TCP socket connected to the client
                        try:
                                self.data = self.request.recv(1024)
                                if self.data == '' or not self.data:
                                        pretty_printer(log_obj = loggersrv.warning,
                                                       put_text = "{reverse}{yellow}{bold}No data received.{end}")
                                        break
                        except socket.error as e:
                                pretty_printer(log_obj = loggersrv.error,
                                               put_text = "{reverse}{red}{bold}While receiving: %s{end}" %str(e))
                                break
                        
                        packetType = MSRPCHeader(self.data)['type']
                        if packetType == rpcBase.packetType['bindReq']:
                                loggersrv.info("RPC bind request received.")
                                pretty_printer(num_text = [-2, 2], where = "srv")
                                handler = pykms_RpcBind.handler(self.data, srv_config)
                        elif packetType == rpcBase.packetType['request']:
                                loggersrv.info("Received activation request.")
                                pretty_printer(num_text = [-2, 13], where = "srv")
                                handler = pykms_RpcRequest.handler(self.data, srv_config)
                        else:
                                pretty_printer(log_obj = loggersrv.error,
                                               put_text = "{reverse}{red}{bold}Invalid RPC request type %s.{end}" %packetType)
                                break

                        res = enco(str(handler.populate()), 'latin-1')

                        if packetType == rpcBase.packetType['bindReq']:
                                loggersrv.info("RPC bind acknowledged.")
                                pretty_printer(num_text = [-3, 5, 6], where = "srv")
                        elif packetType == rpcBase.packetType['request']:
                                loggersrv.info("Responded to activation request.")
                                pretty_printer(num_text = [-3, 18, 19], where = "srv")

                        try:
                                self.request.send(res)
                                if packetType == rpcBase.packetType['request']:
                                        break
                        except socket.error as e:
                                pretty_printer(log_obj = loggersrv.error,
                                               put_text = "{reverse}{red}{bold}While sending: %s{end}" %str(e))
                                break

        def finish(self):
                self.request.close()
                loggersrv.info("Connection closed: %s:%d" % (self.client_address[0], self.client_address[1]))


serverqueue = Queue.Queue(maxsize = 0)
serverthread = server_thread(serverqueue, name = "Thread-Srv")
serverthread.setDaemon(True)
serverthread.start()

if __name__ == "__main__":
        if sys.stdout.isatty():
                srv_main_without_gui()
        else:
                try:
                        srv_main_with_gui()
                except:
                        srv_main_without_gui()
