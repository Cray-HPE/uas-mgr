#!/bin/bash
#
# uas-common-lib.sh - UAS common functions
# Copyright 2019 Cray Inc. All Rights Reserved.

# Global variables
EXIT_CODE=0
FN_COMMON="uas-common-lib"
LOGIN_NODE=""
MAX_TRY=5
MOUNT_FILE="/proc/mounts"
TEST_CASE=0

# Test case header
function TEST_CASE_HEADER {
    ((TEST_CASE++))
    echo ""
    echo "#########################################################################################"
    echo "# Test case $TEST_CASE: $1"
    echo "#########################################################################################"
}

# Find WLM on the system
function FIND_WLM {
    # Verify that slurm pod is running on the system
    # check_pod_status is defined in /opt/cray/tests/ncn-resources/bin/
    check_pod_status slurm
    RC_SLURM_POD=$?

    # Verify that pbs pod is running on the system
    check_pod_status pbs
    RC_PBS_POD=$?
}

# SLURM smoke test
function SLURM_SMOKE_TEST {

    if [[ $1 == UAI ]]; then
        # Make sure that UAI is available.
        # If it is unavailable, skipping check.
        source need_uai

        LOGIN_NODE="$UAI"
    elif [[ $1 == UAN ]]; then
        LOGIN_NODE="$i_uan"
    else
        echo "WARNING: No argument supplied. Skipping check..."
        exit 123
    fi

    TEST_CASE_HEADER "Running SLURM smoke tests on $LOGIN_NODE"

    for ((try = 1; try <= $MAX_TRY; try++))
    do
        # Test sinfo to make sure that compute nodes are up running and idle state
        echo "ssh $LOGIN_NODE sinfo -r -l --states=idle | grep up"
        ssh $LOGIN_NODE sinfo -r -l --states=idle | grep up
        if [[ $? == 0 ]]; then
            echo "Try: $try"
            echo "SUCCESS: [$FN_COMMON] sinfo works well."
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

    if [[ $1 == UAI ]]; then
        # Make sure that UAI is available.
        # If it is unavailable, skipping check.
        source need_uai

        LOGIN_NODE="$UAI"
    elif [[ $1 == UAN ]]; then
        LOGIN_NODE="$i_uan"
    else
        echo "WARNING: No argument supplied. Skipping check..."
        exit 123
    fi

    TEST_CASE_HEADER "Running PBS smoke tests on $LOGIN_NODE"

    for ((try = 1; try <= $MAX_TRY; try++))
    do
        # Test qstat
        echo "ssh $LOGIN_NODE qstat -B | grep -i Active"
        ssh $LOGIN_NODE qstat -B | grep -i Active
        if [[ $? == 0 ]]; then
            echo "Try: $try"
            echo "SUCCESS: [$FN_COMMON] qstat works well."
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
        echo "SUCCESS: [$FN_COMMON] HSN and Compute nodes are available on the system:"
        echo "$nid_list"
    else
        echo "FAIL: [$FN_COMMON] HSN and Compute nodes are not available on the system."
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

# Get WLM version
function GET_WLM_VERSION {
    TEST_CASE_HEADER "Test WLM version"

    WLM_Version=$(rpm -qa | egrep -i "$1")
    if [[ $? == 0 ]]; then
        echo "SUCCESS: $1 version, $WLM_Version"
    else
        echo "FAIL: Cannot get $1 version."
        exit 1
    fi
}

# SLURM functional test
function SLURM_FUNCTIONAL_TEST {

    # First argument is for UAN/UAI
    if [[ $1 == UAI ]]; then
        # Make sure that UAI is available.
        # If it is unavailable, skipping check.
        source need_uai

        LOGIN_NODE="$UAI"
    elif [[ $1 == UAN ]]; then
        LOGIN_NODE="$i_uan"
    else
        echo "WARNING: No first argument, UAN/UAI, supplied. Skipping check..."
        exit 123
    fi

    if [[ -n $SHARED_FS ]] ; then
        cd $SHARED_FS
    else
        echo "WARNING: An environment variable, SHARED_FS, is not set. Skipping check..."
        exit 123
    fi

    # Second argument is for testing SLURM commands
    if [[ $2 != "" ]]; then
        TEST_CASE_HEADER "Test $2 on $LOGIN_NODE"
        CMD="$2"
        echo "ssh $LOGIN_NODE $CMD"
        ssh $LOGIN_NODE $CMD
        if [[ $? == 0 ]]; then
            echo "SUCCESS: [$FN_COMMON] $CMD works well on $LOGIN_NODE."
        else
            echo "FAIL: [$FN_COMMON] $CMD doesn't work on $LOGIN_NODE." >> $RESULT_TEST
            EXIT_CODE=1
        fi
    else
        echo "WARNING: No second argument, SLURM commands, supplied. Skipping check..."
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
