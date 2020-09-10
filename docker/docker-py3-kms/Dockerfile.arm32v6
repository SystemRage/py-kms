# Prepare the multiarch env
FROM alpine AS builder
RUN apk add curl && curl -L "https://github.com/balena-io/qemu/releases/download/v4.0.0%2Bbalena2/qemu-4.0.0.balena2-arm.tar.gz" | tar zxvf - -C . --strip-components 1

# Switch to the target image
FROM arm32v6/alpine:3.12

# Import qemu from the preparation
COPY --from=builder qemu-arm-static /usr/bin

ENV IP		0.0.0.0
ENV PORT		1688
ENV EPID		""
ENV LCID		1033
ENV CLIENT_COUNT	26
ENV ACTIVATION_INTERVAL	120
ENV RENEWAL_INTERVAL	10080
ENV SQLITE		false
ENV HWID		"364F463A8863D35F"
ENV LOGLEVEL		ERROR
ENV LOGFILE		/var/log/pykms_logserver.log
ENV LOGSIZE		""

COPY start.sh /usr/bin/start.sh

RUN apk add --no-cache --update \
	bash \
	git \
	py3-argparse \
	py3-flask \
	py3-pygments \
	python3-tkinter \
	sqlite-libs \
	py3-pip && \
    git clone https://github.com/SystemRage/py-kms.git /tmp/py-kms && \
    git clone https://github.com/coleifer/sqlite-web.git /tmp/sqlite_web && \
    mv /tmp/py-kms/py-kms /home/ && \
    mv /tmp/sqlite_web/sqlite_web /home/ && \
    rm -rf /tmp/py-kms && \
    rm -rf /tmp/sqlite_web && \
    pip3 install peewee tzlocal pysqlite3 && \
    chmod a+x /usr/bin/start.sh && \
    apk del git

WORKDIR /home/py-kms

EXPOSE ${PORT}/tcp

ENTRYPOINT ["/usr/bin/start.sh"]
