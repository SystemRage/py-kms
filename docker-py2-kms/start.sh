#!/bin/sh
# EN: Start daemons
# RU: Запуск демонов
cd /home/py-kms/py2-kms
/usr/bin/python server.py ${TCP_ADDRESS} ${TCP_PORT} -v ${LOGLEVEL} -f ${LOGFILE}
