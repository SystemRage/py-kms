# Switch to the target image
FROM alpine:3.15

ARG BUILD_COMMIT=unknown
ARG BUILD_BRANCH=unknown

ENV IP ::
ENV DUALSTACK 1
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
ENV TZ America/Chicago
ENV WEBUI 1

COPY docker/docker-py3-kms/requirements.txt /home/py-kms/
RUN apk add --no-cache --update \
  bash \
  python3 \
  py3-pip \
  sqlite-libs \
  ca-certificates \
  tzdata \
  shadow \
  && pip3 install --no-cache-dir -r /home/py-kms/requirements.txt \
  && mkdir /db/ \
  && adduser -S py-kms -G users -s /bin/bash \
  && chown py-kms:users /home/py-kms \
  # Fix undefined timezone, in case the user did not mount the /etc/localtime
  && ln -sf /usr/share/zoneinfo/UTC /etc/localtime

COPY py-kms /home/py-kms/
COPY docker/entrypoint.py /usr/bin/entrypoint.py
COPY docker/healthcheck.py /usr/bin/healthcheck.py
COPY docker/start.py /usr/bin/start.py
RUN chmod 555 /usr/bin/entrypoint.py /usr/bin/healthcheck.py /usr/bin/start.py

# Web-interface specifics
COPY LICENSE /LICENSE
RUN echo "$BUILD_COMMIT" > /VERSION && echo "$BUILD_BRANCH" >> /VERSION

WORKDIR /home/py-kms

EXPOSE ${PORT}/tcp
EXPOSE 8080/tcp

HEALTHCHECK --interval=5m --timeout=10s --start-period=10s --retries=3 CMD /usr/bin/python3 /usr/bin/healthcheck.py

ENTRYPOINT [ "/usr/bin/python3", "-u", "/usr/bin/entrypoint.py" ]
