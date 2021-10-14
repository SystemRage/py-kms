FROM alpine:3.12

ENV IP 0.0.0.0
ENV PORT 1688
ENV EPID ""
ENV LCID 1033
ENV CLIENT_COUNT 26
ENV ACTIVATION_INTERVAL 120
ENV RENEWAL_INTERVAL 10080
ENV SQLITE true
ENV SQLITE_PORT	8080
ENV HWID RANDOM
ENV LOGLEVEL INFO
ENV LOGFILE /dev/stdout
ENV LOGSIZE ""

COPY ./py-kms /home/py-kms

RUN apk add --no-cache --update \
	bash \
	git \
	py3-argparse \
	py3-flask \
	py3-pygments \
	python3-tkinter \
	sqlite-libs \
	py3-pip \
	tzdata \
	build-base python3-dev && \
    git clone https://github.com/coleifer/sqlite-web.git /tmp/sqlite_web && \
    cd /tmp/sqlite_web && \
    git checkout 2e7c85da3d37f80074ed3ae39b5851069b4f301c && \
    cd / && \
    mv /tmp/sqlite_web/sqlite_web /home/ && \
    rm -rf /tmp/sqlite_web && \
    pip3 install peewee tzlocal pytz pysqlite3 && \
    apk del git build-base python3-dev

# Fix undefined timezone, in case the user did not mount the /etc/localtime
RUN cp /usr/share/zoneinfo/UTC /etc/localtime

WORKDIR /home/py-kms

EXPOSE ${SQLITE_PORT}/tcp
EXPOSE ${PORT}/tcp

COPY docker/entrypoint.py /usr/bin/entrypoint.py
RUN chmod a+x /usr/bin/entrypoint.py
ENTRYPOINT ["/usr/bin/python3", "/usr/bin/entrypoint.py"]
