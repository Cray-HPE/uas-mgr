#!/bin/bash

# uai-diagnostics.sh - UAI Health Check
# Copyright 2019 Cray Inc. All Rights Reserved.

# This script is designed to test whether launched UAIs
# will be healthy by checking common issues that prevent
# UAIs from launching or from being reachable. Failures
# in this script generally indicate an issue in localization,
# networking, or post-install config. They may not be indicative
# of a UAS service issue.

set -e

error() {
    echo "UAI Diagnostics check failed on line $1"
    rm -rf $CRAY_CONFIG_DIR
}

trap 'error $LINENO' ERR

echo "Checking for uas_ip in Config Map"
kubectl describe cm -n services cray-uas-mgr-cfgmap | grep ^uas_ip
echo "... OK"

echo "Checking that uas_ip is pingable"
UAS_IP=$(kubectl describe cm -n services cray-uas-mgr-cfgmap | grep ^uas_ip | awk '{ print $2 }')
ping -c3 ${UAS_IP}
echo "... OK"

echo "Checking that default image is set"
# Authorize CLI with /opt/cray/tests/ncn-resources/bin/auth_craycli
auth_craycli
DEFAULT_IMAGE=$(cray uas images list | grep ^default_image | awk '{ print $3 }' | sed 's/"//g')
if [ -z "$DEFAULT_IMAGE" ]; then
    echo "No default image found in images list output"
    exit 1
fi
echo "... OK"

echo "Get a list of all non-master nodes"
NODES=$(kubectl get node --selector='!node-role.kubernetes.io/master' -o jsonpath='{.items[*].metadata.name}')

echo "Paths that are not present are treated as warnings"
HOSTFS=$(kubectl describe cm -n services cray-uas-mgr-cfgmap | grep host_path | grep -v ^# | awk '{ print $3 }')
for NODE in $NODES
do
    echo "Checking filesystems on $NODE"
    for FS in ${HOSTFS}
    do
        echo "Looking for ${FS} on $NODE"
        ssh $NODE "ls ${FS} | true"
    done
    echo "... OK"
done

echo "Checking that the ${DEFAULT_IMAGE} is available on all nodes"
for NODE in $NODES
do
    echo "Checking for Docker image ${DEFAULT_IMAGE} on $NODE"
    ssh $NODE "crictl pull ${DEFAULT_IMAGE}"
    echo "... OK"
done

echo "Checking that the macvlan interface is available and online"
for NODE in $NODES
do
    echo "Checking that the mac0 interface on $NODE exists"
    OUT=`ssh $NODE "ip a show mac0 up"`
    echo "Checking that the mac0 interface on $NODE is up"
    if [ -z "$OUT" ]; then
        echo "The mac0 interface is not up"
        exit 1
    fi
    echo "... OK"
done

echo "Checking that keycloak pods are Running"
# check_pod_status tool is defined in /opt/cray/tests/ncn-resources/bin.
check_pod_status keycloak
if [ $? -ne 0 ]; then
    echo "Keycloak pods are not in a Running state."
    exit 1
fi
echo "... OK"

echo "All checks completed successfully"
exit 0
