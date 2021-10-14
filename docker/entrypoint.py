#!/usr/bin/python3

# Need root privileges to change timezone, and user uid/gid

import grp
import os
import pwd
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

def change_uid_grp():
  user_db_entries = pwd.getpwnam("py-kms")
  user_grp_db_entries = grp.getgrnam("power_users")
  uid = user_db_entries.pw_uid
  gid = user_grp_db_entries.gr_gid
  new_gid = int(os.getenv('GID', str(gid)))
  new_uid = int(os.getenv('UID', str(uid)))
  os.chown("/home/py-kms", new_uid, new_uid)
  os.chown("/db/pykms_database.db", new_uid, new_uid)
  if gid != new_gid:
    print("Setting gid to " + str(new_gid), flush=True)
    os.setgid(gid)
  if uid != new_uid:
    print("Setting uid to " + str(new_uid), flush=True)
    os.setuid(uid)
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


def change_tz():
  tz = os.getenv('TZ', 'etc/UTC')
  # TZ is not symlinked and defined TZ exists
  if tz not in os.readlink(LTIME) and os.path.isfile('/usr/share/zoneinfo/' + tz):
    print("Setting timezone to " + tz, flush=True)
    os.remove(LTIME)
    os.symlink(os.path.join('/usr/share/zoneinfo/', tz), LTIME)
# In case SQLITE is defined: Start the web interface
if enableSQLITE:
    time.sleep(5) # The server may take a while to start
    if not os.path.isfile(dbPath):
        # Start a dummy activation to ensure the database file is created
        subprocess.run(['/usr/bin/python3', 'pykms_Client.py', listenIP, listenPort, '-m', 'Windows10', '-n', 'DummyClient', '-c', 'ae3a27d1-b73a-4734-9878-70c949815218'])
    sqliteProcess = subprocess.Popen(['/usr/bin/python3', sqliteWebPath, '-H', listenIP, '--read-only', '-x', dbPath, '-p', os.environ.get('SQLITE_PORT', 8080)])


LTIME = '/etc/localtime'
PYTHON3 = '/usr/bin/python3'
log_level = os.getenv('LOGLEVEL', 'INFO')

# Main
if (__name__ == "__main__"):
  change_tz()
  change_uid_grp()
  subprocess.call("/usr/bin/start.py",shell=True)
