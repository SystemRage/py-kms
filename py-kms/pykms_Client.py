#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import binascii
import datetime
import random
import socket
import string
import sys
import uuid
import logging
import os
import threading

import dns.message
import dns.rdataclass
import dns.rdatatype
import dns.query
import dns.resolver

import pykms_RpcBind, pykms_RpcRequest
from pykms_Filetimes import dt_to_filetime
from pykms_Dcerpc import MSRPCHeader, MSRPCBindNak, MSRPCRequestHeader, MSRPCRespHeader
from pykms_Base import kmsBase, UUID
from pykms_RequestV4 import kmsRequestV4
from pykms_RequestV5 import kmsRequestV5
from pykms_RequestV6 import kmsRequestV6
from pykms_RpcBase import rpcBase
from pykms_DB2Dict import kmsDB2Dict
from pykms_Misc import check_setup, check_other
from pykms_Misc import KmsParser, KmsParserException, KmsParserHelp
from pykms_Misc import kms_parser_get, kms_parser_check_optionals, kms_parser_check_positionals
from pykms_Format import justify, byterize, enco, deco, pretty_printer

clt_version             = "py-kms_2020-07-01"
__license__             = "The Unlicense"
__author__              = u"Matteo ℱan <SystemRage@protonmail.com>"
__url__                 = "https://github.com/SystemRage/py-kms"
clt_description         = "py-kms: KMS Client Emulator written in Python"
clt_config = {}

#---------------------------------------------------------------------------------------------------------------------------------------------------------
class client_thread(threading.Thread):
        def __init__(self, name):
                threading.Thread.__init__(self)
                self.name = name
                self.with_gui = False

        def run(self):
                clt_main(with_gui = self.with_gui)

#---------------------------------------------------------------------------------------------------------------------------------------------------------

loggerclt = logging.getLogger('logclt')

# 'help' string - 'default' value - 'dest' string.
clt_options = {
        'ip'       : {'help' : 'The IP address or hostname of the KMS server.', 'def' : "0.0.0.0", 'des' : "ip"},
        'port'     : {'help' : 'The port the KMS service is listening on. The default is \"1688\".', 'def' : 1688, 'des' : "port"},
        'mode'     : {'help' : 'Use this flag to manually specify a Microsoft product for testing the server. The default is \"Windows81\"',
                      'def' : "Windows8.1", 'des' : "mode",
                      'choi' : ["WindowsVista","Windows7","Windows8","Windows8.1","Windows10","Office2010","Office2013","Office2016","Office2019"]},
        'cmid'     : {'help' : 'Use this flag to manually specify a CMID to use. If no CMID is specified, a random CMID will be generated.',
                      'def' : None, 'des' : "cmid"},
        'name'     : {'help' : 'Use this flag to manually specify an ASCII machine name to use. If no machine name is specified a random one \
will be generated.', 'def' : None, 'des' : "machine"},
        'time0'    : {'help' : 'Set the maximum time to wait for a connection attempt to KMS server to succeed. Default is no timeout.',
                      'def' : None, 'des' : "timeoutidle"},
        'time1'    : {'help' : 'Set the maximum time to wait for sending / receiving a request / response. Default is no timeout.',
                      'def' : None, 'des' : "timeoutsndrcv"},
        'asyncmsg' : {'help' : 'Prints pretty / logging messages asynchronously. Deactivated by default.',
                      'def' : False, 'des' : "asyncmsg"},
        'llevel'   : {'help' : 'Use this option to set a log level. The default is \"ERROR\".', 'def' : "ERROR", 'des' : "loglevel",
                      'choi' : ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "MININFO"]},
        'lfile'    : {'help' : 'Use this option to set an output log file. The default is \"pykms_logclient.log\". \
Type \"STDOUT\" to view log info on stdout. Type \"FILESTDOUT\" to combine previous actions. \
Use \"STDOUTOFF\" to disable stdout messages. Use \"FILEOFF\" if you not want to create logfile.',
                      'def' : os.path.join('.', 'pykms_logclient.log'), 'des' : "logfile"},
        'lsize'    : {'help' : 'Use this flag to set a maximum size (in MB) to the output log file. Deactivated by default.', 'def' : 0, 'des': "logsize"},
        'discovery' : {'help': 'ask the client to perform a _vlmcs._tcp.domain.tld DNS request to set KMS server.', 'def': None , 'des': 'discovery' },
        }

def client_options():
        client_parser = KmsParser(description = clt_description, epilog = 'version: ' + clt_version, add_help = False)
        client_parser.add_argument("ip", nargs = "?", action = "store", default = clt_options['ip']['def'],
                                   help = clt_options['ip']['help'], type = str)
        client_parser.add_argument("port", nargs = "?", action = "store", default = clt_options['port']['def'],
                                   help = clt_options['port']['help'], type = int)
        client_parser.add_argument("-m", "--mode", dest = clt_options['mode']['des'], default = clt_options['mode']['def'],
                                   choices = clt_options['mode']['choi'], help = clt_options['mode']['help'], type = str)
        client_parser.add_argument("-c", "--cmid", dest = clt_options['cmid']['des'], default = clt_options['cmid']['def'],
                                   help = clt_options['cmid']['help'], type = str)
        client_parser.add_argument("-n", "--name", dest = clt_options['name']['des'] , default = clt_options['name']['def'],
                                   help = clt_options['name']['help'], type = str)
        client_parser.add_argument("-t0", "--timeout-idle", action = "store", dest = clt_options['time0']['des'], default = clt_options['time0']['def'],
                                   help = clt_options['time0']['help'], type = str)
        client_parser.add_argument("-t1", "--timeout-sndrcv", action = "store", dest = clt_options['time1']['des'], default = clt_options['time1']['def'],
                                   help = clt_options['time1']['help'], type = str)
        client_parser.add_argument("-y", "--async-msg", action = "store_true", dest = clt_options['asyncmsg']['des'],
                                   default = clt_options['asyncmsg']['def'], help = clt_options['asyncmsg']['help'])
        client_parser.add_argument("-V", "--loglevel", dest = clt_options['llevel']['des'], action = "store",
                                   choices = clt_options['llevel']['choi'], default = clt_options['llevel']['def'],
                                   help = clt_options['llevel']['help'], type = str)
        client_parser.add_argument("-F", "--logfile", nargs = "+", action = "store", dest = clt_options['lfile']['des'],
                                   default = clt_options['lfile']['def'], help = clt_options['lfile']['help'], type = str)
        client_parser.add_argument("-S", "--logsize", dest = clt_options['lsize']['des'], action = "store",
                                   default = clt_options['lsize']['def'], help = clt_options['lsize']['help'], type = float)
        client_parser.add_argument("-D", "--discovery", dest = clt_options['discovery']['des'], action = "store",
                                   default = clt_options['discovery']['def'], help = clt_options['discovery']['help'], type = str)

        client_parser.add_argument("-h", "--help", action = "help", help = "show this help message and exit")

        try:
                userarg = sys.argv[1:]

                # Run help.
                if any(arg in ["-h", "--help"] for arg in userarg):
                        KmsParserHelp().printer(parsers = [client_parser])

                # Get stored arguments.
                pykmsclt_zeroarg, pykmsclt_onearg = kms_parser_get(client_parser)
                # Update pykms options for dict client config.
                kms_parser_check_optionals(userarg, pykmsclt_zeroarg, pykmsclt_onearg, msg = 'optional py-kms client',
                                           exclude_opt_len = ['-F', '--logfile'])
                kms_parser_check_positionals(clt_config, client_parser.parse_args, msg = 'positional py-kms client')

        except KmsParserException as e:
                pretty_printer(put_text = "{reverse}{red}{bold}%s. Exiting...{end}" %str(e), to_exit = True, where = "clt")

def client_check():
        # Setup and some checks.
        check_setup(clt_config, clt_options, loggerclt, where = "clt")

        # Check cmid.
        if clt_config['cmid'] is not None:
                try:
                        uuid.UUID(clt_config['cmid'])
                except ValueError:
                        pretty_printer(log_obj = loggerclt.error, to_exit = True, where = "clt",
                                       put_text = "{reverse}{red}{bold}argument `-c/--cmid`: invalid with: '%s'. Exiting...{end}" %clt_config['cmid'])

        # Check machine name.
        if clt_config['machine'] is not None:
                try:
                        clt_config['machine'].encode('utf-16le')

                        if len(clt_config['machine']) < 2:
                                pretty_printer(log_obj = loggerclt.error, to_exit = True, where = "clt",
                                               put_text = "{reverse}{red}{bold}argument `-n/--name`: too short (required 2 - 63 chars). Exiting...{end}")
                        elif len(clt_config['machine']) > 63:
                                pretty_printer(log_obj = loggerclt.error, to_exit = True, where = "clt",
                                               put_text = "{reverse}{red}{bold}argument `-n/--name`: too long (required 2 - 63 chars). Exiting...{end}")
                except UnicodeEncodeError:
                        pretty_printer(log_obj = loggerclt.error, to_exit = True, where = "clt",
                                       put_text = "{reverse}{red}{bold}argument `-n/--name`: invalid with: '%s'. Exiting...{end}" %clt_config['machine'])
                        
        clt_config['call_id'] = 1

        # Check other specific client options.
        opts = [('timeoutidle', '-t0/--timeout-idle'),
                ('timeoutsndrcv', '-t1/--timeout-sndrcv')]
        check_other(clt_config, opts, loggerclt, where = 'clt')

def client_update():
        kmsdb = kmsDB2Dict()

        loggerclt.debug(f'Searching in kms database for machine "{clt_config["mode"]}"...')

        appitems = kmsdb[2]
        for appitem in appitems:
                kmsitems = appitem['KmsItems']
                for kmsitem in kmsitems:                                
                        name = re.sub('\(.*\)', '', kmsitem['DisplayName']) # Remove bracets
                        name = name.replace('2015', '') # Remove specific years
                        name = name.replace(' ', '') # Ignore whitespaces
                        name = name.replace('/11', '', 1) # Cut out Windows 11, as it is basically Windows 10
                        if name == clt_config['mode']:
                                skuitems = kmsitem['SkuItems']
                                # Select 'Enterprise' for Windows or 'Professional Plus' for Office.
                                for skuitem in skuitems:
                                        sName = skuitem['DisplayName']
                                        sName = sName.replace(' ', '') # Ignore whitespaces
                                        sName = sName.replace('/11', '', 1) # Cut out Windows 11, as it is basically Windows 10
                                        if sName == name + 'Enterprise' or \
                                           sName == name[:6] + 'ProfessionalPlus' + name[6:]:
                                                clt_config['KMSClientSkuID'] = skuitem['Id']
                                                clt_config['RequiredClientCount'] = int(kmsitem['NCountPolicy'])
                                                clt_config['KMSProtocolMajorVersion'] = int(float(kmsitem['DefaultKmsProtocol']))
                                                clt_config['KMSProtocolMinorVersion'] = 0
                                                clt_config['KMSClientLicenseStatus'] = 2
                                                clt_config['KMSClientAppID'] = appitem['Id']
                                                clt_config['KMSClientKMSCountedID'] = kmsitem['Id']
                                                return
        raise RuntimeError(f'Client failed to find machine configuration in kms database - make sure it contains an entry for "{clt_config["mode"]}"')

def client_connect():

        if clt_config['discovery'] is not None:
          loggerclt.info(f'Using Domain: {clt_config["discovery"]}')
          r= None
          try:
            r = dns.resolver.resolve('_vlmcs._tcp.' + clt_config['discovery'], dns.rdatatype.SRV)
            for a in r:
              loggerclt.debug(f'answer KMS server: {a.target} , port: {a.port}')
            clt_config['ip'] = socket.gethostbyname(r[0].target.to_text())
            clt_config['port'] = r[0].port
          except (dns.exception.Timeout, dns.resolver.NXDOMAIN) as e:
                pretty_printer(log_obj = loggerclt.warning,
                           put_text = "{reverse}{red}{bold}Cannot resolve '%s'. Error: '%s'...{end}" %(clt_config['discovery'],
                                                                                                             str(e)))

        loggerclt.info("Connecting to %s on port %d" % (clt_config['ip'], clt_config['port']))
        try:
                clt_sock = socket.create_connection((clt_config['ip'], clt_config['port']), timeout = clt_config['timeoutidle'])
                loggerclt.info("Connection successful !")
                clt_sock.settimeout(clt_config['timeoutsndrcv'])
        except socket.timeout:
                pretty_printer(log_obj = loggerclt.error, to_exit = True, where = "clt",
                               put_text = "{reverse}{red}{bold}Client connection timed out. Exiting...{end}")
        except (socket.gaierror, socket.error) as e:
                pretty_printer(log_obj = loggerclt.error, to_exit = True, where = "clt",
                               put_text = "{reverse}{red}{bold}Connection failed '%s:%d': %s. Exiting...{end}" %(clt_config['ip'],
                                                                                                                 clt_config['port'],
                                                                                                                 str(e)))
        return clt_sock

def client_create(clt_sock):
        binder = pykms_RpcBind.handler(None, clt_config)
        RPC_Bind = enco(str(binder.generateRequest()), 'latin-1')

        try:
                loggerclt.info("Sending RPC bind request...")
                pretty_printer(num_text = [-1, 1], where = "clt")
                clt_sock.send(RPC_Bind)
        except socket.error as e:
                pretty_printer(log_obj = loggerclt.error, to_exit = True, where = "clt",
                               put_text = "{reverse}{red}{bold}While sending: %s. Exiting...{end}" %str(e))
        try:
                bindResponse = clt_sock.recv(1024)
                if bindResponse == '' or not bindResponse:
                        pretty_printer(log_obj = loggerclt.warning, to_exit = True, where = "clt",
                                       put_text = "{reverse}{yellow}{bold}No data received. Exiting...{end}")
                pretty_printer(num_text = [-4, 7], where = "clt")
        except socket.error as e:
                pretty_printer(log_obj = loggerclt.error, to_exit = True, where = "clt",
                               put_text = "{reverse}{red}{bold}While receiving: %s. Exiting...{end}" %str(e))

        packetType = MSRPCHeader(bindResponse)['type']
        if packetType == rpcBase.packetType['bindAck']:
                loggerclt.info("RPC bind acknowledged.")
                pretty_printer(num_text = 8, where = "clt")
                kmsRequest = createKmsRequest()
                requester = pykms_RpcRequest.handler(kmsRequest, clt_config)

                try:
                        loggerclt.info("Sending RPC activation request...")
                        RPC_Actv = enco(str(requester.generateRequest()), 'latin-1')
                        pretty_printer(num_text = [-1, 12], where = "clt")
                        clt_sock.send(RPC_Actv)
                except socket.error as e:
                        pretty_printer(log_obj = loggerclt.error, to_exit = True, where = "clt",
                                       put_text = "{reverse}{red}{bold}While sending: %s. Exiting...{end}" %str(e))
                try:
                        response = clt_sock.recv(1024)
                        pretty_printer(num_text = [-4, 20], where = "clt")
                except socket.error as e:
                        pretty_printer(log_obj = loggerclt.error, to_exit = True, where = "clt",
                                       put_text = "{reverse}{red}{bold}While receiving: %s. Exiting...{end}" %str(e))

                loggerclt.debug("Response: \n%s\n" % justify(deco(binascii.b2a_hex(response), 'latin-1')))
                parsed = MSRPCRespHeader(response)
                kmsData = readKmsResponse(parsed['pduData'], kmsRequest, clt_config)
                kmsResp = kmsData['response']
                
                try:
                        hwid = kmsData['hwid']
                        loggerclt.info("KMS Host HWID: %s" % deco(binascii.b2a_hex(enco(hwid, 'latin-1')).upper(), 'utf-8'))
                except KeyError:
                        pass
                loggerclt.info("KMS Host ePID: %s" % kmsResp['kmsEpid'].encode('utf-8').decode('utf-16le'))
                loggerclt.info("KMS Host Current Client Count: %s" % kmsResp['currentClientCount'])
                loggerclt.info("KMS VL Activation Interval: %s" % kmsResp['vLActivationInterval'])
                loggerclt.info("KMS VL Renewal Interval: %s" % kmsResp['vLRenewalInterval'])
                
                if clt_config['loglevel'] == 'MININFO':
                        loggerclt.mininfo("", extra = {'host': str(clt_sock.getpeername()),
                                                       'status' : kmsBase.licenseStates[requester.srv_config['KMSClientLicenseStatus']],
                                                       'product' : clt_config["mode"]})

                pretty_printer(num_text = 21, where = "clt")
                
        elif packetType == rpcBase.packetType['bindNak']:
                loggerclt.info(justify(MSRPCBindNak(bindResponse).dump(print_to_stdout = False)))
                sys.exit(0)
        else:
                pretty_printer(log_obj = loggerclt.warning, to_exit = True, where = "clt",
                               put_text = "{reverse}{magenta}{bold}Something went wrong. Exiting...{end}")

def clt_main(with_gui = False):
        try:
                if not with_gui:
                        # Parse options.
                        client_options()

                # Check options.
                client_check()
                # Update Config.
                client_update()
                # Create and run client.
                clt_sock = client_connect()
                client_create(clt_sock)
        except (KeyboardInterrupt, SystemExit):
                try:
                        clt_sock.shutdown(socket.SHUT_RDWR)
                        clt_sock.close()
                except:
                        pass

def createKmsRequestBase():
        requestDict = kmsBase.kmsRequestStruct()
        requestDict['versionMinor'] = clt_config['KMSProtocolMinorVersion']
        requestDict['versionMajor'] = clt_config['KMSProtocolMajorVersion']
        requestDict['isClientVm'] = 0
        requestDict['licenseStatus'] = clt_config['KMSClientLicenseStatus']
        requestDict['graceTime'] = 43200
        requestDict['applicationId'] = UUID(uuid.UUID(clt_config['KMSClientAppID']).bytes_le)
        requestDict['skuId'] = UUID(uuid.UUID(clt_config['KMSClientSkuID']).bytes_le)
        requestDict['kmsCountedId'] = UUID(uuid.UUID(clt_config['KMSClientKMSCountedID']).bytes_le)
        requestDict['clientMachineId'] = UUID(uuid.UUID(clt_config['cmid']).bytes_le if (clt_config['cmid'] is not None) else uuid.uuid4().bytes_le)
        requestDict['previousClientMachineId'] = '\0' * 16 # I'm pretty sure this is supposed to be a null UUID.
        requestDict['requiredClientCount'] = clt_config['RequiredClientCount']
        requestDict['requestTime'] = dt_to_filetime(datetime.datetime.utcnow())
        requestDict['machineName'] = (clt_config['machine'] if (clt_config['machine'] is not None) else
                                      ''.join(random.choice(string.ascii_letters + string.digits) for i in range(random.randint(2,63)))).encode('utf-16le')
        requestDict['mnPad'] = '\0'.encode('utf-16le') * (63 - len(requestDict['machineName'].decode('utf-16le')))
        
        # Debug Stuff
        pretty_printer(num_text = 9, where = "clt")
        requestDict = byterize(requestDict)
        loggerclt.debug("Request Base Dictionary: \n%s\n" % justify(requestDict.dump(print_to_stdout = False)))

        return requestDict

def createKmsRequest():
        # Update the call ID
        clt_config['call_id'] += 1

        # KMS Protocol Major Version
        if clt_config['KMSProtocolMajorVersion'] == 4:
                handler = kmsRequestV4(None, clt_config)
        elif clt_config['KMSProtocolMajorVersion'] == 5:
                handler = kmsRequestV5(None, clt_config)
        elif clt_config['KMSProtocolMajorVersion'] == 6:
                handler = kmsRequestV6(None, clt_config)
        else:
                return None

        requestBase = createKmsRequestBase()
        return handler.generateRequest(requestBase)

def readKmsResponse(data, request, clt_config):
        if clt_config['KMSProtocolMajorVersion'] == 4:
                loggerclt.info("Received V4 response")
                response = readKmsResponseV4(data, request)
        elif clt_config['KMSProtocolMajorVersion'] == 5:
                loggerclt.info("Received V5 response")
                response = readKmsResponseV5(data)
        elif clt_config['KMSProtocolMajorVersion'] == 6:
                loggerclt.info("Received V6 response")
                response = readKmsResponseV6(data)
        else:
                loggerclt.info("Unhandled response version: %d.%d" % (clt_config['KMSProtocolMajorVersion'], clt_config['KMSProtocolMinorVersion']))
                loggerclt.info("I'm not even sure how this happened...")
        return response

def readKmsResponseV4(data, request):
        response = kmsRequestV4.ResponseV4(data)
        hashed = kmsRequestV4(data, clt_config).generateHash(bytearray(enco(str(response['response']) , 'latin-1')))
        if deco(hashed, 'latin-1') == response['hash']:
                loggerclt.info("Response Hash has expected value !")
        return response

def readKmsResponseV5(data):
        response = kmsRequestV5.ResponseV5(data)
        decrypted = kmsRequestV5(data, clt_config).decryptResponse(response)
        return decrypted

def readKmsResponseV6(data):
        response = kmsRequestV6.ResponseV5(data)
        decrypted = kmsRequestV6(data, clt_config).decryptResponse(response)
        message = decrypted['message']
        return message

if __name__ == "__main__":
        clt_main(with_gui = False)
