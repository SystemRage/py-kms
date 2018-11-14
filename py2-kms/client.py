#!/usr/bin/env python

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

import filetimes, rpcBind, rpcRequest
from dcerpc import MSRPCHeader, MSRPCBindNak, MSRPCRequestHeader, MSRPCRespHeader
from kmsBase import kmsBase, UUID
from kmsRequestV4 import kmsRequestV4
from kmsRequestV5 import kmsRequestV5
from kmsRequestV6 import kmsRequestV6
from rpcBase import rpcBase
from kmsDB2Dict import kmsDB2Dict
from formatText import shell_message, justify

config = {}

def main():
        parser = argparse.ArgumentParser()
        parser.add_argument("ip", action="store", help='The IP address or hostname of the KMS server.', type=str)
        parser.add_argument("port", nargs="?", action="store", default=1688,
                            help='The port the KMS service is listening on. The default is \"1688\".', type=int)
        parser.add_argument("-m", "--mode", dest="mode",
                            choices=["WindowsVista","Windows7","Windows8","Windows8.1","Windows10",
                                     "Office2010","Office2013","Office2016","Office2019"], default="Windows8.1",
                            help='Use this flag to manually specify a Microsoft product for testing the server. The default is \"Windows81\".', type=str)
        parser.add_argument("-c", "--cmid", dest="cmid", default=None,
                            help='Use this flag to manually specify a CMID to use. If no CMID is specified, a random CMID will be generated.', type=str)
        parser.add_argument("-n", "--name", dest="machineName", default=None,
                            help='Use this flag to manually specify an ASCII machineName to use. If no machineName is specified,\
a random machineName will be generated.', type=str)
        parser.add_argument("-v", "--loglevel", dest="loglevel", action="store", default="ERROR", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
                            help='Use this flag to set a Loglevel. The default is \"ERROR\".', type=str)
        parser.add_argument("-f", "--logfile", dest="logfile", action="store", default=os.path.dirname(os.path.abspath( __file__ )) + "/py2kms_client.log",
                            help='Use this flag to set an output Logfile. The default is \"pykms_client.log\".', type=str)
        
        config.update(vars(parser.parse_args()))

        logging.basicConfig(level=config['loglevel'], format='%(asctime)s %(levelname)-8s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S', filename=config['logfile'], filemode='w')

        checkConfig()
        config['call_id'] = 1
        updateConfig()
        s = socket.socket()
        logging.info("Connecting to %s on port %d..." % (config['ip'], config['port']))
        s.connect((config['ip'], config['port']))
        logging.info("Connection successful !")
        binder = rpcBind.handler(None, config)
        RPC_Bind = str(binder.generateRequest())
        logging.info("Sending RPC bind request...")
        shell_message(nshell = [-1, 1])
        s.send(RPC_Bind)
        try:
                shell_message(nshell = [-4, 7])
                bindResponse = s.recv(1024)
        except socket.error, e:
                if e.errno == errno.ECONNRESET:
                        logging.error("Connection reset by peer. Exiting...")
                        sys.exit()
                else:
                        raise
        if bindResponse == '' or not bindResponse:
                logging.error("No data received ! Exiting...")
                sys.exit()
        packetType = MSRPCHeader(bindResponse)['type']
        if packetType == rpcBase.packetType['bindAck']:
                logging.info("RPC bind acknowledged.")
                shell_message(nshell = 8)
                kmsRequest = createKmsRequest()
                requester = rpcRequest.handler(kmsRequest, config)
                s.send(str(requester.generateRequest()))
                shell_message(nshell = [-1, 12]) 
                response = s.recv(1024)
                logging.debug("Response: \n%s\n" % justify(binascii.b2a_hex(response)))
                shell_message(nshell = [-4, 20]) 
                parsed = MSRPCRespHeader(response)
                kmsData = readKmsResponse(parsed['pduData'], kmsRequest, config)
                kmsResp = kmsData['response']
                               
                try:
                        hwid = kmsData['hwid']
                        logging.info("KMS Host HWID: %s" % binascii.b2a_hex(hwid).upper())
                except KeyError:
                        pass
                logging.info("KMS Host ePID: %s" % kmsResp['kmsEpid'].decode('utf-16le').encode('utf-8'))                       
                logging.info("KMS Host Current Client Count: %s" % kmsResp['currentClientCount'])
                logging.info("KMS VL Activation Interval: %s" % kmsResp['vLActivationInterval'])
                logging.info("KMS VL Renewal Interval: %s" % kmsResp['vLRenewalInterval'])
                shell_message(nshell = 21) 
                
        elif packetType == rpcBase.packetType['bindNak']:
                logging.info(justify(MSRPCBindNak(bindResponse).dump(print_to_stdout = False)))
                sys.exit()
        else:
                logging.critical("Something went wrong.")
                sys.exit()
                

def checkConfig():
        if config['cmid'] is not None:
                try:
                        uuid.UUID(config['cmid'])
                except ValueError:
                        logging.error("Bad CMID. Exiting...")
                        sys.exit()
        if config['machineName'] is not None:
                if len(config['machineName']) < 2 or len(config['machineName']) > 63:
                        logging.error("Error: machineName must be between 2 and 63 characters in length.")
                        sys.exit()

def updateConfig():
        kmsdb = kmsDB2Dict()

        appitems = kmsdb[2]
        for appitem in appitems:
                kmsitems = appitem['KmsItems']
                for kmsitem in kmsitems:
                        # Threshold.
                        try:
                                count = int(kmsitem['NCountPolicy'])
                        except KeyError:
                                count = 25
                                
                        name = re.sub('\(.*\)', '', kmsitem['DisplayName']).replace('2015', '').replace(' ', '')
                        if name == config['mode']:
                                skuitems = kmsitem['SkuItems']
                                # Select 'Enterprise' for Windows or 'Professional Plus' for Office.
                                # (improvement: choice could be also random: skuitem = random.choice(skuitems))
                                for skuitem in skuitems:
                                        if skuitem['DisplayName'].replace(' ','') == name + 'Enterprise' or \
                                           skuitem['DisplayName'].replace(' ','') == name[:6] + 'ProfessionalPlus' + name[6:]:

                                                config['KMSClientSkuID'] = skuitem['Id']
                                                config['RequiredClientCount'] = count
                                                config['KMSProtocolMajorVersion'] = int(float(kmsitem['DefaultKmsProtocol']))
                                                config['KMSProtocolMinorVersion'] = 0
                                                config['KMSClientLicenseStatus'] = 2
                                                config['KMSClientAppID'] = appitem['Id']
                                                config['KMSClientKMSCountedID'] = kmsitem['Id']
                                                break


def createKmsRequestBase():
        requestDict = kmsBase.kmsRequestStruct()
        requestDict['versionMinor'] = config['KMSProtocolMinorVersion']
        requestDict['versionMajor'] = config['KMSProtocolMajorVersion']
        requestDict['isClientVm'] = 0
        requestDict['licenseStatus'] = config['KMSClientLicenseStatus']
        requestDict['graceTime'] = 43200
        requestDict['applicationId'] = UUID(uuid.UUID(config['KMSClientAppID']).bytes_le)
        requestDict['skuId'] = UUID(uuid.UUID(config['KMSClientSkuID']).bytes_le)
        requestDict['kmsCountedId'] = UUID(uuid.UUID(config['KMSClientKMSCountedID']).bytes_le)
        requestDict['clientMachineId'] = UUID(uuid.UUID(config['cmid']).bytes_le if (config['cmid'] is not None) else uuid.uuid4().bytes_le)
        requestDict['previousClientMachineId'] = '\0' * 16 #requestDict['clientMachineId'] # I'm pretty sure this is supposed to be a null UUID.
        requestDict['requiredClientCount'] = config['RequiredClientCount']
        requestDict['requestTime'] = filetimes.dt_to_filetime(datetime.datetime.utcnow())
        requestDict['machineName'] = (config['machineName'] if (config['machineName'] is not None) else
                                      ''.join(random.choice(string.letters + string.digits) for i in range(random.randint(2,63)))).encode('utf-16le')
        requestDict['mnPad'] = '\0'.encode('utf-16le') * (63 - len(requestDict['machineName'].decode('utf-16le')))

        # Debug Stuff
        shell_message(nshell = 9)
        logging.debug("Request Base Dictionary: \n%s\n" % justify(requestDict.dump(print_to_stdout = False)))

        return requestDict

def createKmsRequest():
        # Update the call ID
        config['call_id'] += 1

        # KMS Protocol Major Version
        if config['KMSProtocolMajorVersion'] == 4:
                handler = kmsRequestV4(None, config)
        elif config['KMSProtocolMajorVersion'] == 5:
                handler = kmsRequestV5(None, config)
        elif config['KMSProtocolMajorVersion'] == 6:
                handler = kmsRequestV6(None, config)
        else:
                return None

        requestBase = createKmsRequestBase()
        return handler.generateRequest(requestBase)

def readKmsResponse(data, request, config):
        if config['KMSProtocolMajorVersion'] == 4:
                logging.info("Received V4 response")
                response = readKmsResponseV4(data, request)
        elif config['KMSProtocolMajorVersion'] == 5:
                logging.info("Received V5 response")
                response = readKmsResponseV5(data)
        elif config['KMSProtocolMajorVersion'] == 6:
                logging.info("Received V6 response")
                response = readKmsResponseV6(data)
        else:
                logging.info("Unhandled response version: %d.%d" % (config['KMSProtocolMajorVersion'], config['KMSProtocolMinorVersion']))
                logging.info("I'm not even sure how this happened...")
        return response

def readKmsResponseV4(data, request):
        response = kmsRequestV4.ResponseV4(data)
        hashed = kmsRequestV4(data, config).generateHash(bytearray(str(response['response'])))
        if hashed == response['hash']:
                logging.info("Response Hash has expected value !")
        return response

def readKmsResponseV5(data):
        response = kmsRequestV5.ResponseV5(data)
        decrypted = kmsRequestV5(data, config).decryptResponse(response)
        return decrypted

def readKmsResponseV6(data):
        response = kmsRequestV6.ResponseV5(data)
        decrypted = kmsRequestV6(data, config).decryptResponse(response)
        message = decrypted['message']
        return message

if __name__ == "__main__":
        main()
