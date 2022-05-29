# Switch to the target image
FROM alpine:3.15

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

COPY py-kms /home/py-kms/
COPY docker/requirements.txt /home/py-kms/
RUN apk add --no-cache --update \
  bash \
  python3 \
  py3-pip \
  python3-tkinter \
  sqlite-libs \
  ca-certificates \
  tzdata \
  shadow \
  netcat-openbsd \
  && pip3 install --no-cache-dir -r /home/py-kms/requirements.txt \
  #&& apk del git build-base python3-dev \
  && mkdir /db/ \
  && adduser -S py-kms -G users -s /bin/bash \
  && chown py-kms:users /home/py-kms \
  # Fix undefined timezone, in case the user did not mount the /etc/localtime
  && ln -sf /usr/share/zoneinfo/UTC /etc/localtime

COPY docker/entrypoint.py /usr/bin/entrypoint.py
COPY docker/start.py /usr/bin/start.py

RUN chmod 755 /usr/bin/entrypoint.py

WORKDIR /home/py-kms

EXPOSE ${PORT}/tcp
EXPOSE 8080

HEALTHCHECK --interval=5m --timeout=3s --start-period=10s --retries=4 CMD echo | nc -z ${IP%% *} ${PORT} || exit 1

ENTRYPOINT [ "/usr/bin/python3", "-u", "/usr/bin/entrypoint.py" ]
