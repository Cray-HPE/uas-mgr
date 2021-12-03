# Copyright 2019-2021 Hewlett Packard Enterprise Development LP
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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# (MIT License)

# UNIT TESTS
UNIT_TEST_NAME ?= cray-uas-mgr-unit-test

# DOCKER
NAME ?= cray-uas-mgr
VERSION ?= $(shell cat .version)

# Chart
CHART_NAME ?= cray-uas-mgr
CHART_VERSION ?= $(shell cat .version)
CHART_PATH ?= kubernetes
HELM_UNITTEST_IMAGE ?= quintush/helm-unittest:3.3.0-0.2.5

unit_test: unit_test_image unit_test_run

chart: chart_setup chart_package chart_test

image:
	docker build --pull ${DOCKER_ARGS} --tag '${NAME}:${VERSION}' .

unit_test_image:
	docker build --pull ${DOCKER_ARGS} --tag '${UNIT_TEST_NAME}:${VERSION}'  --target coverage .

unit_test_run:
	docker run --rm '${UNIT_TEST_NAME}:${VERSION}'

unit_test_clean:
	docker rmi --force '${UNIT_TEST_NAME}:${VERSION}'

chart_setup:
	mkdir -p ${CHART_PATH}/.packaged
	grep -v -e 'global:' -e 'appVersion:' ${CHART_PATH}/${CHART_NAME}/values.yaml > /tmp/values.yaml-${VERSION}
	printf "\nglobal:\n  appVersion: ${VERSION}" >>  /tmp/values.yaml-${VERSION}
	cp /tmp/values.yaml-${VERSION} ${CHART_PATH}/${CHART_NAME}/values.yaml

chart_package:
	helm dep up ${CHART_PATH}/${CHART_NAME}
	helm package ${CHART_PATH}/${CHART_NAME} -d ${CHART_PATH}/.packaged --app-version ${VERSION} --version ${CHART_VERSION}

chart_test:
	helm lint "${CHART_PATH}/${CHART_NAME}"
	docker run --rm -v ${PWD}/${CHART_PATH}:/apps ${HELM_UNITTEST_IMAGE} -3 ${CHART_NAME}
