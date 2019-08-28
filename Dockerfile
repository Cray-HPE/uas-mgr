# Cray User Access Service Dockerfile
# Copyright 2019 Cray Inc. All Rights Reserved.

#########################
### Base
#########################
FROM dtr.dev.cray.com/baseos/alpine as base

# Install application dependencies
RUN apk update && apk add \
    g++ \
    gcc \
    libffi-dev \
    linux-headers \
    musl-dev \
    openssl-dev \
    python3 \
    python3-dev

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY setup.py requirements.txt .version /usr/src/app/
COPY api/ swagger_server/ /usr/src/app/swagger_server/

RUN pip3 install --no-cache-dir -r requirements.txt

#########################
### Coverage/Unit Tests
#########################
FROM base as coverage
COPY test-requirements.txt .coveragerc /usr/src/app/
RUN pip3 install --no-cache-dir -r test-requirements.txt
RUN ./swagger_server/test/version-check.sh
RUN mkdir -p /var/run/secrets/kubernetes.io/
COPY serviceaccount/ /var/run/secrets/kubernetes.io/serviceaccount/
ENTRYPOINT pytest --cov swagger_server --cov-fail-under 68

#########################
### API Tests
#########################
FROM base as testing
COPY api_test.sh api_test.sh
RUN apk update && apk add curl
ENTRYPOINT ["./api_test.sh"]

#########################
### Application
#########################
FROM base as application

EXPOSE 8088
ENTRYPOINT ["python3"]
CMD ["-m", "swagger_server"]
