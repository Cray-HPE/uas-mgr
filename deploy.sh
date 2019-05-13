#!/bin/bash

set -x

TAG="dtr.dev.cray.com/$USER/cray-uas-mgr:latest"
TARGET="sms-1.craydev.com"
POD='cray-uas-mgr'
OUT=$(mktemp)

##########
# BUILD  #
##########
docker build -t $TAG . | tee $OUT
if [ $? -ne 0 ]; then
  echo "Docker build failed"
  rm $OUT
  exit 1
fi

##########
#  TEST  #
##########
# Use the FROM layer after the one we are interesting in 
# for a more deterministic pattern to match with "-B1"
test_layer=$(grep -B1 "FROM base as application" $OUT | head -1 | awk '{print $2}')
coverage_layer=$(grep -B1 "FROM base as testing" $OUT | head -1 | awk '{print $2}')
rm $OUT
docker run $test_layer
if [ $? -ne 0 ]; then
  echo "Docker test_layer $test_layer failed"
  exit 1
fi

docker run $coverage_layer
if [ $? -ne 0 ]; then
  echo "Docker coverage_layer $coverage_layer failed"
  exit 1
fi

##########
# DEPLOY #
##########
docker push $TAG
ssh $TARGET kubectl delete pod -l app=cray-uas-mgr

exit 0
