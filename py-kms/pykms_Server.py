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
import pickle
import socketserver
import queue as Queue
import selectors
from time import monotonic as time

import pykms_RpcBind, pykms_RpcRequest
from pykms_RpcBase import rpcBase
from pykms_Dcerpc import MSRPCHeader
from pykms_Misc import check_setup, check_lcid
from pykms_Misc import KmsParser, KmsParserException, KmsParserHelp
from pykms_Misc import kms_parser_get, kms_parser_check_optionals, kms_parser_check_positionals
from pykms_Format import enco, deco, pretty_printer
from Etrigan import Etrigan, Etrigan_parser, Etrigan_check, Etrigan_job

srv_version             = "py-kms_2020-07-01"
__license__             = "The Unlicense"
__author__              = u"Matteo ℱan <SystemRage@protonmail.com>"
__url__                 = "https://github.com/SystemRage/py-kms"
srv_description         = "py-kms: KMS Server Emulator written in Python"
srv_config = {}

##---------------------------------------------------------------------------------------------------------------------------------------------------------
class KeyServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        daemon_threads = True
        allow_reuse_address = True

        def __init__(self, server_address, RequestHandlerClass):
                self.address_family = socket.AF_INET6 # This call make sure the server creates an IPv6 socket and NOT an IPv4 by default
                socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass)
                self.__shutdown_request = False
                self.r_service, self.w_service = socket.socketpair()

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
                                selector.register(fileobj = self.r_service.fileno(), events = selectors.EVENT_READ)

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
                                                        elif key.fileobj is self.r_service.fileno():
                                                                # only to clean buffer.
                                                                msgkill = os.read(self.r_service.fileno(), 8).decode('utf-8')
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
                self.is_running_server, self.with_gui, self.checked = [False for _ in range(3)]
                self.is_running_thread = threading.Event()

        def terminate_serve(self):
                self.server.shutdown()
                self.server.server_close()
                self.server = None
                self.is_running_server = False

        def terminate_thread(self):
                self.is_running_thread.set()

        def terminate_eject(self):
                os.write(self.server.w_service.fileno(), u'☠'.encode('utf-8'))

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
                                                if not self.checked:
                                                        server_check()
                                                # Create and run server.
                                                self.server = server_create()
                                                self.server.pykms_serve()
                                except (SystemExit, Exception) as e:
                                        self.eject = True
                                        if not self.with_gui:
                                                raise
                                        else:
                                                if isinstance(e, SystemExit):
                                                        continue
                                                else:
                                                        raise

##---------------------------------------------------------------------------------------------------------------------------------------------------------

loggersrv = logging.getLogger('logsrv')

# 'help' string - 'default' value - 'dest' string.
srv_options = {
        'ip' : {'help' : 'The IPv6 address to listen on. The default is \"::\" (all interfaces).', 'def' : "::", 'des' : "ip"},
        'port' : {'help' : 'The network port to listen on. The default is \"1688\".', 'def' : 1688, 'des' : "port"},
        'epid' : {'help' : 'Use this option to manually specify an ePID to use. If no ePID is specified, a random ePID will be auto generated.',
                  'def' : None, 'des' : "epid"},
        'lcid' : {'help' : 'Use this option to manually specify an LCID for use with randomly generated ePIDs. Default is \"1033\" (en-us)',
                  'def' : 1033, 'des' : "lcid"},
        'count' : {'help' : 'Use this option to specify the current client count. A number >=25 is required to enable activation of client OSes; \
for server OSes and Office >=5', 'def' : None, 'des' : "clientcount"},
        'activation' : {'help' : 'Use this option to specify the activation interval (in minutes). Default is \"120\" minutes (2 hours).',
                        'def' : 120, 'des': "activation"},
        'renewal' : {'help' : 'Use this option to specify the renewal interval (in minutes). Default is \"10080\" minutes (7 days).',
                     'def' : 1440 * 7, 'des' : "renewal"},
        'sql' : {'help' : 'Use this option to store request information from unique clients in an SQLite database. Desactivated by default.',
                 'def' : False, 'des' : "sqlite"},
        'hwid' : {'help' : 'Use this option to specify a HWID. The HWID must be an 16-character string of hex characters. \
The default is \"364F463A8863D35F\" or type \"RANDOM\" to auto generate the HWID.', 'def' : "364F463A8863D35F", 'des' : "hwid"},
        'time0' : {'help' : 'Maximum inactivity time (in seconds) after which the connection with the client is closed. If \"None\" (default) serve forever.',
                   'def' : None, 'des' : "timeoutidle"},
        'asyncmsg' : {'help' : 'Prints pretty / logging messages asynchronously. Desactivated by default.',
                      'def' : False, 'des' : "asyncmsg"},
        'llevel' : {'help' : 'Use this option to set a log level. The default is \"ERROR\".', 'def' : "ERROR", 'des' : "loglevel",
                    'choi' : ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "MINI"]},
        'lfile' : {'help' : 'Use this option to set an output log file. The default is \"pykms_logserver.log\". \
Type \"STDOUT\" to view log info on stdout. Type \"FILESTDOUT\" to combine previous actions. \
Use \"STDOUTOFF\" to disable stdout messages. Use \"FILEOFF\" if you not want to create logfile.',
                   'def' : os.path.join('.', 'pykms_logserver.log'), 'des' : "logfile"},
        'lsize' : {'help' : 'Use this flag to set a maximum size (in MB) to the output log file. Desactivated by default.', 'def' : 0, 'des': "logsize"},
        }

def server_options():
        server_parser = KmsParser(description = srv_description, epilog = 'version: ' + srv_version, add_help = False)
        server_parser.add_argument("ip", nargs = "?", action = "store", default = srv_options['ip']['def'], help = srv_options['ip']['help'], type = str)
        server_parser.add_argument("port", nargs = "?", action = "store", default = srv_options['port']['def'], help = srv_options['port']['help'], type = int)
        server_parser.add_argument("-e", "--epid", action = "store", dest = srv_options['epid']['des'], default = srv_options['epid']['def'],
                                   help = srv_options['epid']['help'], type = str)
        server_parser.add_argument("-l", "--lcid", action = "store", dest = srv_options['lcid']['des'], default = srv_options['lcid']['def'],
                                   help = srv_options['lcid']['help'], type = int)
        server_parser.add_argument("-c", "--client-count", action = "store", dest = srv_options['count']['des'] , default = srv_options['count']['def'],
                                   help = srv_options['count']['help'], type = int)
        server_parser.add_argument("-a", "--activation-interval", action = "store", dest = srv_options['activation']['des'],
                                   default = srv_options['activation']['def'], help = srv_options['activation']['help'], type = int)
        server_parser.add_argument("-r", "--renewal-interval", action = "store", dest = srv_options['renewal']['des'],
                                   default = srv_options['renewal']['def'], help = srv_options['renewal']['help'], type = int)
        server_parser.add_argument("-s", "--sqlite", action = "store_true", dest = srv_options['sql']['des'],
                                   default = srv_options['sql']['def'], help = srv_options['sql']['help'])
        server_parser.add_argument("-w", "--hwid", action = "store", dest = srv_options['hwid']['des'], default = srv_options['hwid']['def'],
                                   help = srv_options['hwid']['help'], type = str)
        server_parser.add_argument("-t0", "--timeout-idle", action = "store", dest = srv_options['time0']['des'], default = srv_options['time0']['def'],
                                   help = srv_options['time0']['help'], type = int)
        server_parser.add_argument("-y", "--async-msg", action = "store_true", dest = srv_options['asyncmsg']['des'],
                                   default = srv_options['asyncmsg']['def'], help = srv_options['asyncmsg']['help'])
        server_parser.add_argument("-V", "--loglevel", action = "store", dest = srv_options['llevel']['des'], choices = srv_options['llevel']['choi'],
                                   default = srv_options['llevel']['def'], help = srv_options['llevel']['help'], type = str)
        server_parser.add_argument("-F", "--logfile", nargs = "+", action = "store", dest = srv_options['lfile']['des'],
                                   default = srv_options['lfile']['def'], help = srv_options['lfile']['help'], type = str)
        server_parser.add_argument("-S", "--logsize", action = "store", dest = srv_options['lsize']['des'], default = srv_options['lsize']['def'],
                                   help = srv_options['lsize']['help'], type = float)

        server_parser.add_argument("-h", "--help", action = "help", help = "show this help message and exit")

        daemon_parser = KmsParser(description = "daemon options inherited from Etrigan", add_help = False)
        daemon_subparser = daemon_parser.add_subparsers(dest = "mode")

        etrigan_parser = daemon_subparser.add_parser("etrigan", add_help = False)
        etrigan_parser.add_argument("-g", "--gui", action = "store_const", dest = 'gui', const = True, default = False,
                                    help = "Enable py-kms GUI usage.")
        etrigan_parser = Etrigan_parser(parser = etrigan_parser)

        try:
                userarg = sys.argv[1:]

                # Run help.
                if any(arg in ["-h", "--help"] for arg in userarg):
                        KmsParserHelp().printer(parsers = [server_parser, daemon_parser, etrigan_parser])

                # Get stored arguments.
                pykmssrv_zeroarg, pykmssrv_onearg = kms_parser_get(server_parser)
                etrigan_zeroarg, etrigan_onearg = kms_parser_get(etrigan_parser)
                pykmssrv_zeroarg += ['etrigan'] # add subparser

                # Set defaults for config.
                # example case:
                #               python3 pykms_Server.py
                srv_config.update(vars(server_parser.parse_args([])))

                try:
                        # Eventually set daemon options for dict server config.
                        pos = sys.argv[1:].index('etrigan')
                        # example cases:
                        #               python3 pykms_Server.py etrigan start
                        #               python3 pykms_Server.py etrigan start --daemon_optionals
                        #               python3 pykms_Server.py 1.2.3.4 etrigan start
                        #               python3 pykms_Server.py 1.2.3.4 etrigan start --daemon_optionals
                        #               python3 pykms_Server.py 1.2.3.4 1234 etrigan start
                        #               python3 pykms_Server.py 1.2.3.4 1234 etrigan start --daemon_optionals
                        #               python3 pykms_Server.py --pykms_optionals etrigan start
                        #               python3 pykms_Server.py --pykms_optionals etrigan start --daemon_optionals
                        #               python3 pykms_Server.py 1.2.3.4 --pykms_optionals etrigan start
                        #               python3 pykms_Server.py 1.2.3.4 --pykms_optionals etrigan start --daemon_optionals
                        #               python3 pykms_Server.py 1.2.3.4 1234 --pykms_optionals etrigan start
                        #               python3 pykms_Server.py 1.2.3.4 1234 --pykms_optionals etrigan start --daemon_optionals

                        kms_parser_check_optionals(userarg[0:pos], pykmssrv_zeroarg, pykmssrv_onearg, exclude_opt_len = ['-F', '--logfile'])
                        kms_parser_check_positionals(srv_config, server_parser.parse_args, arguments = userarg[0:pos], force_parse = True)
                        kms_parser_check_optionals(userarg[pos:], etrigan_zeroarg, etrigan_onearg, msg = 'optional etrigan')
                        kms_parser_check_positionals(srv_config, daemon_parser.parse_args, arguments = userarg[pos:], msg = 'positional etrigan')

                except ValueError:
                        # Update pykms options for dict server config.
                        # example cases:
                        #               python3 pykms_Server.py 1.2.3.4
                        #               python3 pykms_Server.py 1.2.3.4 --pykms_optionals
                        #               python3 pykms_Server.py 1.2.3.4 1234
                        #               python3 pykms_Server.py 1.2.3.4 1234 --pykms_optionals
                        #               python3 pykms_Server.py --pykms_optionals

                        kms_parser_check_optionals(userarg, pykmssrv_zeroarg, pykmssrv_onearg, exclude_opt_len = ['-F', '--logfile'])
                        kms_parser_check_positionals(srv_config, server_parser.parse_args)

        except KmsParserException as e:
                pretty_printer(put_text = "{reverse}{red}{bold}%s. Exiting...{end}" %str(e), to_exit = True)


class Etrigan_Check(Etrigan_check):
        def emit_opt_err(self, msg):
                pretty_printer(put_text = "{reverse}{red}{bold}%s{end}" %msg, to_exit = True)

class Etrigan(Etrigan):
        def emit_message(self, message, to_exit = False):
                if not self.mute:
                        pretty_printer(put_text = "{reverse}{green}{bold}%s{end}" %message)
                if to_exit:
                        sys.exit(0)

        def emit_error(self, message, to_exit = True):
                if not self.mute:
                        pretty_printer(put_text = "{reverse}{red}{bold}%s{end}" %message, to_exit = True)

def server_daemon():
        if 'etrigan' in srv_config.values():
                path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pykms_config.pickle')

                if srv_config['operation'] in ['stop', 'restart', 'status'] and len(sys.argv[1:]) > 2:
                        pretty_printer(put_text = "{reverse}{red}{bold}too much arguments with etrigan '%s'. Exiting...{end}" %srv_config['operation'],
                                       to_exit = True)

                # Check file arguments.
                Etrigan_Check().checkfile(srv_config['etriganpid'], '--etrigan-pid', '.pid')
                Etrigan_Check().checkfile(srv_config['etriganlog'], '--etrigan-log', '.log')

                if srv_config['gui']:
                        pass
                else:
                        if srv_config['operation'] == 'start':
                                with open(path, 'wb') as file:
                                        pickle.dump(srv_config, file, protocol = pickle.HIGHEST_PROTOCOL)
                        elif srv_config['operation'] in ['stop', 'status', 'restart']:
                                with open(path, 'rb') as file:
                                        old_srv_config = pickle.load(file)
                                old_srv_config = {x: old_srv_config[x] for x in old_srv_config if x not in ['operation']}
                                srv_config.update(old_srv_config)

                serverdaemon = Etrigan(srv_config['etriganpid'],
                                       logfile = srv_config['etriganlog'], loglevel = srv_config['etriganlev'],
                                       mute = srv_config['etriganmute'], pause_loop = None)

                if srv_config['operation'] == 'start':
                        serverdaemon.want_quit = True
                        if srv_config['gui']:
                                serverdaemon.funcs_to_daemonize = [server_with_gui]
                        else:
                                server_without_gui = ServerWithoutGui()
                                serverdaemon.funcs_to_daemonize = [server_without_gui.start, server_without_gui.join]
                                indx_for_clean = lambda: (0, )
                                serverdaemon.quit_on_stop = [indx_for_clean, server_without_gui.clean]

                Etrigan_job(srv_config['operation'], serverdaemon)

def server_check():
        # Setup and some checks.
        check_setup(srv_config, srv_options, loggersrv, where = "srv")

        # Random HWID.
        if srv_config['hwid'] == "RANDOM":
                randomhwid = uuid.uuid4().hex
                srv_config['hwid'] = randomhwid[:16]
           
        # Sanitize HWID.
        hexstr = srv_config['hwid']
        # Strip 0x from the start of hexstr
        if hexstr.startswith("0x"):
            hexstr = hexstr[2:]

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


        # Check other specific server options.
        list_dest = ['clientcount', 'timeoutidle']
        list_opt = ['-c/--client-count', '-t0/--timeout-idle']

        if serverthread.with_gui:
                list_dest += ['activation', 'renewal']
                list_opt += ['-a/--activation-interval', '-r/--renewal-interval']

        for dest, opt in zip(list_dest, list_opt):
                value = srv_config[dest]
                if (value is not None) and (not isinstance(value, int)):
                        pretty_printer(log_obj = loggersrv.error, to_exit = True,
                                       put_text = "{reverse}{red}{bold}argument `%s`: invalid with: '%s'. Exiting...{end}" %(opt, value))

def server_create():
        try:
                server = KeyServer((srv_config['ip'], srv_config['port']), kmsServerHandler)
        except (socket.gaierror, socket.error) as e:
                pretty_printer(log_obj = loggersrv.error, to_exit = True,
                               put_text = "{reverse}{red}{bold}Connection failed '%s:%d': %s. Exiting...{end}" %(srv_config['ip'],
                                                                                                                srv_config['port'],
                                                                                                                str(e)))
        server.timeout = srv_config['timeoutidle']
        loggersrv.info("TCP server listening at %s on port %d." % (srv_config['ip'], srv_config['port']))
        loggersrv.info("HWID: %s" % deco(binascii.b2a_hex(srv_config['hwid']), 'utf-8').upper())
        return server

def server_terminate(generic_srv, exit_server = False, exit_thread = False):
        if exit_server:
                generic_srv.terminate_serve()
        if exit_thread:
                generic_srv.terminate_thread()

class ServerWithoutGui(object):
        def start(self):
                import queue as Queue
                daemon_queue = Queue.Queue(maxsize = 0)
                daemon_serverthread = server_thread(daemon_queue, name = "Thread-Srv-Daemon")
                daemon_serverthread.setDaemon(True)
                # options already checked in `server_main_terminal`.
                daemon_serverthread.checked = True
                daemon_serverthread.start()
                daemon_queue.put('start')
                return 0, daemon_serverthread

        def join(self, daemon_serverthread):
                while daemon_serverthread.is_alive():
                        daemon_serverthread.join(timeout = 0.5)

        def clean(self, daemon_serverthread):
                server_terminate(daemon_serverthread, exit_server = True, exit_thread = True)

def server_main_terminal():
        # Parse options.
        server_options()
        # Check options.
        server_check()
        serverthread.checked = True

        if 'etrigan' not in srv_config.values():
                # (without GUI) and (without daemon).
                # Run threaded server.
                serverqueue.put('start')
                # Wait to finish.
                try:
                        while serverthread.is_alive():
                                serverthread.join(timeout = 0.5)
                except (KeyboardInterrupt, SystemExit):
                        server_terminate(serverthread, exit_server = True, exit_thread = True)
        else:
                # (with or without GUI) and (with daemon)
                # Setup daemon (eventually).
                server_daemon()

def server_with_gui():
        import pykms_GuiBase

        root = pykms_GuiBase.KmsGui()
        root.title(pykms_GuiBase.gui_description + ' (' + pykms_GuiBase.gui_version + ')')
        root.mainloop()

def server_main_no_terminal():
        # Run tkinter GUI.
        # (with GUI) and (without daemon).
        server_with_gui()

class kmsServerHandler(socketserver.BaseRequestHandler):
        def setup(self):
                loggersrv.info("Connection accepted: %s:%d" %(self.client_address[0], self.client_address[1]))

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
                loggersrv.info("Connection closed: %s:%d" %(self.client_address[0], self.client_address[1]))


serverqueue = Queue.Queue(maxsize = 0)
serverthread = server_thread(serverqueue, name = "Thread-Srv")
serverthread.setDaemon(True)
serverthread.start()

if __name__ == "__main__":
        if sys.stdout.isatty():
                server_main_terminal()
        else:
                try:
                        server_main_no_terminal()
                except:
                        server_main_terminal()
