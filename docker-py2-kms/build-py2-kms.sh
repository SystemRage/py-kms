docker stop py2-kms
docker rm py2-kms
docker image rm pykms/pykms:py2-kms
docker build -t pykms/pykms:py2-kms .
