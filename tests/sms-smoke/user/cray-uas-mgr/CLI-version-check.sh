#!/bin/bash
#
# Check for Cray CLI version matches - from DST-3133 issue
# Copyright 2019 Cray Inc. All Rights Reserved.

# CRAY CLI version on SMS node
SMS_CRAY_CLI_VER=$(cray --version)
if [ -z "${SMS_CRAY_CLI_VER}" ]; then
    echo "Fail: Unable to check CRAY CLI version on SMS"
    exit 1
fi

# Make sure that UAI is available.
# If it is unavailable, skipping check. 
source need_uai

# CRAY CLI verson on UAI 
UAI_CRAY_CLI_VER=$(ssh $UAI cray --version)
if [ -z "${UAI_CRAY_CLI_VER}" ]; then
    echo "Fail: Unable to check CRAY CLI version on UAI"
    exit 1
else
    # Verify that CRAY CLI versions on SMS node and UAI match
    DIFF=$(diff -u <(echo "${SMS_CRAY_CLI_VER}") <(echo "${UAI_CRAY_CLI_VER}"))
    if [ $? -eq 0 ]; then
        echo "CRAY CLI versions on SMS node and UAI match (${SMS_CRAY_CLI_VER})"
        exit 0
    else
        echo "CRAY CLI versions on SMS node do NOT match, diff follows:"
        echo "${DIFF}"
        echo "TO-DO: After DST-3133 is fixed, change exit 123 to exit 1"
        exit 123
    fi
fi
