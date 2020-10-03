# This is a minimized version from docker/docker-py3-kms/Dockerfile without SQLite support to further reduce image size

# Prepare the multiarch env
FROM alpine AS builder
RUN apk add curl && curl -L "https://github.com/balena-io/qemu/releases/download/v4.0.0%2Bbalena2/qemu-4.0.0.balena2-arm.tar.gz" | tar zxvf - -C . --strip-components 1

# Switch to the target image
FROM arm32v7/alpine:3.12

# Import qemu from the preparation
COPY --from=builder qemu-arm-static /usr/bin

ENV IP		0.0.0.0
ENV PORT		1688
ENV EPID		""
ENV LCID		1033
ENV CLIENT_COUNT	26
ENV ACTIVATION_INTERVAL	120
ENV RENEWAL_INTERVAL	10080
ENV HWID		"RANDOM"
ENV LOGLEVEL	INFO
ENV LOGFILE		/var/log/pykms_logserver.log
ENV LOGSIZE		""

RUN apk add --no-cache --update \
	bash \
	git \
	py3-argparse \
	py3-flask \
	py3-pygments \
	python3-tkinter \
	sqlite-libs \
	py3-pip && \
    pip3 install peewee tzlocal && \
    git clone https://github.com/SystemRage/py-kms/ /tmp/py-kms && \
    mv /tmp/py-kms/py-kms /home/ && \
    rm -rf /tmp/py-kms && \
    apk del git

WORKDIR /home/py-kms

EXPOSE ${PORT}/tcp

ENTRYPOINT /usr/bin/python3 pykms_Server.py ${IP} ${PORT} -l ${LCID} -c ${CLIENT_COUNT} -a ${ACTIVATION_INTERVAL} -r ${RENEWAL_INTERVAL} -w ${HWID} -V ${LOGLEVEL} -F ${LOGFILE}
