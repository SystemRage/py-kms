# Switch to the target image
FROM alpine:3.14

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
ENV LOGFILE STDOUT
ENV LOGSIZE ""
ENV TZ America/Chicago

COPY ./py-kms /home/py-kms

#hadolint ignore=DL3013,DL3018
RUN apk add --no-cache --update \
    bash \
    git \
    python3 \
    py3-argparse \
    py3-flask \
    py3-pygments \
    python3-tkinter \
    sqlite-libs \
    py3-pip \
    build-base python3-dev \
    ca-certificates \
    duplicity \
    su-exec \
    sudo \
    tzdata \
    shadow \
    && git clone --branch master --depth 1 https://github.com/coleifer/sqlite-web.git /tmp/sqlite_web \
    && mv /tmp/sqlite_web/sqlite_web /home/  \
    && rm -rf /tmp/sqlite_web \
    && pip3 install --no-cache-dir peewee tzlocal pytz pysqlite3 wheel \
    && apk del git build-base python3-dev \
    && mkdir /db/ \
    && addgroup power_users  \
    && adduser -S py-kms -G users -s /bin/bash \
    && usermod -a -G power_users py-kms \
    && chown py-kms:users /home/py-kms \
    # Fix undefined timezone, in case the user did not mount the /etc/localtime
    && ln -sf /usr/share/zoneinfo/UTC /etc/localtime

COPY docker/entrypoint.py /usr/bin/entrypoint.py
COPY docker/start.py /usr/bin/start.py

RUN chmod 755 /usr/bin/entrypoint.py

WORKDIR /home/py-kms
#USER py-kms
EXPOSE ${PORT}/tcp
EXPOSE 8080

ENTRYPOINT [ "/usr/bin/python3", "/usr/bin/entrypoint.py" ]
CMD ["/usr/bin/start.py"]
