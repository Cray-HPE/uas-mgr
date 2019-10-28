#!/bin/bash

# uas-smoke.sh - UAS Manager Smoke
# Copyright 2019 Cray Inc. All Rights Reserved.

# UAS common functions to test
# $RESOURCES is set to /opt/cray/tests/ncn-resources
if [[ -f $RESOURCES/user/cray-uas-mgr/uas-common-lib.sh ]]; then
    echo "source $RESOURCES/user/cray-uas-mgr/uas-common-lib.sh"
    source $RESOURCES/user/cray-uas-mgr/uas-common-lib.sh
else
    echo "FAIL: Cannot find uas-common-lib.sh. Skipping check..."
    exit 123
fi

set -x
set -e

# Test cray-uas-mgr pod
# check_pod_status is defined at /opt/cray/tests/sms-resources/bin/
check_pod_status cray-uas-mgr
if [[ $? == 0 ]]; then
    echo "SUCCESS: Verify that cray-uas-mgr pod exists on a system"
else
    echo "FAIL: cray-uas-mgr pod doesn't exist on a system."
    exit 1
fi

# Test uas-mgr version
OUT_UAS_MGR_VER=$(rpm -q cray-uas-mgr-crayctldeploy)
if [[ $? == 0 ]]; then
    echo "SUCCESS: Get uas-mgr version, $OUT_UAS_MGR_VER"
else
    echo "FAIL: Cannot get uas-mgr version"
    echo "$OUT_UAS_MGR_VER"
    exit 1
fi

# Set a temp directory for the craycli config
# and auth token
export CRAY_CONFIG_DIR=$(mktemp -d)

cray init --hostname https://api-gw-service-nmn.local --no-auth
cray auth login --username $COMMON_USER_NAME --password $COMMON_USER_PW

cray uas mgr-info list

cray uas images list

cray uas uais list

rm -r $CRAY_CONFIG_DIR

exit 0
