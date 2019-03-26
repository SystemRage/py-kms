FROM ubuntu:latest

# docker build -t ubuntu1604py36
FROM ubuntu:16.04

RUN apt-get update && \
  apt-get install -y software-properties-common vim && \
  add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update -y

RUN apt-get install -y build-essential python3.6 python3.6-dev python3-pip python3.6-venv python-sqlite && \
        apt-get install -y git

# update pip
RUN python3.6 -m pip install pip --upgrade && \
        python3.6 -m pip install wheel


ADD py3-kms /app
CMD ["/usr/bin/python3.6", "/app/server.py"]
