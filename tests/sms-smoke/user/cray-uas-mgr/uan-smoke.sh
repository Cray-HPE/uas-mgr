#!/bin/bash

# uan-smoke.sh - UAN Smoke
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

RESULT_TEST="$PWD/output_${@}$$.txt"
touch $RESULT_TEST

echo "UAN Smoke test" >> $RESULT_TEST
echo "" >> $RESULT_TEST

# Check that UAN is available on a system
# Function IS_UAN_AVAILABLE is defined in $RESOURCES/user/cray-uas-mgr/uas-common-lib.sh
IS_UAN_AVAILABLE

# Verify that ssh UAN works well
for i_uan in $List_UANs
do
    TEST_CASE_HEADER "Verify that ssh UAN cat /etc/motd works well"
    ssh $i_uan cat /etc/motd
    if [[ $? == 0 ]]; then
        echo "SUCCESS: ssh $i_uan cat /etc/motd works well"
    else
        echo "FAIL: ssh $i_uan cat /etc/motd doesn't work." >> $RESULT_TEST
        EXIT_CODE=1
    fi

    TEST_CASE_HEADER "Verify that PE is installed on UAN"
    ssh $i_uan module list
    if [[ $? == 0 ]]; then
        echo "SUCCESS: PE is installed on $i_uan"
    else
        echo "FAIL: PE is not installed on $i_uan" >> $RESULT_TEST
        EXIT_CODE=1
    fi

    TEST_CASE_HEADER "Verify that ping outside of cray network works well on $i_uan"
    ssh $i_uan ping -c 1 www.hpe.com
    if [[ $? == 0 ]]; then
        echo "SUCCESS: ping outside of cray network works well on $i_uan"
    else
        echo "FAIL: Cannot ping outside of cray network on $i_uan" >> $RESULT_TEST
        EXIT_CODE=1
    fi

    TEST_CASE_HEADER "Verify that man pages work for standard Linux/Unix commands on $i_uan"
    ssh $i_uan man ls > /dev/null 2>&1
    if [[ $? == 0 ]]; then
        echo "SUCCESS: man page work for standard Linux/Unix commands on $i_uan"
    else
        echo "WARNING: man page does not work for standard Linux/Unix commands on $i_uan. It is due to a known bug, SKERN-2206. Skipping check..."
        EXIT_CODE=123
    fi
done

# Check a final result
# Function CHECK_FINAL_RESULT is defined in $RESOURCES/user/cray-uas-mgr/uas-common-lib.sh
CHECK_FINAL_RESULT
