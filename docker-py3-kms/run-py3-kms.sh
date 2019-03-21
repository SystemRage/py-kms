docker run -d --name py3-kms \
    -p 1688:1688 \
    -e TCP_ADDRESS=0.0.0.0 \
    -e TCP_PORT=1688 \
    -e LOGLEVEL=DEBUG \
    -e LOGFILE=/var/log/py3-kms.log \
    -v /etc/localtime:/etc/localtime:ro \
    -v /var/log:/var/log:rw \
    --restart unless-stopped pykms/pykms:py3-kms
