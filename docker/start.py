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

dbPath = os.path.join(os.sep, 'home', 'py-kms', 'db', 'pykms_database.db')
log_level_bootstrap = log_level = os.environ.get('LOGLEVEL', 'INFO')
if log_level_bootstrap == "MININFO":
  log_level_bootstrap = "INFO"
log_file = os.environ.get('LOGFILE', 'STDOUT')
listen_ip = os.environ.get('IP', '::').split()
listen_port = os.environ.get('PORT', '1688')

def start_kms():
  # Make sure the full path to the db exists
  if not os.path.exists(os.path.dirname(dbPath)):
    os.makedirs(os.path.dirname(dbPath), exist_ok=True)

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
  command.append('-s')
  command.append(dbPath)

  loggersrv.debug("server_cmd: %s" % (" ".join(str(x) for x in command).strip()))
  pykms_process = subprocess.Popen(command)

  try:
    time.sleep(2) # Wait for the server to start up
    pykms_webui_env = os.environ.copy()
    pykms_webui_env['PYKMS_SQLITE_DB_PATH'] = dbPath
    pykms_webui_env['PORT'] = '8080'
    pykms_webui_env['PYKMS_LICENSE_PATH'] = '/LICENSE'
    pykms_webui_process = subprocess.Popen(['gunicorn', '--log-level', os.environ.get('LOGLEVEL'), 'pykms_WebUI:app'], env=pykms_webui_env)
  except Exception as e:
    loggersrv.error("Failed to start webui: %s" % e)

  try:
    pykms_process.wait()
  except Exception:
    # In case of any error - just shut down
    pass
  except KeyboardInterrupt:
    pass
  pykms_webui_process.terminate()
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
