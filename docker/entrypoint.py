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

# Build the command to execute
command = ['/usr/bin/python3', 'pykms_Server.py', os.environ.get('IP'), os.environ.get('PORT')]
for (arg, env) in argumentVariableMapping.items():
    if env in os.environ and os.environ.get(env) != '':
        command.append(arg)
        command.append(os.environ.get(env))
        
enableSQLITE = os.environ.get('SQLITE').lower() == 'true'
os.makedirs('db', exist_ok=True)
dbPath = os.path.join(os.environ.get('PWD'), 'db', 'pykms_database.db')
if enableSQLITE:
    command.append('-s')
    command.append(dbPath)

pykmsProcess = subprocess.Popen(command)

# In case SQLITE is defined: Start the web interface
if enableSQLITE:
    time.sleep(5) # The server may take a while to start
    if not os.path.isfile(dbPath):
        # Start a dummy activation to ensure the database file is created
        subprocess.run(['/usr/bin/python3', 'pykms_Client.py', os.environ.get('IP'), os.environ.get('PORT'), '-m', 'Windows10', '-n', 'DummyClient', '-c', 'ae3a27d1-b73a-4734-9878-70c949815218'])
    sqliteProcess = subprocess.Popen(['/usr/bin/python3', '/home/sqlite_web/sqlite_web.py', '-H', os.environ.get('IP'), '--read-only', '-x', dbPath, '-p', os.environ.get('SQLITE_PORT')])    

try:
    pykmsProcess.wait()
except:
    # In case of any error - just shut down
    pass

if enableSQLITE:
    sqliteProcess.terminate()
    pykmsProcess.terminate()
