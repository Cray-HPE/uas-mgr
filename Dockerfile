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

COPY requirements.txt /usr/src/app/
#
# PR REVIEWERS!!!!  IF THIS COMMENT IS STILL HERE POINT IT OUT!!!!
#
# Temporarily use both the DST trusted repos pip index AND pypi
# to find packages.  This should ONLY use the DST repos when this
# comment is removed.  Being worked now by DST as DST-5496.
#
RUN pip3 install --no-cache-dir \
                 --extra-index https://pypi.org/simple \
                 --index-url http://dst.us.cray.com/dstpiprepo/simple \
                 --trusted-host dst.us.cray.com -r requirements.txt

#########################
### Coverage/Unit Tests
#########################
FROM base as coverage
COPY test-requirements.txt .coveragerc /usr/src/app/
#
# PR REVIEWERS!!!!  IF THIS COMMENT IS STILL HERE POINT IT OUT!!!!
#
# Temporarily use both the DST trusted repos pip index AND pypi
# to find packages.  This should ONLY use the DST repos when this
# comment is removed.  Being worked now by DST as DST-5496.
#
RUN pip3 install --no-cache-dir \
                 --extra-index https://pypi.org/simple \
                 --index-url http://dst.us.cray.com/dstpiprepo/simple \
                 --trusted-host dst.us.cray.com -r test-requirements.txt

# Copy the code into the container
COPY setup.py .version /usr/src/app/
COPY api/ swagger_server/ /usr/src/app/swagger_server/

RUN ./swagger_server/test/version-check.sh
RUN mkdir -p /var/run/secrets/kubernetes.io/
COPY serviceaccount/ /var/run/secrets/kubernetes.io/serviceaccount/
ENTRYPOINT pytest --cov swagger_server --cov-fail-under 67

#########################
### API Tests
#########################
FROM base as testing

# Copy the code into the container
COPY setup.py .version /usr/src/app/
COPY api/ swagger_server/ /usr/src/app/swagger_server/
COPY api_test.sh api_test.sh

ENTRYPOINT ["./api_test.sh"]

#########################
### Application
#########################
FROM base as application

# Copy the code into the container
COPY setup.py .version /usr/src/app/
COPY api/ swagger_server/ /usr/src/app/swagger_server/

EXPOSE 8088
ENTRYPOINT ["python3"]
CMD ["-m", "swagger_server"]
