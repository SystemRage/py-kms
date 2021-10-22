#!/usr/bin/python3

# This replaces the old start.sh and ensures all arguments are bound correctly from the environment variables...

import os
import time
import subprocess

argumentVariableMapping = {
    '-l': 'LCID',
    '-c': 'CLIENT_COUNT',
    '-a': 'ACTIVATION_INTERVAL',
    '-r': 'RENEWAL_INTERVAL',
    '-w': 'HWID',
    '-V': 'LOGLEVEL',
    '-F': 'LOGFILE',
    '-S': 'LOGSIZE',
    '-e': 'EPID'
}
sqliteWebPath = '/home/sqlite_web/sqlite_web.py'

# Build the command to execute
listenIP = os.environ.get('IP', '0.0.0.0')
listenPort = os.environ.get('PORT', '1688')
command = ['/usr/bin/python3', 'pykms_Server.py', listenIP, listenPort]
for (arg, env) in argumentVariableMapping.items():
    if env in os.environ and os.environ.get(env) != '':
        command.append(arg)
        command.append(os.environ.get(env))
        
enableSQLITE = os.path.isfile(sqliteWebPath) and os.environ.get('SQLITE', 'false').lower() == 'true'
if enableSQLITE:
    dbPath = os.path.join('db', 'pykms_database.db')
    print('Storing database file to ' + dbPath)
    os.makedirs('db', exist_ok=True)
    command.append('-s')
    command.append(dbPath)

pykmsProcess = subprocess.Popen(command)

# In case SQLITE is defined: Start the web interface
if enableSQLITE:
    time.sleep(5) # The server may take a while to start
    if not os.path.isfile(dbPath):
        # Start a dummy activation to ensure the database file is created
        subprocess.run(['/usr/bin/python3', 'pykms_Client.py', listenIP, listenPort, '-m', 'Windows10', '-n', 'DummyClient', '-c', 'ae3a27d1-b73a-4734-9878-70c949815218'])
    sqliteProcess = subprocess.Popen(['/usr/bin/python3', sqliteWebPath, '-H', listenIP, '--read-only', '-x', dbPath, '-p', os.environ.get('SQLITE_PORT', 8080)])

try:
    pykmsProcess.wait()
except:
    # In case of any error - just shut down
    pass

if enableSQLITE:
    sqliteProcess.terminate()
    pykmsProcess.terminate()
