# HowTo start the image...
```
docker run -it -d --name py3-kms \
    -p 8080:8080 \
    -p 1688:1688 \
    -e IP=0.0.0.0 \
    -e PORT=1688 \
    -e HWID=RANDOM \
    -e LOGLEVEL=INFO \
    -e LOGSIZE=2 \
    -e LOGFILE=/var/log/py3-kms.log \
    -v /etc/localtime:/etc/localtime:ro \
    -v /var/log:/var/log:rw \
    --restart unless-stopped realsimonmicro/py-kms:minimal
```
