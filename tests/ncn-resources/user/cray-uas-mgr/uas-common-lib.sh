#!/bin/bash
#
# uas-common-lib.sh - UAS common functions
# Copyright 2019 Cray Inc. All Rights Reserved.

# Global variables
FN_COMMON="uas-common-lib"
exit_code=0

# Find list of compute nodes
function GET_NID_LIST {
    # get_node is defined in /opt/cray/tests/ncn-resources/bin
    nid_list=$(get_node --all | awk '{print $1}')
    echo "Running get_node tool"
    get_node
    if [[ $? == 0 ]]; then
        echo "SUCCESS: [$FN_COMMON] Compute nodes are available on the system:"
        echo "$nid_list"
    else
        echo "FAIL: [$FN_COMMON] Compute nodes are not available on the system."
        exit 1
    fi
}

# Test case header
function TEST_CASE_HEADER {
    ((TEST_CASE++))
    echo ""
    echo "#######################################################################"
    echo "# Test case $TEST_CASE: $1"
    echo "#######################################################################"
}

# Check that UAN is available on a system
function IS_UAN_AVAILABLE {
    # See if Role="Application" for UAN is in the Node Map
    cray hsm Defaults NodeMaps list | grep Application
    if [[ $? == 0 ]]; then
        echo "SUCCESS: [$FN_COMMON] Role=Application for UAN is in the Node Map"
    else
        echo "FAIL: [$FN_COMMON] Role=Application for UAN is not in the Node Map. Skipping check..."
        echo "[$FN_COMMON] After an automated installation of UAN is done, we need to change exit 123 to exit 1"
        exit 123
    fi

    # Get ID for UAN
    ID_UANs=$(cray hsm Defaults NodeMaps list | grep ID | grep -v NID | awk '{print $3}' | sed 's/"//g')

    if [[ -n $ID_UANs ]]; then
        echo "#################################################"
        echo "ID for nodes: $ID_UANs"
        echo "#################################################"
    else
        echo "FAIL: [$FN_COMMON] No IDs are available on a system"
        exit 1
    fi

    # Run cray hsm Inventory Hardware describe ID
    for id in $ID_UANs
    do
        echo ""
        echo "#################################################"
        echo "cray hsm Inventory Hardware describe $id"
        echo "#################################################"
        cray hsm Inventory Hardware describe $id
        if [[ $? == 0 ]]; then
            echo "SUCCESS: [$FN_COMMON] UAN is installed on a system."
        else
            echo "FAIL: [$FN_COMMON] UAN is not installed on a system. Skipping check..."
            echo "[$FN_COMMON] After an automated installation of UAN is done, we need to change exit 123 to exit 1"
            exit 123
        fi
    done

    # Get list of UANs
    if [[ -f /etc/ansible/hosts/uan ]]; then
        List_UANs=$(cat /etc/ansible/hosts/uan | grep -v "\[" | grep -v "#")
        if [[ -n $List_UANs ]]; then
            echo "[$FN_COMMON] List of UANs: $List_UANs"
        else
            echo "FAIL: [$FN_COMMON] No UANs on a system"
            exit 1
        fi
    else
        echo "FAIL: [$FN_COMMON] /etc/ansible/hosts/uan doesn't exit"
        exit 1
    fi
}

# Check a final result
function CHECK_FINAL_RESULT {
    if [[ -n $RESULT_TEST ]]; then
        echo ""
        grep FAIL $RESULT_TEST
        if [[ $? == 0 ]]; then
            exit_code=1
        fi
    else
        echo "WARNING: A result file doesn't exist. Skipping check..."
        exit_code=123
    fi

    echo ""
    echo -n "exit_code: $exit_code - "
    if [[ $exit_code == 0 ]]; then
        echo "SUCCESS: All test cases passed"
    else
        echo "FAIL: At least one of test cases failed"
    fi

    exit $exit_code
}
