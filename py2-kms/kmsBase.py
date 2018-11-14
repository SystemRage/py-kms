#!/usr/bin/env python

import binascii
import logging
import os
import sys
import time
import uuid

from structure import Structure
from kmsDB2Dict import kmsDB2Dict
import kmsPidGenerator
import filetimes
from formatText import justify, shell_message

# sqlite3 is optional
try:
	import sqlite3
except ImportError:
	pass

class UUID(Structure):
	commonHdr = ()
	structure = (
		('raw', '16s'),
	)

	def get(self):
		return uuid.UUID(bytes_le=str(self))

class kmsBase:
        def __init__(self, data, config):
                self.data = data
		self.config = config
		
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

	errorCodes = {
		'SL_E_VL_NOT_WINDOWS_SLP' : 0xC004F035,
		'SL_E_VL_NOT_ENOUGH_COUNT' : 0xC004F038,
		'SL_E_VL_BINDING_SERVICE_NOT_ENABLED' : 0xC004F039,
		'SL_E_VL_INFO_PRODUCT_USER_RIGHT' : 0x4004F040,
		'SL_I_VL_OOB_NO_BINDING_SERVER_REGISTRATION' : 0x4004F041,
		'SL_E_VL_KEY_MANAGEMENT_SERVICE_ID_MISMATCH' : 0xC004F042,
		'SL_E_VL_MACHINE_NOT_BOUND' : 0xC004F056
	}


	def getPadding(self, bodyLength):
                ## https://forums.mydigitallife.info/threads/71213-Source-C-KMS-Server-from-Microsoft-Toolkit?p=1277542&viewfull=1#post1277542
                return 4 + (((~bodyLength & 3) + 1) & 3)

	def serverLogic(self, kmsRequest):
		if self.config['sqlite'] and self.config['dbSupport']:
			self.dbName = 'clients.db'
			if not os.path.isfile(self.dbName):
				# Initialize the database.
				con = None
				try:
					con = sqlite3.connect(self.dbName)
					cur = con.cursor()
					cur.execute("CREATE TABLE clients(clientMachineId TEXT, machineName TEXT, applicationId TEXT, \
skuId TEXT, licenseStatus TEXT, lastRequestTime INTEGER, kmsEpid TEXT, requestCount INTEGER)")

				except sqlite3.Error, e:
                                        logging.error("Error %s:" % e.args[0])
					sys.exit(1)

				finally:
					if con:
						con.commit()
						con.close()

		shell_message(nshell = 15)
                logging.debug("KMS Request Bytes: \n%s\n" % justify(binascii.b2a_hex(str(kmsRequest))))
                logging.debug("KMS Request: \n%s\n" % justify(kmsRequest.dump(print_to_stdout = False)))
			
		clientMachineId = kmsRequest['clientMachineId'].get()
		applicationId = kmsRequest['applicationId'].get()
		skuId = kmsRequest['skuId'].get()
		requestDatetime = filetimes.filetime_to_dt(kmsRequest['requestTime'])

		# Localize the request time, if module "tzlocal" is available.
		try:
                        from tzlocal import get_localzone
                        from pytz.exceptions import UnknownTimeZoneError
                        try:
                                tz = get_localzone()
                                local_dt = tz.localize(requestDatetime)
                        except UnknownTimeZoneError:
                                logging.warning('Unknown time zone ! Request time not localized.')
                                local_dt = requestDatetime
                except ImportError:
                        logging.warning('Module "tzlocal" not available ! Request time not localized.')
                        local_dt = requestDatetime

		# Get SkuId, AppId and client threshold.
		appName, skuName = applicationId, skuId
		
		kmsdb = kmsDB2Dict()

                appitems = kmsdb[2]
                for appitem in appitems:
                        kmsitems = appitem['KmsItems']
                        for kmsitem in kmsitems:

                                # Activation threshold.
                                try:
                                        count = int(kmsitem['NCountPolicy'])
                                except KeyError:
                                        count = 25
                                
                                if self.config["CurrentClientCount"] <= count:
                                        currentClientCount = count + 1
                                else:
                                        currentClientCount = self.config["CurrentClientCount"]
                                
                                skuitems = kmsitem['SkuItems']
                                for skuitem in skuitems:
                                        try:
                                                if uuid.UUID(skuitem['Id']) == skuId:
                                                        skuName = skuitem['DisplayName']
                                                        break
                                        except IndexError:
                                                pass
                                        
                        if uuid.UUID(appitem['Id']) == applicationId:
                                appName = appitem['DisplayName']
                                

		infoDict = {
			"machineName" : kmsRequest.getMachineName(),
			"clientMachineId" : str(clientMachineId),
			"appId" : appName,
			"skuId" : skuName,
			"licenseStatus" : kmsRequest.getLicenseStatus(),
			"requestTime" : int(time.time()),
			"kmsEpid" : None
		}

                logging.info("Machine Name: %s" % infoDict["machineName"])
                logging.info("Client Machine ID: %s" % infoDict["clientMachineId"])
                logging.info("Application ID: %s" % infoDict["appId"])
                logging.info("SKU ID: %s" % infoDict["skuId"])
                logging.info("License Status: %s" % infoDict["licenseStatus"])
                logging.info("Request Time: %s" % local_dt.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)'))

		if self.config['sqlite'] and self.config['dbSupport']:
			con = None
			try:
				con = sqlite3.connect(self.dbName)
				cur = con.cursor()
				cur.execute("SELECT * FROM clients WHERE clientMachineId=:clientMachineId;", infoDict)
				try:
					data = cur.fetchone()
					if not data:
						#print "Inserting row..."
						cur.execute("INSERT INTO clients (clientMachineId, machineName, applicationId, \
skuId, licenseStatus, lastRequestTime, requestCount) VALUES (:clientMachineId, :machineName, :appId, :skuId, :licenseStatus, :requestTime, 1);", infoDict)
					else:
						#print "Data:", data
						if data[1] != infoDict["machineName"]:
							cur.execute("UPDATE clients SET machineName=:machineName WHERE \
clientMachineId=:clientMachineId;", infoDict)
						if data[2] != infoDict["appId"]:
							cur.execute("UPDATE clients SET applicationId=:appId WHERE \
clientMachineId=:clientMachineId;", infoDict)
						if data[3] != infoDict["skuId"]:
							cur.execute("UPDATE clients SET skuId=:skuId WHERE \
clientMachineId=:clientMachineId;", infoDict)
						if data[4] != infoDict["licenseStatus"]:
							cur.execute("UPDATE clients SET licenseStatus=:licenseStatus WHERE \
clientMachineId=:clientMachineId;", infoDict)
						if data[5] != infoDict["requestTime"]:
							cur.execute("UPDATE clients SET lastRequestTime=:requestTime WHERE \
clientMachineId=:clientMachineId;", infoDict)
						# Increment requestCount
						cur.execute("UPDATE clients SET requestCount=requestCount+1 WHERE \
clientMachineId=:clientMachineId;", infoDict)

				except sqlite3.Error, e:
                                        logging.error("Error %s:" % e.args[0])
					
			except sqlite3.Error, e:
                                logging.error("Error %s:" % e.args[0])
				sys.exit(1)
			finally:
				if con:
					con.commit()
					con.close()

		return self.createKmsResponse(kmsRequest, currentClientCount)
	

	def createKmsResponse(self, kmsRequest, currentClientCount):
		response = self.kmsResponseStruct()
		response['versionMinor'] = kmsRequest['versionMinor']
		response['versionMajor'] = kmsRequest['versionMajor']
		
		if not self.config["epid"]:
			response["kmsEpid"] = kmsPidGenerator.epidGenerator(kmsRequest['kmsCountedId'].get(), kmsRequest['versionMajor'],
                                                                            self.config["lcid"]).encode('utf-16le')
		else:
			response["kmsEpid"] = self.config["epid"].encode('utf-16le')
			
		response['clientMachineId'] = kmsRequest['clientMachineId']
		response['responseTime'] = kmsRequest['requestTime']
		response['currentClientCount'] = currentClientCount		
		response['vLActivationInterval'] = self.config["VLActivationInterval"]
		response['vLRenewalInterval'] = self.config["VLRenewalInterval"]

		if self.config['sqlite'] and self.config['dbSupport']:
			con = None
			try:
				con = sqlite3.connect(self.dbName)
				cur = con.cursor()
				cur.execute("SELECT * FROM clients WHERE clientMachineId=?;", [str(kmsRequest['clientMachineId'].get())])
				try:
					data = cur.fetchone()
					if data[6]:
						response["kmsEpid"] = data[6].encode('utf-16le')
					else:
						cur.execute("UPDATE clients SET kmsEpid=? WHERE clientMachineId=?;",
                                                            (str(response["kmsEpid"].decode('utf-16le')), str(kmsRequest['clientMachineId'].get())))

				except sqlite3.Error, e:
                                        logging.error("Error %s:" % e.args[0])
					
			except sqlite3.Error, e:
                                logging.error("Error %s:" % e.args[0])
                                sys.exit(1)
			finally:
				if con:
					con.commit()
					con.close()

                logging.info("Server ePID: %s" % response["kmsEpid"].decode('utf-16le').encode('utf-8'))
                        
		return response


import kmsRequestV4, kmsRequestV5, kmsRequestV6, kmsRequestUnknown

def generateKmsResponseData(data, config):
	version = kmsBase.GenericRequestHeader(data)['versionMajor']
	currentDate = time.strftime("%a %b %d %H:%M:%S %Y")

	if version == 4:
		logging.info("Received V%d request on %s." % (version, currentDate))
		messagehandler = kmsRequestV4.kmsRequestV4(data, config)	
	elif version == 5:
		logging.info("Received V%d request on %s." % (version, currentDate))
		messagehandler = kmsRequestV5.kmsRequestV5(data, config)
	elif version == 6:
		logging.info("Received V%d request on %s." % (version, currentDate))
		messagehandler = kmsRequestV6.kmsRequestV6(data, config)
	else:
		logging.info("Unhandled KMS version V%d." % version)
		messagehandler = kmsRequestUnknown.kmsRequestUnknown(data, config)
		
	return messagehandler.executeRequestLogic()
