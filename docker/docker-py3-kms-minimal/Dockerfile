# This is a minimized version from docker/docker-py3-kms/Dockerfile without SQLite support to further reduce image size
FROM alpine:3.15

ENV IP 0.0.0.0
ENV PORT 1688
ENV EPID ""
ENV LCID 1033
ENV CLIENT_COUNT 26
ENV ACTIVATION_INTERVAL 120
ENV RENEWAL_INTERVAL 10080
ENV HWID RANDOM
ENV LOGLEVEL INFO
ENV LOGFILE STDOUT
ENV LOGSIZE ""

COPY ./py-kms /home/py-kms
#hadolint ignore=DL3013,DL3018
RUN apk add --no-cache --update \
  bash \
  git \
  py3-argparse \
  py3-flask \
  py3-pygments \
  python3-tkinter \
  sqlite-libs \
  py3-pip \
  tzdata  \
  shadow \
  netcat-openbsd \
  build-base python3-dev \
  && pip3 install --no-cache-dir peewee tzlocal pytz wheel dnspython \
  && apk del git build-base python3-dev \
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

EXPOSE ${PORT}/tcp

HEALTHCHECK --interval=5m --timeout=3s --start-period=10s --retries=4 CMD echo | nc -z ${IP%% *} ${PORT} || exit 1

ENTRYPOINT ["/usr/bin/python3", "-u","/usr/bin/entrypoint.py"]
CMD ["/usr/bin/start.py"]
