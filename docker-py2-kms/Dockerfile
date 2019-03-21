# Use Alpine Linux
FROM alpine:3.8

# Maintainer
#MAINTAINER Artur Petrov <artur@phpchain.ru>

# EN: Variables
# RU: Переменные

# EN: IP-address
# RU: IP-адрес
ENV TCP_ADDRESS		0.0.0.0
# The IP address to listen on. The default is "0.0.0.0" (all interfaces).

# EN: TCP-port
# RU: TCP-порт
ENV TCP_PORT		1688
# The network port to listen on. The default is "1688".

# EN: log level ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")
# RU: Уровень логирования ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")
ENV LOGLEVEL		ERROR
# Use this flag to set a Loglevel. The default is "ERROR".

# EN: log file
# RU: Лог-файл
ENV LOGFILE		/var/log/pykms_server.log

# EN: Startup script
# RU: Скрипт автозапуска
COPY start.sh /usr/bin/start.sh

# EN: Software installation
# RU: Установка программного обеспечения
RUN     echo "http://dl-cdn.alpinelinux.org/alpine/latest-stable/main" >> /etc/apk/repositories && \
    apk update && \
    apk upgrade && \
    apk add --update \
	bash \
	git \
	py2-argparse && \

# EN: Clone git-repo
# RU: Клонирование git-репозитория
git clone https://github.com/SystemRage/py-kms.git /home/py-kms && \

# EN: Change permissions
# RU: Меняем права доступа
chmod a+x /usr/bin/start.sh && \

# EN: Clear after install software
# RU: Очистка после установки программного обеспечения
apk del git

# Set Workdir
WORKDIR /home/py-kms/py2-kms

# Expose ports
EXPOSE ${TCP_PORT}/tcp

# Entry point
ENTRYPOINT ["/usr/bin/start.sh"]
