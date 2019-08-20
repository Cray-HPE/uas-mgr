#!/bin/bash

# uas-smoke.sh - UAS Manager Smoke
# Copyright 2019 Cray Inc. All Rights Reserved.

set -x
set -e

# Test cray-uas-mgr pod
# check_pod_status is defined at /opt/cray/tests/sms-resources/bin/
check_pod_status cray-uas-mgr
if [[ $? == 0 ]]; then
    echo "PASS: Verify that cray-uas-mgr pod exists on a system"
else
    echo "FAIL: cray-uas-mgr pod doesn't exist on a system."
    exit 1
fi

# Set a temp directory for the craycli config
# and auth token
export CRAY_CONFIG_DIR=$(mktemp -d)

cray init --hostname https://api-gw-service-nmn.local --no-auth
cray auth login --username uastest --password uastestpwd

cray uas mgr-info list

cray uas images list

cray uas uais list

rm -r $CRAY_CONFIG_DIR

exit 0
