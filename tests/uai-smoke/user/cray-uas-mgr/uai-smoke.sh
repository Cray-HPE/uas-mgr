#!/bin/bash

# uai-smoke.sh - UAI Smoke
# Copyright 2019 Cray Inc. All Rights Reserved.

API_GATEWAY="api-gw-service-nmn.local"

echo "###################################################################"
echo "# Test Case 1: Verify that the api gateway is accessible from a UAI"
echo "###################################################################"
echo ""
ping -c1 $API_GATEWAY
if [[ $? == 0 ]]; then
    echo ""
    echo "SUCCESS: The api gateway, $API_GATEWAY, is accessible from a UAI."
else
    echo ""
    echo "FAIL: The api gateway, $API_GATEWAY, is not accessible from a UAI."
    exit 1
fi

echo "###################################################"
echo "# Test Case 2: Verify that PE is installed on a UAI"
echo "###################################################"
echo ""
module list
if [[ $? == 0 ]]; then
    echo ""
    echo "SUCCESS: PE is installed on a UAI."
else
    echo ""
    echo "FAIL: PE is not installed on a UAI."
    exit 1
fi

exit 0

