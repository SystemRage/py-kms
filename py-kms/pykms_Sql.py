#!/usr/bin/env python3

import os
import logging
import sys

# sqlite3 is optional.
try:
	import sqlite3
except ImportError:
	pass

#--------------------------------------------------------------------------------------------------------------------------------------------------------

loggersrv = logging.getLogger('logsrv')

def sql_initialize():
	dbName = 'clients.db'
	if not os.path.isfile(dbName):
		# Initialize the database.
		con = None
		try:
			con = sqlite3.connect(dbName)
			cur = con.cursor()
			cur.execute("CREATE TABLE clients(clientMachineId TEXT, machineName TEXT, applicationId TEXT, skuId TEXT, \
licenseStatus TEXT, lastRequestTime INTEGER, kmsEpid TEXT, requestCount INTEGER)")

		except sqlite3.Error as e:
			loggersrv.error("Error %s:" % e.args[0])
			sys.exit(1)
		finally:
			if con:
				con.commit()
				con.close()
	return dbName


def sql_update(dbName, infoDict):
	con = None
	try:
		con = sqlite3.connect(dbName)
		cur = con.cursor()
		cur.execute("SELECT * FROM clients WHERE clientMachineId=:clientMachineId;", infoDict)
		try:
			data = cur.fetchone()
			if not data:
				# Insert row.
				cur.execute("INSERT INTO clients (clientMachineId, machineName, applicationId, \
skuId, licenseStatus, lastRequestTime, requestCount) VALUES (:clientMachineId, :machineName, :appId, :skuId, :licenseStatus, :requestTime, 1);", infoDict)
			else:
				# Update data.
				if data[1] != infoDict["machineName"]:
					cur.execute("UPDATE clients SET machineName=:machineName WHERE clientMachineId=:clientMachineId;", infoDict)
				if data[2] != infoDict["appId"]:
					cur.execute("UPDATE clients SET applicationId=:appId WHERE clientMachineId=:clientMachineId;", infoDict)
				if data[3] != infoDict["skuId"]:
					cur.execute("UPDATE clients SET skuId=:skuId WHERE clientMachineId=:clientMachineId;", infoDict)
				if data[4] != infoDict["licenseStatus"]:
					cur.execute("UPDATE clients SET licenseStatus=:licenseStatus WHERE clientMachineId=:clientMachineId;", infoDict)
				if data[5] != infoDict["requestTime"]:
					cur.execute("UPDATE clients SET lastRequestTime=:requestTime WHERE clientMachineId=:clientMachineId;", infoDict)
				# Increment requestCount
				cur.execute("UPDATE clients SET requestCount=requestCount+1 WHERE clientMachineId=:clientMachineId;", infoDict)

		except sqlite3.Error as e:
			loggersrv.error("Error %s:" % e.args[0])
			sys.exit(1)
	except sqlite3.Error as e:
		loggersrv.error("Error %s:" % e.args[0])
		sys.exit(1)
	finally:
		if con:
		    con.commit()
		    con.close()

def sql_update_epid(dbName, kmsRequest, response):
	cmid = str(kmsRequest['clientMachineId'].get())
	con = None
	try:
		con = sqlite3.connect(dbName)
		cur = con.cursor()
		cur.execute("SELECT * FROM clients WHERE clientMachineId=?;", [cmid])
		try:
			data = cur.fetchone()
			if data[6]:
				response["kmsEpid"] = data[6].encode('utf-16le')
			else:
				cur.execute("UPDATE clients SET kmsEpid=? WHERE clientMachineId=?;", (str(response["kmsEpid"].decode('utf-16le')),
												      cmid))
		except sqlite3.Error as e:
			loggersrv.error("Error %s:" % e.args[0])
			sys.exit(1)
	except sqlite3.Error as e:
		loggersrv.error("Error %s:" % e.args[0])
		sys.exit(1)
	finally:
		if con:
			con.commit()
			con.close()
	return response
