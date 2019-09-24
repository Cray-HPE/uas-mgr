#!/bin/bash

# wlm-diagnostics.sh - WLM Health Check
# Copyright 2019 Cray Inc. All Rights Reserved.

echo ""
echo "##################################################"
echo "# Test Case 1: Checking that DNS pods are running "
echo "##################################################"
# check_pod_status is defined in /opt/cray/tests/sms-resources/bin
check_pod_status coredns
if [[ $? == 0 ]]; then
    echo "SUCCESS: Verify that DNS pods are running on a system."
    echo ""
    LIST_COREDNS_PODS=$(kubectl -n kube-system get pods -o wide | grep coredns | awk '{print $1}')
    if [[ -n $LIST_COREDNS_PODS ]]; then
        echo "List of coredns pods: $LIST_COREDNS_PODS"
    else
        echo "List of coredns pods is empty. Skipping check..."
        exit 123
    fi
else
    echo "FAIL: DNS pods are not running on a system. So, WLM will not run."
    exit 1
fi

echo ""
echo "###################################"
echo "# Test Case 2: Checking DNS health "
echo "###################################"

for dns_pod in $LIST_COREDNS_PODS
do
    echo "kubectl logs -n kube-system $dns_pod | grep -i error"
    OUT_DNS_ERROR=$(kubectl logs -n kube-system $dns_pod | grep -i error)
    if [[ $? == 0 ]]; then
        echo "A log output of DNS pod, $dns_pod, is:"
        echo "$OUT_DNS_ERROR"
        echo "" 
        echo "FAIL: DNS pod, $dns_pod, has errors. So, WLM will not run."
        exit 1
    else
        echo "SUCCESS: DNS pod doesn't have an error to run WLM"
    fi
done

echo ""
echo "#############################################################"
echo "# Test Case 3: Checking that metallb-system pods are running "
echo "#############################################################"
check_pod_status metallb-system
if [[ $? == 0 ]]; then
    echo "SUCCESS: metallb-system pods are running."
else
    echo "FAIL: metallb-system pods are not running. So, WLM will not run."
    exit 1
fi

echo ""
echo "############################################################"
echo "# Test Case 4: Verify that all compute nodes are up running "
echo "############################################################"
# Find list of compute nodes
nid_list=$(grep nid.*.local /etc/hosts | grep -v nmn | grep -v bmc | awk '{print $3}')

if [[ -n $nid_list ]]; then
    echo "List of compute nodes: $nid_list"

    for CN in $nid_list
    do
        echo "ping -c 1 $CN"
        OUT_PING=$(ping -c 1 $CN)
        if [[ $? == 0 ]]; then
            echo "SUCCESS: HSN works well on $CN."
        else
            echo "ping -c 1 $CN returns $OUT_PING"
            echo "FAIL: Cannot run WLM due to HSN issue on $CN."
            exit 1
        fi
    done
else
    echo "FAIL: No compute nodes are available on a system to use WLM."
    exit 1
fi

