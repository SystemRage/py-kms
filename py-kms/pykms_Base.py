#!/usr/bin/env python3

import binascii
import logging
import os
import sys
import time
import uuid
import socket

from pykms_Structure import Structure
from pykms_DB2Dict import kmsDB2Dict
from pykms_PidGenerator import epidGenerator
from pykms_Filetimes import filetime_to_dt
from pykms_Sql import sql_initialize, sql_update, sql_update_epid
from pykms_Format import justify, byterize, enco, deco, ShellMessage

#--------------------------------------------------------------------------------------------------------------------------------------------------------

loggersrv = logging.getLogger('logsrv')

class UUID(Structure):
        commonHdr = ()
        structure = (
                ('raw', '16s'),
        )

        def get(self):
                return uuid.UUID(bytes_le = enco(str(self), 'latin-1'))

class kmsBase:
        def __init__(self, data, srv_config):
                self.data = data
                self.srv_config = srv_config
                
        class kmsRequestStruct(Structure):
                commonHdr = ()
                structure = (
                        ('versionMinor',            '<H'),
                        ('versionMajor',            '<H'),
                        ('isClientVm',              '<I'),
                        ('licenseStatus',           '<I'),
                        ('graceTime',               '<I'),
                        ('applicationId',           ':', UUID),
                        ('skuId',                   ':', UUID),
                        ('kmsCountedId' ,           ':', UUID),
                        ('clientMachineId',         ':', UUID),
                        ('requiredClientCount',     '<I'),
                        ('requestTime',             '<Q'),
                        ('previousClientMachineId', ':', UUID),
                        ('machineName',             'u'),
                        ('_mnPad',                  '_-mnPad', '126-len(machineName)'),
                        ('mnPad',                   ':'),
                )

                def getMachineName(self):
                        return self['machineName'].decode('utf-16le')
                
                def getLicenseStatus(self):
                        return kmsBase.licenseStates[self['licenseStatus']] or "Unknown"

        class kmsResponseStruct(Structure):
                commonHdr = ()
                structure = (
                        ('versionMinor',         '<H'),
                        ('versionMajor',         '<H'),
                        ('epidLen',              '<I=len(kmsEpid)+2'),
                        ('kmsEpid',              'u'),
                        ('clientMachineId',      ':', UUID),
                        ('responseTime',         '<Q'),
                        ('currentClientCount',   '<I'),
                        ('vLActivationInterval', '<I'),
                        ('vLRenewalInterval',    '<I'),
                )

        class GenericRequestHeader(Structure):
                commonHdr = ()
                structure = (
                        ('bodyLength1',  '<I'),
                        ('bodyLength2',  '<I'),
                        ('versionMinor', '<H'),
                        ('versionMajor', '<H'),
                        ('remainder',    '_'),
                )

        licenseStates = {
                0 : "Unlicensed",
                1 : "Activated",
                2 : "Grace Period",
                3 : "Out-of-Tolerance Grace Period",
                4 : "Non-Genuine Grace Period",
                5 : "Notifications Mode",
                6 : "Extended Grace Period",
        }

        licenseStatesEnum = {
                'unlicensed' : 0,
                'licensed' : 1,
                'oobGrace' : 2,
                'ootGrace' : 3,
                'nonGenuineGrace' : 4,
                'notification' : 5,
                'extendedGrace' : 6
        }

        
        def getPadding(self, bodyLength):
                ## https://forums.mydigitallife.info/threads/71213-Source-C-KMS-Server-from-Microsoft-Toolkit?p=1277542&viewfull=1#post1277542
                return 4 + (((~bodyLength & 3) + 1) & 3)

        def serverLogic(self, kmsRequest):
                if self.srv_config['sqlite'] and self.srv_config['dbSupport']:
                        self.dbName = sql_initialize()
                                                                        
                ShellMessage.Process(15).run()
                kmsRequest = byterize(kmsRequest)
                loggersrv.debug("KMS Request Bytes: \n%s\n" % justify(deco(binascii.b2a_hex(enco(str(kmsRequest), 'latin-1')), 'latin-1')))                         
                loggersrv.debug("KMS Request: \n%s\n" % justify(kmsRequest.dump(print_to_stdout = False)))
                                        
                clientMachineId = kmsRequest['clientMachineId'].get()
                applicationId = kmsRequest['applicationId'].get()
                skuId = kmsRequest['skuId'].get()
                requestDatetime = filetime_to_dt(kmsRequest['requestTime'])
                                
                # Localize the request time, if module "tzlocal" is available.
                try:
                        from tzlocal import get_localzone
                        from pytz.exceptions import UnknownTimeZoneError
                        try:
                                tz = get_localzone()
                                local_dt = tz.localize(requestDatetime)
                        except UnknownTimeZoneError:
                                loggersrv.warning('Unknown time zone ! Request time not localized.')
                                local_dt = requestDatetime
                except ImportError:
                        loggersrv.warning('Module "tzlocal" not available ! Request time not localized.')
                        local_dt = requestDatetime

                # Activation threshold.
                # https://docs.microsoft.com/en-us/windows/deployment/volume-activation/activate-windows-10-clients-vamt                
                MinClients = kmsRequest['requiredClientCount'] 
                RequiredClients = MinClients * 2
                if self.srv_config["CurrentClientCount"] != None:
                        if 0 < self.srv_config["CurrentClientCount"] < MinClients:
                                # fixed to 6 (product server) or 26 (product desktop)
                                currentClientCount = MinClients + 1
                                loggersrv.warning("Not enough clients ! Fixed with %s, but activated client could be detected as not genuine !" %currentClientCount)
                        elif MinClients <= self.srv_config["CurrentClientCount"] < RequiredClients:
                                currentClientCount = self.srv_config["CurrentClientCount"]
                                loggersrv.warning("With count = %s, activated client could be detected as not genuine !" %currentClientCount)
                        elif self.srv_config["CurrentClientCount"] >= RequiredClients:
                                # fixed to 10 (product server) or 50 (product desktop)
                                currentClientCount = RequiredClients
                                if self.srv_config["CurrentClientCount"] > RequiredClients:
                                        loggersrv.warning("Too many clients ! Fixed with %s" %currentClientCount)
                else:
                        # fixed to 10 (product server) or 50 (product desktop)
                        currentClientCount = RequiredClients     

                        
                # Get a name for SkuId, AppId.        
                kmsdb = kmsDB2Dict()
 
                appitems = kmsdb[2]
                for appitem in appitems:
                        kmsitems = appitem['KmsItems']
                        for kmsitem in kmsitems:                                       
                                skuitems = kmsitem['SkuItems']
                                for skuitem in skuitems:
                                        try:
                                                if uuid.UUID(skuitem['Id']) == skuId:
                                                        skuName = skuitem['DisplayName']
                                                        break
                                        except:
                                                skuName = skuId
                                                loggersrv.warning("Can't find a name for this product !!")
                                    
                        try:
                                if uuid.UUID(appitem['Id']) == applicationId:
                                        appName = appitem['DisplayName']
                        except:
                                appName = applicationId
                                loggersrv.warning("Can't find a name for this application group !!")

                infoDict = {
                        "machineName" : kmsRequest.getMachineName(),
                        "clientMachineId" : str(clientMachineId),
                        "appId" : appName,
                        "skuId" : skuName,
                        "licenseStatus" : kmsRequest.getLicenseStatus(),
                        "requestTime" : int(time.time()),
                        "kmsEpid" : None
                }

                loggersrv.info("Machine Name: %s" % infoDict["machineName"])
                loggersrv.info("Client Machine ID: %s" % infoDict["clientMachineId"])
                loggersrv.info("Application ID: %s" % infoDict["appId"])
                loggersrv.info("SKU ID: %s" % infoDict["skuId"])
                loggersrv.info("License Status: %s" % infoDict["licenseStatus"])
                loggersrv.info("Request Time: %s" % local_dt.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)'))
                
                if self.srv_config['loglevel'] == 'MINI':
                        loggersrv.mini("", extra = {'host': socket.gethostname() + " [" + self.srv_config["ip"] + "]",
                                                    'status' : infoDict["licenseStatus"],
                                                    'product' : infoDict["skuId"]})

                if self.srv_config['sqlite'] and self.srv_config['dbSupport']:
                        sql_update(self.dbName, infoDict)

                return self.createKmsResponse(kmsRequest, currentClientCount)

        def createKmsResponse(self, kmsRequest, currentClientCount):
                response = self.kmsResponseStruct()
                response['versionMinor'] = kmsRequest['versionMinor']
                response['versionMajor'] = kmsRequest['versionMajor']
                
                if not self.srv_config["epid"]:
                        response["kmsEpid"] = epidGenerator(kmsRequest['kmsCountedId'].get(), kmsRequest['versionMajor'],
                                                            self.srv_config["lcid"]).encode('utf-16le')
                else:
                        response["kmsEpid"] = self.srv_config["epid"].encode('utf-16le')
                        
                response['clientMachineId'] = kmsRequest['clientMachineId']
                # rule: timeserver - 4h <= timeclient <= timeserver + 4h, check if is satisfied.
                response['responseTime'] = kmsRequest['requestTime'] 
                response['currentClientCount'] = currentClientCount
                response['vLActivationInterval'] = self.srv_config["VLActivationInterval"]
                response['vLRenewalInterval'] = self.srv_config["VLRenewalInterval"]

                if self.srv_config['sqlite'] and self.srv_config['dbSupport']:
                        response = sql_update_epid(self.dbName, kmsRequest, response)

                loggersrv.info("Server ePID: %s" % response["kmsEpid"].decode('utf-16le'))
                        
                return response


import pykms_RequestV4, pykms_RequestV5, pykms_RequestV6, pykms_RequestUnknown

def generateKmsResponseData(data, srv_config):
        version = kmsBase.GenericRequestHeader(data)['versionMajor']
        currentDate = time.strftime("%a %b %d %H:%M:%S %Y")

        if version == 4:
                loggersrv.info("Received V%d request on %s." % (version, currentDate))
                messagehandler = pykms_RequestV4.kmsRequestV4(data, srv_config)     
        elif version == 5:
                loggersrv.info("Received V%d request on %s." % (version, currentDate))
                messagehandler = pykms_RequestV5.kmsRequestV5(data, srv_config)
        elif version == 6:
                loggersrv.info("Received V%d request on %s." % (version, currentDate))
                messagehandler = pykms_RequestV6.kmsRequestV6(data, srv_config)
        else:
                loggersrv.info("Unhandled KMS version V%d." % version)
                messagehandler = pykms_RequestUnknown.kmsRequestUnknown(data, srv_config)
                
        return messagehandler.executeRequestLogic()
