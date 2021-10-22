#!/usr/bin/python3

# This replaces the old start.sh and ensures all arguments are bound correctly from the environment variables...
import os
import subprocess
import time

LTIME = '/etc/localtime'
PYTHON3 = '/usr/bin/python3'
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
enableSQLITE = os.path.isfile(sqliteWebPath) and os.environ.get('SQLITE', 'false').lower() == 'true'
dbPath = os.path.join(os.sep, 'home', 'py-kms', 'db', 'pykms_database.db')
log_level = os.getenv('LOGLEVEL', 'INFO')


def start_kms_client():
  if not os.path.isfile(dbPath):
    # Start a dummy activation to ensure the database file is created
    client_cmd = [PYTHON3, 'pykms_Client.py', os.environ.get('IP', "0.0.0.0"), os.environ.get('PORT', 1688),
                  '-m', 'Windows10', '-n', 'DummyClient', '-c', 'ae3a27d1-b73a-4734-9878-70c949815218',
                  '-V', os.environ.get('LOGLEVEL', 'INFO'), '-F', os.environ.get('LOGFILE', 'STDOUT')]
    if os.environ.get('LOGSIZE', '') != "":
      client_cmd.append('-S')
      client_cmd.append(os.environ.get('LOGSIZE'))

    if log_level.lower() in ['info', 'debug']:
      print("Starting a dummy activation to ensure the database file is created", flush=True)
    if log_level.lower() == 'debug':
      print("client_cmd: " + str(client_cmd), flush=True)

    subprocess.run(client_cmd)


def start_kms():
  # Build the command to execute
  command = [PYTHON3, 'pykms_Server.py', os.environ.get('IP'), os.environ.get('PORT')]
  for (arg, env) in argumentVariableMapping.items():
    if env in os.environ and os.environ.get(env) != '':
      command.append(arg)
      command.append(os.environ.get(env))

  if enableSQLITE:
    print('Storing database file to ' + dbPath, flush=True)
    command.append('-s')
    command.append(dbPath)

  if log_level.lower() == 'debug':
    print("server_cmd: " + str(command), flush=True)

  pykms_process = subprocess.Popen(command)

  # In case SQLITE is defined: Start the web interface
  if enableSQLITE:
    time.sleep(5)  # The server may take a while to start
    os.system('ls -al ' + dbPath)
    start_kms_client()
    sqlite_cmd = [PYTHON3, '/home/sqlite_web/sqlite_web.py', '-H', os.environ.get('IP'), '--read-only', '-x', dbPath,
                  '-p', os.environ.get('SQLITE_PORT')]

    if log_level.lower() == 'debug':
      print("sqlite_cmd: " + str(sqlite_cmd), flush=True)

    sqlite_process = subprocess.Popen(sqlite_cmd)

  try:
    pykms_process.wait()
  except Exception:
    # In case of any error - just shut down
    pass

  if enableSQLITE:
    sqlite_process.terminate()
    pykms_process.terminate()


# Main
if (__name__ == "__main__"):
  start_kms()
