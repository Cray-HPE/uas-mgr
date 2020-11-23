#!/bin/bash

#
# Copyright 2020 Hewlett Packard Enterprise Development LP#
#
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
    if [ -n "${OUT}" ]; then
        rm -f ${OUT}
    fi
}
OUT=""
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

TAG="cray/cray-uas-mgr:latest"
OUT=$(mktemp)

echo "Building image..."
##########
# BUILD  #
##########
docker build -t $TAG . 2>&1 | tee ${OUT}
if [ $? -ne 0 ]; then
  echo "Docker build failed"
  rm ${OUT}
  exit 1
fi

echo "Running tests..."
##########
#  TEST  #
##########
# Use the FROM layer after the one we are interesting in 
# for a more deterministic pattern to match with "-B1"
test_layer=$(grep -B1 "FROM base as application" $OUT | head -1 | awk '{print $2}')
coverage_layer=$(grep -B1 "FROM base as testing" $OUT | head -1 | awk '{print $2}')
docker run $test_layer
if [ $? -ne 0 ]; then
  echo "Docker test_layer $test_layer failed"
  exit 1
fi

echo "Checking test coverage..."
docker run $coverage_layer
if [ $? -ne 0 ]; then
    echo "Docker coverage_layer $coverage_layer failed"
    exit 1
fi

echo "'$TAG' is created successfully"
exit 0
