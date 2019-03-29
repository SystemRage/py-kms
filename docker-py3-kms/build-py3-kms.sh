docker stop py3-kms
docker rm py3-kms
docker image rm pykms/pykms:py3-kms
docker build -t pykms/pykms:py3-kms .
