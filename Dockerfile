# Cray User Access Service Dockerfile
# Copyright 2019 Cray Inc. All Rights Reserved.

#########################
### Base
#########################
FROM dtr.dev.cray.com/baseos/alpine as base

# packages needed to run the app & install deps
ENV BASE_PACKAGES g++ gcc libffi-dev linux-headers musl-dev openssl-dev python3 python3-dev

# packages needed to debug the application from inside the container
ENV DEBUG_PACKAGES procps iputils curl wget vim less

# Install application dependencies
RUN apk update && apk add $BASE_PACKAGES && apk add $DEBUG_PACKAGES

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
ENTRYPOINT pytest --cov swagger_server --cov-fail-under 67

#########################
### API Tests
#########################
FROM base as testing
COPY api_test.sh api_test.sh
ENTRYPOINT ["./api_test.sh"]

#########################
### Application
#########################
FROM base as application

EXPOSE 8088
ENTRYPOINT ["python3"]
CMD ["-m", "swagger_server"]
