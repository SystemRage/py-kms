#!/usr/bin/env python

import argparse
import binascii
import hashlib
import random
import re
import socket
import SocketServer
import struct
import uuid
import logging
import os

import rpcBind, rpcRequest
from dcerpc import MSRPCHeader
from rpcBase import rpcBase
from formatText import shell_message

config = {}

def main():
        parser = argparse.ArgumentParser(description='py2-kms: KMS Server Emulator written in Python2', epilog="version: py2-kms_2018-03-01")
        parser.add_argument("ip", nargs="?", action="store", default="0.0.0.0",
                            help='The IP address to listen on. The default is \"0.0.0.0\" (all interfaces).', type=str)
        parser.add_argument("port", nargs="?", action="store", default=1688,
                            help='The network port to listen on. The default is \"1688\".', type=int)
        parser.add_argument("-e", "--epid", dest="epid", default=None,
                            help='Use this flag to manually specify an ePID to use. If no ePID is specified, a random ePID will be generated.', type=str)
        parser.add_argument("-l", "--lcid", dest="lcid", default=1033,
                            help='Use this flag to manually specify an LCID for use with randomly generated ePIDs. If an ePID is manually specified,\
this setting is ignored.', type=int)
        parser.add_argument("-c", "--client-count", dest="CurrentClientCount", default=26,
                            help='Use this flag to specify the current client count. Default is 26. A number >25 is required to enable activation.', type=int)
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
        
        config.update(vars(parser.parse_args()))
        #Random HWID
        if config['hwid'] == "random":
                randomhwid = uuid.uuid4().hex
                config['hwid'] = randomhwid[:16]
        
        # Sanitize HWID
        try:
                config['hwid'] = binascii.a2b_hex(re.sub(r'[^0-9a-fA-F]', '', config['hwid'].strip('0x')))
                if len(binascii.b2a_hex(config['hwid'])) < 16:
                        logging.error("HWID \"%s\" is invalid. Hex string is too short." % binascii.b2a_hex(config['hwid']).upper())
                        return
                elif len(binascii.b2a_hex(config['hwid'])) > 16:
                        logging.error("HWID \"%s\" is invalid. Hex string is too long." % binascii.b2a_hex(config['hwid']).upper())
                        return
        except TypeError:
                logging.error("HWID \"%s\" is invalid. Odd-length hex string." % binascii.b2a_hex(config['hwid']).upper())
                return

        logging.basicConfig(level=config['loglevel'], format='%(asctime)s %(levelname)-8s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S', filename=config['logfile'], filemode='w')
        
        try:
                import sqlite3
                config['dbSupport'] = True
        except:
                logging.warning("Module \"sqlite3\" is not installed, database support disabled.")
                config['dbSupport'] = False
        server = SocketServer.TCPServer((config['ip'], config['port']), kmsServer)
        server.timeout = 5
        logging.info("TCP server listening at %s on port %d." % (config['ip'], config['port']))
        logging.info("HWID: %s" % binascii.b2a_hex(config['hwid']).upper())
        server.serve_forever()

class kmsServer(SocketServer.BaseRequestHandler):
        def setup(self):
                self.connection = self.request
                logging.info("Connection accepted: %s:%d" % (self.client_address[0], self.client_address[1]))

        def handle(self):
                while True:
                        # self.request is the TCP socket connected to the client
                        try:
                                self.data = self.connection.recv(1024)
                        except socket.error, e:
                                if e[0] == 104:
                                        logging.error("Connection reset by peer.")
                                        break
                                else:
                                        raise
                        if self.data == '' or not self.data:
                                logging.warning("No data received !")
                                break
                        # self.data = bytearray(self.data.strip())
                        # logging.debug(binascii.b2a_hex(str(self.data)))
                        packetType = MSRPCHeader(self.data)['type']
                        if packetType == rpcBase.packetType['bindReq']:
                                logging.info("RPC bind request received.")
                                shell_message(nshell = [-2, 2])
                                handler = rpcBind.handler(self.data, config)
                        elif packetType == rpcBase.packetType['request']:
                                logging.info("Received activation request.")
                                shell_message(nshell = [-2, 13])
                                handler = rpcRequest.handler(self.data, config)
                        else:
                                logging.error("Invalid RPC request type ", packetType)
                                break

                        handler.populate()
                        res = str(handler.getResponse())
                        self.connection.send(res)

                        if packetType == rpcBase.packetType['bindReq']:
                                logging.info("RPC bind acknowledged.")
                                shell_message(nshell = [-3, 5, 6])
                        elif packetType == rpcBase.packetType['request']:
                                logging.info("Responded to activation request.")
                                shell_message(nshell = [-3, 18, 19])
                                break

        def finish(self):
                self.connection.close()
                logging.info("Connection closed: %s:%d" % (self.client_address[0], self.client_address[1]))
                
if __name__ == "__main__":
        main()
