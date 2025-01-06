#!/usr/bin/python3 -u
import os
import sys
import logging

def do_check(logger):
  import socket
  listen_ip = os.environ.get('IP', '::').split()
  listen_ip.insert(0, '127.0.0.1') # always try to connect to localhost first
  listen_port = os.environ.get('PORT', '1688')
  for ip in listen_ip:
    try:
      s = socket.socket(socket.AF_INET6 if ':' in ip else socket.AF_INET, socket.SOCK_STREAM)
      s.settimeout(1) # 1 second timeout
      address = ip if ':' in ip else (ip, int(listen_port))
      logger.debug(f"Trying to connect to {address}...")
      s.connect(address)
      s.close()
      return True
    except:
      pass
  return False # no connection could be established


if __name__ == '__main__':
  log_level_bootstrap = log_level = os.getenv('LOGLEVEL', 'INFO')
  if log_level_bootstrap == "MININFO":
    log_level_bootstrap = "INFO"
  loggersrv = logging.getLogger('healthcheck.py')
  loggersrv.setLevel(log_level_bootstrap)
  streamhandler = logging.StreamHandler(sys.stdout)
  streamhandler.setLevel(log_level_bootstrap)
  formatter = logging.Formatter(fmt='\x1b[94m%(asctime)s %(levelname)-8s %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
  streamhandler.setFormatter(formatter)
  loggersrv.addHandler(streamhandler)
  
  sys.exit(0 if do_check(loggersrv) else 1)
