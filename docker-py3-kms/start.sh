#!/bin/sh
# EN: Start daemons
# RU: Запуск демонов
cd /home/py-kms/py3-kms
/usr/bin/python3 server.py ${TCP_ADDRESS} ${TCP_PORT} -v ${LOGLEVEL} -f ${LOGFILE}
