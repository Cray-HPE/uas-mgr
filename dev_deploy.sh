#!/bin/bash

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

: ${TAG:="cray/cray-uas-mgr:latest"}

usage() {
    (
        echo "usage: local_deploy [-t tag]"
        echo ""
        echo "Where:"
        echo "    -t - the tag to apply to your new image"
    ) >&2
    exit 1
}

cleanup() {
    if [ -n "${COVGTAG}" ]; then
        docker rmi --force ${COVGTAG} && true
    fi
    if [ -n "${TESTTAG}" ]; then
        docker rmi --force ${TESTTAG} && true
    fi
}
PUSH=no

trap cleanup EXIT

args=`getopt 't:' $*`
# you should not use `getopt abo: "$@"` since that would parse
# the arguments differently from what the set command below does.
if [ $? != 0 ]; then
    usage
fi

set -- $args
# You cannot use the set command with a backquoted getopt directly,
# since the exit code from getopt would be shadowed by those of set,
# which is zero by definition.
for i; do
    case "$i" in
        -t)
            TAG="$2"; shift
            shift;;
        --)
            shift
            break;;
    esac
done
NAME=$(echo ${TAG} | sed -e 's/:.*$//')
VERS=$(echo ${TAG} | sed -e 's/^.*:/:/')

echo "Building coverage image..."
# Build a coverage image to check test coverage
COVGTAG=${NAME}-coverage${VERS}
docker build --progress plain -t ${COVGTAG} --target coverage .
if [ $? -ne 0 ]; then
  echo "Docker build of coverage image failed"
  exit 1
fi

echo "Running unit tests and checking coverage"
docker run ${COVGTAG}
if [ $? -ne 0 ]; then
    echo "Docker coverage check ${COVGTAG} failed"
    exit 1
fi

echo "Building API test image..."
# Build an API Test image to check basic API response
TESTTAG=${NAME}-api-test${VERS}
docker build --progress plain -t ${TESTTAG} --target testing .
if [ $? -ne 0 ]; then
  echo "Docker build of API test image failed"
  exit 1
fi

echo "Running API test"
docker run ${TESTTAG}
if [ $? -ne 0 ]; then
    echo "Docker API test check ${TESTTAG} failed"
    exit 1
fi

echo "Building final image..."
# Build the final product image
docker build --progress plain -t ${TAG} .
if [ $? -ne 0 ]; then
  echo "Docker build of final image failed"
  exit 1
fi

echo "'$TAG' is created successfully"
exit 0
