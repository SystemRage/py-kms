#!/usr/bin/python3

# Need root privileges to change timezone, and user uid/gid

import grp
import os
import pwd
import subprocess

PYTHON3 = '/usr/bin/python3'
dbPath = os.path.join(os.sep, 'home', 'py-kms', 'db', 'pykms_database.db')
log_level = os.getenv('LOGLEVEL', 'INFO')


def change_uid_grp():
  user_db_entries = pwd.getpwnam("py-kms")
  user_grp_db_entries = grp.getgrnam("power_users")
  uid = user_db_entries.pw_uid
  gid = user_grp_db_entries.gr_gid
  new_gid = int(os.getenv('GID', str(gid)))
  new_uid = int(os.getenv('UID', str(uid)))
  os.chown("/home/py-kms", new_uid, new_gid)
  os.chown("/usr/bin/start.py", new_uid, new_gid)
  if os.path.isfile(dbPath): os.chown(dbPath, new_uid, new_gid)
  os.system("ls -al /usr/bin/start.py")
  if gid != new_gid:
    print("Setting gid to " + str(new_gid), flush=True)
    os.setgid(gid)
  if uid != new_uid:
    print("Setting uid to " + str(new_uid), flush=True)
    os.setuid(uid)


def change_tz():
  tz = os.getenv('TZ', 'etc/UTC')
  # TZ is not symlinked and defined TZ exists
  if tz not in os.readlink('/etc/localtime') and os.path.isfile('/usr/share/zoneinfo/' + tz):
    print("Setting timezone to " + tz, flush=True)
    os.remove('/etc/localtime')
    os.symlink(os.path.join('/usr/share/zoneinfo/', tz), '/etc/localtime')


# Main
if (__name__ == "__main__"):
  change_tz()
  subprocess.call(PYTHON3 + " /usr/bin/start.py", preexec_fn=change_uid_grp(), shell=True)
