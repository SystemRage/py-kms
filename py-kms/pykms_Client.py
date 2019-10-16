#!/usr/bin/env python3

import re
import argparse
import binascii
import datetime
import random
import socket
import string
import sys
import uuid
import logging
import os
import errno

import pykms_RpcBind, pykms_RpcRequest 
from pykms_Filetimes import dt_to_filetime
from pykms_Dcerpc import MSRPCHeader, MSRPCBindNak, MSRPCRequestHeader, MSRPCRespHeader
from pykms_Base import kmsBase, UUID
from pykms_RequestV4 import kmsRequestV4
from pykms_RequestV5 import kmsRequestV5
from pykms_RequestV6 import kmsRequestV6
from pykms_RpcBase import rpcBase
from pykms_DB2Dict import kmsDB2Dict
from pykms_Misc import logger_create, check_logfile
from pykms_Format import justify, byterize, enco, deco, ShellMessage

clt_description = 'KMS Client Emulator written in Python'
clt_version = 'py-kms_2019-05-15'
clt_config = {}

#---------------------------------------------------------------------------------------------------------------------------------------------------------

loggerclt = logging.getLogger('logclt')

# 'help' string - 'default' value - 'dest' string.
clt_options = {
        'ip' : {'help' : 'The IP address or hostname of the KMS server.', 'def' : "0.0.0.0", 'des' : "ip"},
        'port' : {'help' : 'The port the KMS service is listening on. The default is \"1688\".', 'def' : 1688, 'des' : "port"},
        'mode' : {'help' : 'Use this flag to manually specify a Microsoft product for testing the server. The default is \"Windows81\"',
                  'def' : "Windows8.1", 'des' : "mode",
                  'choi' : ["WindowsVista","Windows7","Windows8","Windows8.1","Windows10","Office2010","Office2013","Office2016","Office2019"]},
        'cmid' : {'help' : 'Use this flag to manually specify a CMID to use. If no CMID is specified, a random CMID will be generated.',
                  'def' : None, 'des' : "cmid"},
        'name' : {'help' : 'Use this flag to manually specify an ASCII machineName to use. If no machineName is specified a random machineName \
will be generated.', 'def' : None, 'des' : "machineName"},
        'llevel' : {'help' : 'Use this option to set a log level. The default is \"ERROR\".', 'def' : "ERROR", 'des' : "loglevel",
                    'choi' : ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "MINI"]},
        'lfile' : {'help' : 'Use this option to set an output log file. The default is \"pykms_logclient.log\". Type \"STDOUT\" to view \
log info on stdout. Type \"FILESTDOUT\" to combine previous actions.',
                   'def' : os.path.dirname(os.path.abspath( __file__ )) + "/pykms_logclient.log", 'des' : "logfile"},
        'lsize' : {'help' : 'Use this flag to set a maximum size (in MB) to the output log file. Desactivated by default.', 'def' : 0, 'des': "logsize"},
        }

def client_options():
        parser = argparse.ArgumentParser(description = clt_description, epilog = 'version: ' + clt_version)
        parser.add_argument("ip", nargs = "?", action = "store", default = clt_options['ip']['def'], help = clt_options['ip']['help'], type = str)
        parser.add_argument("port", nargs = "?", action = "store", default = clt_options['port']['def'], help = clt_options['port']['help'], type = int)
        parser.add_argument("-m", "--mode", dest = clt_options['mode']['des'], default = clt_options['mode']['def'], choices = clt_options['mode']['choi'],
                            help = clt_options['mode']['help'], type = str)
        parser.add_argument("-c", "--cmid", dest = clt_options['cmid']['des'], default = clt_options['cmid']['def'], help = clt_options['cmid']['help'], type = str)
        parser.add_argument("-n", "--name", dest = clt_options['name']['des'] , default = clt_options['name']['def'], help = clt_options['name']['help'], type = str)
        parser.add_argument("-V", "--loglevel", dest = clt_options['llevel']['des'], action = "store", choices = clt_options['llevel']['choi'],
                            default = clt_options['llevel']['def'], help = clt_options['llevel']['help'], type = str)
        parser.add_argument("-F", "--logfile", nargs = "+", dest = clt_options['lfile']['des'], default = clt_options['lfile']['def'],
                            help = clt_options['lfile']['help'], type = str)
        parser.add_argument("-S", "--logsize", dest = clt_options['lsize']['des'], action = "store", default = clt_options['lsize']['def'],
                            help = clt_options['lsize']['help'], type = float)
        
        clt_config.update(vars(parser.parse_args()))
        # Check logfile.
        clt_config['logfile'] = check_logfile(clt_config['logfile'], clt_options['lfile']['def'], loggerclt)
        

def client_check():
        # Setup hidden or not messages.
        ShellMessage.view = ( False if any(i in ['STDOUT', 'FILESTDOUT'] for i in clt_config['logfile']) else True )
        # Create log.
        logger_create(loggerclt, clt_config, mode = 'a')

        # Check cmid.
        if clt_config['cmid'] is not None:
                try:
                        uuid.UUID(clt_config['cmid'])
                except ValueError:
                        loggerclt.error("Bad CMID. Exiting...")
                        sys.exit()
                        
        # Check machineName.
        if clt_config['machineName'] is not None:
                if len(clt_config['machineName']) < 2 or len(clt_config['machineName']) > 63:
                        loggerclt.error("machineName must be between 2 and 63 characters in length.")
                        sys.exit()
                        
        clt_config['call_id'] = 1

             
def client_update():
        kmsdb = kmsDB2Dict()

        appitems = kmsdb[2]
        for appitem in appitems:
                kmsitems = appitem['KmsItems']
                for kmsitem in kmsitems:                                
                        name = re.sub('\(.*\)', '', kmsitem['DisplayName']).replace('2015', '').replace(' ', '')
                        if name == clt_config['mode']:
                                skuitems = kmsitem['SkuItems']
                                # Select 'Enterprise' for Windows or 'Professional Plus' for Office.
                                for skuitem in skuitems:
                                        if skuitem['DisplayName'].replace(' ','') == name + 'Enterprise' or \
                                           skuitem['DisplayName'].replace(' ','') == name[:6] + 'ProfessionalPlus' + name[6:]:

                                                clt_config['KMSClientSkuID'] = skuitem['Id']
                                                clt_config['RequiredClientCount'] = int(kmsitem['NCountPolicy'])
                                                clt_config['KMSProtocolMajorVersion'] = int(float(kmsitem['DefaultKmsProtocol']))
                                                clt_config['KMSProtocolMinorVersion'] = 0
                                                clt_config['KMSClientLicenseStatus'] = 2
                                                clt_config['KMSClientAppID'] = appitem['Id']
                                                clt_config['KMSClientKMSCountedID'] = kmsitem['Id']
                                                break
        
def client_create():
        loggerclt.info("Connecting to %s on port %d..." % (clt_config['ip'], clt_config['port']))
        s = socket.create_connection((clt_config['ip'], clt_config['port']))
        loggerclt.info("Connection successful !")
        binder = pykms_RpcBind.handler(None, clt_config)
        RPC_Bind = enco(str(binder.generateRequest()), 'latin-1')
        loggerclt.info("Sending RPC bind request...")
        ShellMessage.Process([-1, 1]).run()
        s.send(RPC_Bind)
        try:
                ShellMessage.Process([-4, 7]).run()
                bindResponse = s.recv(1024)
        except socket.error as e:
                if e.errno == errno.ECONNRESET:
                        loggerclt.error("Connection reset by peer. Exiting...")
                        sys.exit()
                else:
                        raise
        if bindResponse == '' or not bindResponse:
                loggerclt.error("No data received ! Exiting...")
                sys.exit()
        packetType = MSRPCHeader(bindResponse)['type']
        if packetType == rpcBase.packetType['bindAck']:
                loggerclt.info("RPC bind acknowledged.")
                ShellMessage.Process(8).run()
                kmsRequest = createKmsRequest()
                requester = pykms_RpcRequest.handler(kmsRequest, clt_config)
                s.send(enco(str(requester.generateRequest()), 'latin-1'))
                ShellMessage.Process([-1, 12]).run()
                response = s.recv(1024)
                loggerclt.debug("Response: \n%s\n" % justify(deco(binascii.b2a_hex(response), 'latin-1')))
                ShellMessage.Process([-4, 20]).run() 
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
                
                if clt_config['loglevel'] == 'MINI':
                        loggerclt.mini("", extra = {'host': socket.gethostname() + " [" + clt_config["ip"] + "]",
                                                    'status' : "Activated",
                                                    'product' : clt_config["mode"]})
                
                ShellMessage.Process(21).run()
                
        elif packetType == rpcBase.packetType['bindNak']:
                loggerclt.info(justify(MSRPCBindNak(bindResponse).dump(print_to_stdout = False)))
                sys.exit()
        else:
                loggerclt.critical("Something went wrong.")
                sys.exit()


def clt_main(with_gui = False):
        if not with_gui:
                # Parse options.
                client_options()
                
        # Check options.
        client_check()
        # Update Config.
        client_update()
        # Create and run client.
        client_create()
    
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
        requestDict['machineName'] = (clt_config['machineName'] if (clt_config['machineName'] is not None) else
                                      ''.join(random.choice(string.ascii_letters + string.digits) for i in range(random.randint(2,63)))).encode('utf-16le')
        requestDict['mnPad'] = '\0'.encode('utf-16le') * (63 - len(requestDict['machineName'].decode('utf-16le')))
        
        # Debug Stuff
        ShellMessage.Process(9).run()
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
