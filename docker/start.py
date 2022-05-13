#!/usr/bin/python3 -u

# This replaces the old start.sh and ensures all arguments are bound correctly from the environment variables...
import logging
import os
import subprocess
import sys
import time

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
enableSQLITE = os.environ.get('SQLITE', 'false').lower() == 'true' and  os.environ.get('TYPE') != 'MINIMAL'
dbPath = os.path.join(os.sep, 'home', 'py-kms', 'db', 'pykms_database.db')
log_level_bootstrap = log_level = os.environ.get('LOGLEVEL', 'INFO')
if log_level_bootstrap == "MININFO":
  log_level_bootstrap = "INFO"
log_file = os.environ.get('LOGFILE', 'STDOUT')
listen_ip = os.environ.get('IP', '0.0.0.0').split()
listen_port = os.environ.get('PORT', '1688')
sqlite_port = os.environ.get('SQLITE_PORT', '8080')


def start_kms_client():
  if not os.path.isfile(dbPath):
    # Start a dummy activation to ensure the database file is created
    client_cmd = [PYTHON3, '-u', 'pykms_Client.py', listen_ip[0], listen_port,
                  '-m', 'Windows10', '-n', 'DummyClient', '-c', 'ae3a27d1-b73a-4734-9878-70c949815218',
                  '-V', log_level, '-F', log_file]
    if os.environ.get('LOGSIZE', '') != "":
      client_cmd.append('-S')
      client_cmd.append(os.environ.get('LOGSIZE'))
    loggersrv.info("Starting a dummy activation to ensure the database file is created")
    loggersrv.debug("client_cmd: %s" % (" ".join(str(x) for x in client_cmd).strip()))

    subprocess.run(client_cmd)


def start_kms():
  sqlite_process = None
  # Build the command to execute
  command = [PYTHON3, '-u', 'pykms_Server.py', listen_ip[0], listen_port]
  for (arg, env) in argumentVariableMapping.items():
    if env in os.environ and os.environ.get(env) != '':
      command.append(arg)
      command.append(os.environ.get(env))
  if len(listen_ip) > 1:
    command.append("connect")
    for i in range(1, len(listen_ip)):
      command.append("-n")
      command.append(listen_ip[i] + "," + listen_port)

  if enableSQLITE:
    loggersrv.info("Storing database file to %s" % dbPath)
    command.append('-s')
    command.append(dbPath)
    os.makedirs(os.path.dirname(dbPath), exist_ok=True)

  loggersrv.debug("server_cmd: %s" % (" ".join(str(x) for x in command).strip()))
  pykms_process = subprocess.Popen(command)

  # In case SQLITE is defined: Start the web interface
  if enableSQLITE:
    time.sleep(5)  # The server may take a while to start
    start_kms_client()
    sqlite_cmd = ['sqlite_web', '-H', listen_ip[0], '--read-only', '-x',
                  dbPath, '-p', sqlite_port]

    loggersrv.debug("sqlite_cmd: %s" % (" ".join(str(x) for x in sqlite_cmd).strip()))
    sqlite_process = subprocess.Popen(sqlite_cmd)

  try:
    pykms_process.wait()
  except Exception:
    # In case of any error - just shut down
    pass
  except KeyboardInterrupt:
    pass

  if enableSQLITE:
    if None != sqlite_process: sqlite_process.terminate()
    pykms_process.terminate()


# Main
if (__name__ == "__main__"):
  loggersrv = logging.getLogger('logsrv')
  loggersrv.setLevel(log_level_bootstrap)
  streamhandler = logging.StreamHandler(sys.stdout)
  streamhandler.setLevel(log_level_bootstrap)
  formatter = logging.Formatter(fmt='\x1b[94m%(asctime)s %(levelname)-8s %(message)s',
                                datefmt='%a, %d %b %Y %H:%M:%S')
  streamhandler.setFormatter(formatter)
  loggersrv.addHandler(streamhandler)
  loggersrv.debug("user id: %s" % os.getuid())
  start_kms()
