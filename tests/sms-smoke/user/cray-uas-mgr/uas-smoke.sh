#!/bin/bash

# uas-smoke.sh - UAS Manager Smoke
# Copyright 2019 Cray Inc. All Rights Reserved.

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

# Authorize CLI with /opt/cray/tests/ncn-resources/bin/auth_craycli
auth_craycli

cray uas mgr-info list

cray uas images list

cray uas uais list

cray uas admin config images list

cray uas admin config volumes list

echo "INFO: kubectl describe -n services cm/cray-uas-mgr-cfgmap"
kubectl describe -n services cm/cray-uas-mgr-cfgmap

exit 0
