# This is a minimized version from docker/docker-py3-kms/Dockerfile without SQLite support to further reduce image size
FROM alpine:3.14

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
  pip3 install --no-cache peewee tzlocal pytz wheel && \
  apk del git build-base python3-dev && \
  # Fix undefined timezone, in case the user did not mount the /etc/localtime
  ln -sf /usr/share/zoneinfo/UTC /etc/localtime

WORKDIR /home/py-kms

EXPOSE ${PORT}/tcp

COPY docker/entrypoint.py /usr/bin/entrypoint.py
RUN chmod a+x /usr/bin/entrypoint.py
ENTRYPOINT ["/usr/bin/python3", "/usr/bin/entrypoint.py"]
#CMD["/usr/bin/start.py"]
