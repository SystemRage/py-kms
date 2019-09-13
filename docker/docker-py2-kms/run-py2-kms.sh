docker stop py2-kms
docker rm py2-kms
docker run -d --name py2-kms \
    -p 8080:8080 \
    -p 1688:1688 \
    -e IP=0.0.0.0 \
    -e PORT=1688 \
    -e CLIENT_COUNT=30 \
    -e SQLITE=true \
    -e HWID=RANDOM \
    -e LOGLEVEL=INFO \
    -e LOGFILE=/var/log/py2-kms.log \
    -e LOGSIZE=2 \
    -v /etc/localtime:/etc/localtime:ro \
    -v /var/log:/var/log:rw \
    --restart unless-stopped pykms/pykms:py2-kms
