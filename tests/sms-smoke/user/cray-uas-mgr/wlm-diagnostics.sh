#!/bin/bash

# wlm-diagnostics.sh - WLM Health Check
# Copyright 2019 Cray Inc. All Rights Reserved.

HSN_COMPUTE_NODE=NO

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

echo "WLM diagnostics test" >> $RESULT_TEST
echo "" >> $RESULT_TEST

TEST_CASE_HEADER "Checking that DNS pods are running"
# check_pod_status is defined in /opt/cray/tests/sms-resources/bin
check_pod_status coredns
if [[ $? == 0 ]]; then
    echo "SUCCESS: Verify that DNS pods are running on the system."
    echo ""
    LIST_COREDNS_PODS=$(kubectl -n kube-system get pods -o wide | grep coredns | awk '{print $1}')
    if [[ -n $LIST_COREDNS_PODS ]]; then
        echo "List of coredns pods: $LIST_COREDNS_PODS"
    else
        echo "List of coredns pods is empty. Skipping check..."
        exit 123
    fi
else
    echo "FAIL: DNS pods are not running on the system. So, WLM will not run."
    exit 1
fi

TEST_CASE_HEADER "Checking DNS health"

for dns_pod in $LIST_COREDNS_PODS
do
    echo "kubectl logs -n kube-system $dns_pod | grep -i error"
    OUT_DNS_ERROR=$(kubectl logs -n kube-system $dns_pod | grep -i error)
    if [[ $? == 0 ]]; then
        echo "A log output of DNS pod, $dns_pod, is:"
        echo "$OUT_DNS_ERROR"
        echo "" 
        echo "WARNING: DNS pod, $dns_pod, has errors. So, WLM might not run as expected."
    else
        echo "SUCCESS: DNS pod doesn't have an error to run WLM"
    fi
done

TEST_CASE_HEADER "Checking that metallb-system pods are running"
check_pod_status metallb-system
if [[ $? == 0 ]]; then
    echo "SUCCESS: metallb-system pods are running."
else
    echo "FAIL: metallb-system pods are not running. So, WLM will not run."
    exit 1
fi

# Call function, GET_NID_LIST, from $RESOURCES/user/cray-uas-mgr/uan-common-lib.sh
GET_NID_LIST

# nid_list is defined in $RESOURCES/user/cray-uas-mgr/uan-common-lib.sh
if [[ -n $nid_list ]]; then
    echo "List of compute nodes: $nid_list"

    for CN in $nid_list
    do
        echo "ping -c 1 $CN"
        OUT_PING=$(ping -c 1 $CN)
        if [[ $? == 0 ]]; then
            echo "SUCCESS: HSN works well on $CN."
            HSN_COMPUTE_NODE=YES
        else
            echo "ping -c 1 $CN returns $OUT_PING"
            echo "WARNING: Cannot run WLM due to HSN issue on $CN."
        fi
    done
else
    echo "FAIL: No compute nodes are available on the system to use WLM."
    exit 1
fi

if [[ $HSN_COMPUTE_NODE == YES ]]; then
    echo ""
    echo "SUCCESS: HSN works on at least one of compute nodes."
else
    echo ""
    echo "FAIL: HSN doesn't work on all compute nodes"
    exit 1
fi

TEST_CASE_HEADER "Verify that at least one of WLM pods is running on the system"
# Check that WLM is running on the system
FIND_WLM

if [[ $RC_SLURM_POD == 0 && $RC_PBS_POD == 0 ]]; then
    echo "SUCCESS: Both SLURM and PBS pods are running on the system."

    # Test WLM version
    GET_WLM_VERSION "SLURM|PBS"

    # Get a default UAS image
    GET_DEFAULT_UAS_IMAGE
    if [[ $DEFAULT_UAS_IMAGE == SLURM ]]; then
        # SLURM smoke test
        # It is defined in $RESOURCES/user/cray-uas-mgr/uas-common-lib.sh
        SLURM_SMOKE_TEST UAI
    fi

    if [[ $DEFAULT_UAS_IMAGE == PBS ]]; then
        # PBS smoke test
        # It is defined in $RESOURCES/user/cray-uas-mgr/uas-common-lib.sh
        PBS_SMOKE_TEST UAI
    fi

elif [[ $RC_SLURM_POD == 0 ]]; then
    echo "SUCCESS: SLURM pod is running on the system"

    # Test SLURM version
    GET_WLM_VERSION SLURM

    # Check that a default UAS image is SLURM
    CHECK_DEFAULT_UAS_IMAGE SLURM

    # SLURM smoke test
    # It is defined in $RESOURCES/user/cray-uas-mgr/uas-common-lib.sh
    SLURM_SMOKE_TEST UAI

elif [[ $RC_PBS_POD == 0 ]]; then
    echo "SUCCESS: PBS pod is running on the system"

    # Test PBS vesion
    GET_WLM_VERSION PBS

    # Check that a default UAS image is PBS
    CHECK_DEFAULT_UAS_IMAGE PBS

    # PBS smoke test
    # It is defined in $RESOURCES/user/cray-uas-mgr/uas-common-lib.sh
    PBS_SMOKE_TEST UAI

else
    echo "FAIL: No WLM pod is running on the system."
    exit 1
fi

# Check a final result
CHECK_FINAL_RESULT
