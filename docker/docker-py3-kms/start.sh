#!/bin/bash
# EN: Start daemons
# RU: Запуск демонов
cd /home/py-kms/py-kms
if [ "$SQLITE" == false ];
then
  if [ "$EPID" == "" ];
  then
    /usr/bin/python3 pykms_Server.py ${IP} ${PORT} -l ${LCID} -c ${CLIENT_COUNT} -a ${ACTIVATION_INTERVAL} -r ${RENEWAL_INTERVAL} -w ${HWID} -V ${LOGLEVEL} -F ${LOGFILE}
  else
    /usr/bin/python3 pykms_Server.py ${IP} ${PORT} -e ${EPID} -l ${LCID} -c ${CLIENT_COUNT} -a ${ACTIVATION_INTERVAL} -r ${RENEWAL_INTERVAL} -s ${SQLITE} -w ${HWID} -V ${LOGLEVEL} -F ${LOGFILE}
  fi
else
  if [ "$EPID" == "" ];
  then
    /bin/bash -c "/usr/bin/python3 pykms_Server.py ${IP} ${PORT} -l ${LCID} -c ${CLIENT_COUNT} -a ${ACTIVATION_INTERVAL} -r ${RENEWAL_INTERVAL} -s -w ${HWID} -V ${LOGLEVEL} -F ${LOGFILE} &" && /usr/bin/python3 pykms_Client.py ${IP} ${PORT} -m Windows10 && /usr/bin/python3 /home/sqlite_web/sqlite_web.py -H ${IP} -x ${PWD}/clients.db --read-only
  else
    /bin/bash -c "/usr/bin/python3 pykms_Server.py ${IP} ${PORT} -e ${EPID} -l ${LCID} -c ${CLIENT_COUNT} -a ${ACTIVATION_INTERVAL} -r ${RENEWAL_INTERVAL} -s -w ${HWID} -V ${LOGLEVEL} -F ${LOGFILE} &" && /usr/bin/python3 pykms_Client.py ${IP} ${PORT} -m Windows10 && /usr/bin/python3 /home/sqlite_web/sqlite_web.py -H ${IP} -x ${PWD}/clients.db --read-only
  fi
fi
