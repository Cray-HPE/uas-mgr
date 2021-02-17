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
exit 0
ssh $TARGET kubectl delete pod -l app=cray-uas-mgr

exit 0
