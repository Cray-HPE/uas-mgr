#!/bin/bash
#
# uas-common-lib.sh - UAS common functions
# Copyright 2019 Cray Inc. All Rights Reserved.

# Global variables
FN_COMMON="uas-common-lib"
EXIT_CODE=0
TEST_CASE=0
MAX_TRY=5

# Test case header
function TEST_CASE_HEADER {
    ((TEST_CASE++))
    echo ""
    echo "#########################################################################################"
    echo "# Test case $TEST_CASE: $1"
    echo "#########################################################################################"
}

# SLURM smoke test
function SLURM_SMOKE_TEST {
    TEST_CASE_HEADER "Running SLURM smoke tests"

    # Make sure that UAI is available.
    # If it is unavailable, skipping check.
    source need_uai

    for ((try = 1; try <= $MAX_TRY; try++))
    do
        echo "ssh $UAI sinfo -r -l --states=idle | grep up"
        ssh $UAI sinfo -r -l --states=idle | grep up
        # Test sinfo to make sure that compute nodes are up running and idle state
        echo "ssh $UAI sinfo -r -l --states=idle | grep up"
        ssh $UAI sinfo -r -l --states=idle | grep up
        if [[ $? == 0 ]]; then
            echo "Try: $try"
            echo "PASS: [$FN_COMMON] sinfo works well."
            break;
        fi
    done

    if ((try > MAX_TRY))
    then
        echo "Try: $try"
        echo "FAIL: [$FN_COMMON] sinfo doesn't work."
        exit 1
    fi
}

# PBS smoke test
function PBS_SMOKE_TEST {
    TEST_CASE_HEADER "Running PBS smoke tests"

    # Make sure that UAI is available.
    # If it is unavailable, skipping check.
    source need_uai

    for ((try = 1; try <= $MAX_TRY; try++))
    do
        # Test qstat
        echo "ssh $UAI qstat -B | grep -i Active"
        ssh $UAI qstat -B | grep -i Active
        if [[ $? == 0 ]]; then
            echo "Try: $try"
            echo "PASS: [$FN_COMMON] qstat works well."
            break;
        fi
    done

    if ((try > MAX_TRY))
    then
        echo "Try: $try"
        echo "FAIL: [$FN_COMMON] qstat doesn't work."
        exit 1
    fi
}

# Find list of compute nodes
function GET_NID_LIST {
    TEST_CASE_HEADER "Verify that compute nodes are available on the system"
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

# Check that UAN is available on the system
function IS_UAN_AVAILABLE {
    TEST_CASE_HEADER "Verify that UAN is available on the system"
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

# Check that a default UAS image is SLURM/PBS
function CHECK_DEFAULT_UAS_IMAGE {
    TEST_CASE_HEADER "Check that a default UAS image is $1"
    OUT_DEFAULT_UAS_IMAGES=$(cray uas images list | grep default)
    cray uas images list | grep default | grep -i $1
    if [[ $? == 0 ]]; then
        echo "SUCCESS: A default UAS image is $1"
    else
        echo "FAIL: $OUT_DEFAULT_UAS_IMAGES. It is not $1. Skipping check..."
        exit 123
    fi
}

# Check a final result
function CHECK_FINAL_RESULT {
    if [[ -n $RESULT_TEST ]]; then
        echo ""
        grep FAIL $RESULT_TEST
        if [[ $? == 0 ]]; then
            EXIT_CODE=1
        fi
    else
        echo "WARNING: A result file doesn't exist. Skipping check..."
        EXIT_CODE=123
    fi

    echo ""
    echo -n "EXIT_CODE: $EXIT_CODE - "
    if [[ $EXIT_CODE == 0 ]]; then
        echo "SUCCESS: All test cases passed"
    elif [[ $EXIT_CODE == 123 ]]; then
        echo "Skipping check due to known issues."
    else
        echo "FAIL: At least one of test cases failed"
    fi

    exit $EXIT_CODE
}
