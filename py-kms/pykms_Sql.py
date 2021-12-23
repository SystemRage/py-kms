#!/usr/bin/env python3

import os
import logging

# sqlite3 is optional.
try:
        import sqlite3
except ImportError:
        pass

from pykms_Format import pretty_printer

#--------------------------------------------------------------------------------------------------------------------------------------------------------

loggersrv = logging.getLogger('logsrv')

def sql_initialize(dbName):
        if not os.path.isfile(dbName):
                # Initialize the database.
                loggersrv.debug(f'Initializing database file "{dbName}"...')
                con = None
                try:
                        con = sqlite3.connect(dbName)
                        cur = con.cursor()
                        cur.execute("CREATE TABLE clients(clientMachineId TEXT, machineName TEXT, applicationId TEXT, skuId TEXT, \
licenseStatus TEXT, lastRequestTime INTEGER, kmsEpid TEXT, requestCount INTEGER)")

                except sqlite3.Error as e:
                        pretty_printer(log_obj = loggersrv.error, to_exit = True,
                                       put_text = "{reverse}{red}{bold}Sqlite Error: %s. Exiting...{end}" %str(e))
                finally:
                        if con:
                                con.commit()
                                con.close()

def sql_update(dbName, infoDict):
        con = None
        try:
                con = sqlite3.connect(dbName)
                cur = con.cursor()
                cur.execute("SELECT * FROM clients WHERE clientMachineId=:clientMachineId AND applicationId=:appId;", infoDict)
                try:
                        data = cur.fetchone()
                        if not data:
                                # Insert row.
                                cur.execute("INSERT INTO clients (clientMachineId, machineName, applicationId, \
skuId, licenseStatus, lastRequestTime, requestCount) VALUES (:clientMachineId, :machineName, :appId, :skuId, :licenseStatus, :requestTime, 1);", infoDict)
                        else:
                                # Update data.
                                if data[1] != infoDict["machineName"]:
                                        cur.execute("UPDATE clients SET machineName=:machineName WHERE \
clientMachineId=:clientMachineId AND applicationId=:appId;", infoDict)
                                if data[2] != infoDict["appId"]:
                                        cur.execute("UPDATE clients SET applicationId=:appId WHERE \
clientMachineId=:clientMachineId AND applicationId=:appId;", infoDict)
                                if data[3] != infoDict["skuId"]:
                                        cur.execute("UPDATE clients SET skuId=:skuId WHERE \
clientMachineId=:clientMachineId AND applicationId=:appId;", infoDict)
                                if data[4] != infoDict["licenseStatus"]:
                                        cur.execute("UPDATE clients SET licenseStatus=:licenseStatus WHERE \
clientMachineId=:clientMachineId AND applicationId=:appId;", infoDict)
                                if data[5] != infoDict["requestTime"]:
                                        cur.execute("UPDATE clients SET lastRequestTime=:requestTime WHERE \
clientMachineId=:clientMachineId AND applicationId=:appId;", infoDict)
                                # Increment requestCount
                                cur.execute("UPDATE clients SET requestCount=requestCount+1 WHERE \
clientMachineId=:clientMachineId AND applicationId=:appId;", infoDict)

                except sqlite3.Error as e:
                        pretty_printer(log_obj = loggersrv.error, to_exit = True,
                                       put_text = "{reverse}{red}{bold}Sqlite Error: %s. Exiting...{end}" %str(e))
        except sqlite3.Error as e:
                pretty_printer(log_obj = loggersrv.error, to_exit = True,
                               put_text = "{reverse}{red}{bold}Sqlite Error: %s. Exiting...{end}" %str(e))
        finally:
                if con:
                    con.commit()
                    con.close()

def sql_update_epid(dbName, kmsRequest, response, appName):
        cmid = str(kmsRequest['clientMachineId'].get())
        con = None
        try:
                con = sqlite3.connect(dbName)
                cur = con.cursor()
                cur.execute("SELECT * FROM clients WHERE clientMachineId=? AND applicationId=?;", (cmid, appName))
                try:
                        data = cur.fetchone()
                        cur.execute("UPDATE clients SET kmsEpid=? WHERE \
clientMachineId=? AND applicationId=?;", (str(response["kmsEpid"].decode('utf-16le')), cmid, appName))

                except sqlite3.Error as e:
                        pretty_printer(log_obj = loggersrv.error, to_exit = True,
                                       put_text = "{reverse}{red}{bold}Sqlite Error: %s. Exiting...{end}" %str(e))
        except sqlite3.Error as e:
                pretty_printer(log_obj = loggersrv.error, to_exit = True,
                               put_text = "{reverse}{red}{bold}Sqlite Error: %s. Exiting...{end}" %str(e))
        finally:
                if con:
                        con.commit()
                        con.close()
