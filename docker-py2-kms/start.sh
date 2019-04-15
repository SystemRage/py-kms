#!/bin/bash
# EN: Start daemons
# RU: Запуск демонов
cd /home/py-kms/py2-kms
if [ "$SQLITE" == false ];
then
  if [ "$EPID" == "" ];
  then
    /usr/bin/python server.py ${IP} ${PORT} -l ${LCID} -c ${CLIENT_COUNT} -a ${ACTIVATION_INTERVAL} -r ${RENEWAL_INTERVAL} -w ${HWID} -v ${LOGLEVEL} -f ${LOGFILE}
  else
    /usr/bin/python server.py ${IP} ${PORT} -e ${EPID} -l ${LCID} -c ${CLIENT_COUNT} -a ${ACTIVATION_INTERVAL} -r ${RENEWAL_INTERVAL} -s ${SQLITE} -w ${HWID} -v ${LOGLEVEL} -f ${LOGFILE}
  fi
else
  if [ "$EPID" == "" ];
  then
    /bin/bash -c "/usr/bin/python server.py ${IP} ${PORT} -l ${LCID} -c ${CLIENT_COUNT} -a ${ACTIVATION_INTERVAL} -r ${RENEWAL_INTERVAL} -s -w ${HWID} -v ${LOGLEVEL} -f ${LOGFILE} &" && /usr/bin/python client.py ${IP} ${PORT} -m Windows10 && /usr/bin/python /home/sqlite_web/sqlite_web.py -H ${IP} -x ${PWD}/clients.db
  else
    /bin/bash -c "/usr/bin/python server.py ${IP} ${PORT} -e ${EPID} -l ${LCID} -c ${CLIENT_COUNT} -a ${ACTIVATION_INTERVAL} -r ${RENEWAL_INTERVAL} -s -w ${HWID} -v ${LOGLEVEL} -f ${LOGFILE} &" && /usr/bin/python client.py ${IP} ${PORT} -m Windows10 && /usr/bin/python /home/sqlite_web/sqlite_web.py -H ${IP} -x ${PWD}/clients.db
  fi
fi
