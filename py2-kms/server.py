#!/usr/bin/env python

import argparse
import binascii
import re
import sys
import socket
import SocketServer
import uuid
import logging
import os
import errno

import rpcBind, rpcRequest
from dcerpc import MSRPCHeader
from rpcBase import rpcBase
from formatText import shell_message
from logging.handlers import RotatingFileHandler

config = {}

logger = logging.getLogger('root')

# Valid language identifiers to be used in the EPID (see "kms.c" in vlmcsd)
ValidLcid = [1025, 1026, 1027, 1028, 1029,
             1030, 1031, 1032, 1033, 1034, 1035, 1036, 1037, 1038, 1039,
             1040, 1041, 1042, 1043, 1044, 1045, 1046, 1048, 1049,
             1050, 1051, 1052, 1053, 1054, 1056, 1057, 1058, 1059,
             1060, 1061, 1062, 1063, 1065, 1066, 1067, 1068, 1069,
             1071, 1074, 1076, 1077, 1078, 1079,
             1080, 1081, 1082, 1083, 1086, 1087, 1088, 1089,
             1091, 1092, 1093, 1094, 1095, 1097, 1098, 1099,
             1100, 1102, 1103, 1104, 1106, 1110, 1111, 1114, 1125, 1131, 1153,
             2049, 2052, 2055, 2057, 2058, 2060, 2064, 2067, 2068, 2070, 2074, 2077, 2092, 2107, 2110, 2115, 2155,
             3073, 3076, 3079, 3081, 3082, 3084, 3098, 3131, 3179,
             4097, 4100, 4103, 4105, 4106, 4108, 4122, 4155,
             5121, 5124, 5127, 5129, 5130, 5132, 5146, 5179,
             6145, 6153, 6154, 6156, 6170, 6203,
             7169, 7177, 7178, 7194, 7227,
             8193, 8201, 8202, 8251,
             9217, 9225, 9226, 9275,
             10241, 10249, 10250, 11265, 11273, 11274, 12289, 12297, 12298,
             13313, 13321, 13322, 14337, 14346, 15361, 15370, 16385, 16394, 17418, 18442, 19466, 20490]

def createLogger(config):
        logger.setLevel(config['loglevel'])

        log_formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S')
        log_handler = RotatingFileHandler(filename=config['logfile'], mode='a', maxBytes=int(config['logsize']*1024*512), backupCount=1, encoding=None, delay=0)
        print int(config['logsize']*1024*512)
        log_handler.setFormatter(log_formatter)
        
        logger.addHandler(log_handler)

def main():
        parser = argparse.ArgumentParser(description='py2-kms: KMS Server Emulator written in Python2', epilog="version: py2-kms_2018-11-15")
        parser.add_argument("ip", nargs="?", action="store", default="0.0.0.0",
                            help='The IP address to listen on. The default is \"0.0.0.0\" (all interfaces).', type=str)
        parser.add_argument("port", nargs="?", action="store", default=1688,
                            help='The network port to listen on. The default is \"1688\".', type=int)
        parser.add_argument("-e", "--epid", dest="epid", default=None,
                            help='Use this flag to manually specify an ePID to use. If no ePID is specified, a random ePID will be generated.', type=str)
        parser.add_argument("-l", "--lcid", dest="lcid", default=1033,
                            help='Use this flag to manually specify an LCID for use with randomly generated ePIDs. Default is 1033 (en-us)', type=int)
        parser.add_argument("-c", "--client-count", dest="CurrentClientCount", default=26,
                            help='Use this flag to specify the current client count. Default is 26. A number >=25 is required to enable \
activation of client OSes; for server OSes and Office >=5', type=int)
        parser.add_argument("-a", "--activation-interval", dest="VLActivationInterval", default=120,
                            help='Use this flag to specify the activation interval (in minutes). Default is 120 minutes (2 hours).', type=int)
        parser.add_argument("-r", "--renewal-interval", dest="VLRenewalInterval", default=1440 * 7,
                            help='Use this flag to specify the renewal interval (in minutes). Default is 10080 minutes (7 days).', type=int)
        parser.add_argument("-s", "--sqlite", dest="sqlite", action="store_const", const=True, default=False,
                            help='Use this flag to store request information from unique clients in an SQLite database.')
        parser.add_argument("-w", "--hwid", dest="hwid", action="store", default='364F463A8863D35F',
                            help='Use this flag to specify a HWID. The HWID must be an 16-character string of hex characters. \
The default is \"364F463A8863D35F\" or type \"random\" to auto generate the HWID.', type=str)   
        parser.add_argument("-v", "--loglevel", dest="loglevel", action="store", default="ERROR", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
                            help='Use this flag to set a Loglevel. The default is \"ERROR\".', type=str)
        parser.add_argument("-f", "--logfile", dest="logfile", action="store", default=os.path.dirname(os.path.abspath( __file__ )) + "/py2kms_server.log",
                            help='Use this flag to set an output Logfile. The default is \"pykms_server.log\".', type=str)
        parser.add_argument("-S", "--logsize", dest="logsize", action="store", default=0,
                            help='Use this flag to set a maximum size (in MB) to the output Logfile. Desactivated by default.', type=float)
        
        config.update(vars(parser.parse_args()))

        createLogger(config)

        # Random HWID.
        if config['hwid'] == "random":
                randomhwid = uuid.uuid4().hex
                config['hwid'] = randomhwid[:16]
        
        # Sanitize HWID.
        try:
                config['hwid'] = binascii.a2b_hex(re.sub(r'[^0-9a-fA-F]', '', config['hwid'].strip('0x')))
                if len(binascii.b2a_hex(config['hwid'])) < 16:
                        logger.error("Error: HWID \"%s\" is invalid. Hex string is too short." % binascii.b2a_hex(config['hwid']).upper())
                        return
                elif len(binascii.b2a_hex(config['hwid'])) > 16:
                        logger.error("Error: HWID \"%s\" is invalid. Hex string is too long." % binascii.b2a_hex(config['hwid']).upper())
                        return
        except TypeError:
                logger.error("Error: HWID \"%s\" is invalid. Odd-length hex string." % binascii.b2a_hex(config['hwid']).upper())
                return
        
        # Check LCID.
        # http://stackoverflow.com/questions/3425294/how-to-detect-the-os-default-language-in-python
	if not config['lcid'] or (config['lcid'] not in ValidLcid):		
		if hasattr(sys, 'implementation') and sys.implementation.name == 'cpython':
			config['lcid'] = 1033
		elif os.name == 'nt':
			import ctypes

			config['lcid'] = ctypes.windll.kernel32.GetUserDefaultUILanguage()  # TODO: or GetSystemDefaultUILanguage?
		else:
			import locale

			try:
				config['lcid'] = next(k for k, v in locale.windows_locale.items() if v == locale.getdefaultlocale()[0])
			except StopIteration:
				config['lcid'] = 1033

        try:
                import sqlite3            
        except:
                logger.warning("Module \"sqlite3\" is not installed, database support disabled.")
                config['dbSupport'] = False
        else:
                config['dbSupport'] = True
                
        server = SocketServer.TCPServer((config['ip'], config['port']), kmsServer)
        server.timeout = 5
        logger.info("TCP server listening at %s on port %d." % (config['ip'], config['port']))
        logger.info("HWID: %s" % binascii.b2a_hex(config['hwid']).upper())
        server.serve_forever()
        

class kmsServer(SocketServer.BaseRequestHandler):
        def setup(self):
                logger.info("Connection accepted: %s:%d" % (self.client_address[0], self.client_address[1]))

        def handle(self):
                while True:
                        # self.request is the TCP socket connected to the client
                        try:
                                data = self.request.recv(1024)
                        except socket.error, e:
                                if e.errno == errno.ECONNRESET:
                                        logger.error("Connection reset by peer.")
                                        break
                                else:
                                        raise
                        if not data:
                                logger.warning("No data received !")
                                break
                        # data = bytearray(self.data.strip())
                        # logger.debug(binascii.b2a_hex(str(data)))
                        packetType = MSRPCHeader(data)['type']
                        if packetType == rpcBase.packetType['bindReq']:
                                logger.info("RPC bind request received.")
                                shell_message(nshell = [-2, 2])
                                handler = rpcBind.handler(data, config)
                        elif packetType == rpcBase.packetType['request']:
                                logger.info("Received activation request.")
                                shell_message(nshell = [-2, 13])
                                handler = rpcRequest.handler(data, config)
                        else:
                                logger.error("Error: Invalid RPC request type ", packetType)
                                break

                        res = str(handler.populate())
                        self.request.send(res)

                        if packetType == rpcBase.packetType['bindReq']:
                                logger.info("RPC bind acknowledged.")
                                shell_message(nshell = [-3, 5, 6])
                        elif packetType == rpcBase.packetType['request']:
                                logger.info("Responded to activation request.")
                                shell_message(nshell = [-3, 18, 19])
                                break

        def finish(self):
                self.request.close()
                logger.info("Connection closed: %s:%d" % (self.client_address[0], self.client_address[1]))
                
if __name__ == "__main__":
        main()
