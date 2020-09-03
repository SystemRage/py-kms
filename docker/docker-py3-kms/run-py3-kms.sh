docker stop py3-kms
docker rm py3-kms
docker run -d --name py3-kms \
    -t \
    -p 8080:8080 \
    -p 1688:1688 \
    -e IP=0.0.0.0 \
    -e PORT=1688 \
    -e SQLITE=true \
    -e HWID=RANDOM \
    -e LOGLEVEL=INFO \
    -e LOGFILE=/var/log/pykms_logserver.log \
    -e LOGSIZE=2 \
    -v /etc/localtime:/etc/localtime:ro \
    -v /var/log:/var/log:rw \
    --restart unless-stopped pykmsorg/py-kms:python3
