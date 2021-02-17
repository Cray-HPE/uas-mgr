# Cray User Access Service Dockerfile
# MIT License
#
# (C) Copyright [2020] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

#########################
### Base
#########################
FROM dtr.dev.cray.com/baseos/alpine as base

# packages needed to run the app & install deps
ENV BASE_PACKAGES g++ gcc libffi-dev linux-headers musl-dev openssl-dev python3 python3-dev py3-pip

# packages needed to debug the application from inside the container
ENV DEBUG_PACKAGES procps iputils curl wget vim less

# Install application dependencies
RUN apk update && apk add $BASE_PACKAGES && apk add $DEBUG_PACKAGES

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip3 install --no-cache-dir \
                 --index-url http://dst.us.cray.com/dstpiprepo/simple \
                 --trusted-host dst.us.cray.com -r requirements.txt
#########################
### Coverage/Unit Tests
#########################
FROM base as coverage
COPY pylintrc test-requirements.txt .coveragerc /usr/src/app/
# Allow the use of either pypi or DST here because this is not part of the
# production delivered code, so it is less critical that everything be
# strictly Cray provided.
RUN pip3 install --no-cache-dir \
                 --extra-index https://pypi.org/simple \
                 --index-url http://dst.us.cray.com/dstpiprepo/simple \
                 --trusted-host dst.us.cray.com -r test-requirements.txt

# Copy the code into the container
COPY setup.py .version /usr/src/app/
COPY api/ swagger_server/ /usr/src/app/swagger_server/

# Install a test configuration
COPY swagger_server/test/cray-uas-mgr.yaml /etc/uas/

# Lint the code (need 100% clean here)
RUN pylint swagger_server

RUN ./swagger_server/test/version-check.sh
RUN mkdir -p /var/run/secrets/kubernetes.io/
COPY serviceaccount/ /var/run/secrets/kubernetes.io/serviceaccount/
ENV ETCD_MOCK_CLIENT yes
ENTRYPOINT pytest --cov swagger_server --cov-fail-under 75

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
