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
#
# uas-smoke.sh - UAS Manager Smoke

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
