#!/usr/bin/python3 -u

# Need root privileges to change timezone, and user uid/gid, file/folder ownernship

import grp
import logging
import os
import pwd
import subprocess
import sys

PYTHON3 = '/usr/bin/python3'
dbPath = os.path.join(os.sep, 'home', 'py-kms', 'db', 'pykms_database.db')
log_level = os.getenv('LOGLEVEL', 'INFO')

loggersrv = logging.getLogger('logsrv')
loggersrv.setLevel(log_level)
streamhandler = logging.StreamHandler(sys.stdout)
streamhandler.setLevel(log_level)
formatter = logging.Formatter(fmt = '\x1b[94m%(asctime)s %(levelname)-8s %(message)s',
                              datefmt = '%a, %d %b %Y %H:%M:%S',)
streamhandler.setFormatter(formatter)
loggersrv.addHandler(streamhandler)


def change_uid_grp():
  user_db_entries = pwd.getpwnam("py-kms")
  user_grp_db_entries = grp.getgrnam("power_users")
  uid = int(user_db_entries.pw_uid)
  gid = int(user_grp_db_entries.gr_gid)
  new_gid = int(os.getenv('GID', str(gid)))
  new_uid = int(os.getenv('UID', str(uid)))
  os.chown("/home/py-kms", new_uid, new_gid)
  os.chown("/usr/bin/start.py", new_uid, new_gid)
  if os.path.isfile(dbPath):
    os.chown(dbPath, new_uid, new_gid)
    loggersrv.debug("%s" %str(subprocess.check_output("ls -al " + dbPath, shell=True)))

  loggersrv.info("Setting gid to '%s'." % str(new_gid))
  os.setgid(new_gid)

  loggersrv.info("Setting uid to '%s'." % str(new_uid))
  os.setuid(new_uid)


def change_tz():
  tz = os.getenv('TZ', 'etc/UTC')
  # TZ is not symlinked and defined TZ exists
  if tz not in os.readlink('/etc/localtime') and os.path.isfile('/usr/share/zoneinfo/' + tz):
    loggersrv.info("Setting timzeone to %s" % tz )
    os.remove('/etc/localtime')
    os.symlink(os.path.join('/usr/share/zoneinfo/', tz), '/etc/localtime')
    f = open("/etc/timezone", "w")
    f.write(tz)
    f.close()


# Main
if (__name__ == "__main__"):
  loggersrv.info("Log level: %s" % log_level)
  change_tz()
  subprocess.call(PYTHON3 + " -u /usr/bin/start.py", preexec_fn=change_uid_grp(), shell=True)
