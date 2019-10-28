#!/bin/bash

# uai-diagnostics.sh - UAI Health Check
# Copyright 2019 Cray Inc. All Rights Reserved.

# This script is designed to test whether launched UAIs
# will be healthy by checking common issues that prevent
# UAIs from launching or from being reachable. Failures
# in this script generally indicate an issue in localization,
# networking, or post-install config. They may not be indicative
# of a UAS service issue.

# UAS common functions to test
# $RESOURCES is set to /opt/cray/tests/ncn-resources
if [[ -f $RESOURCES/user/cray-uas-mgr/uas-common-lib.sh ]]; then
    echo "source $RESOURCES/user/cray-uas-mgr/uas-common-lib.sh"
    source $RESOURCES/user/cray-uas-mgr/uas-common-lib.sh
else
    echo "FAIL: Cannot find uas-common-lib.sh. Skipping check..."
    exit 123
fi

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
export CRAY_CONFIG_DIR=$(mktemp -d)
cray init --hostname https://api-gw-service-nmn.local --no-auth
cray auth login --username $COMMON_USER_NAME --password $COMMON_USER_PW
DEFAULT_IMAGE=$(cray uas images list | grep ^default_image | awk '{ print $3 }' | sed 's/"//g')
if [ -z "$DEFAULT_IMAGE" ]; then
    echo "No default image found in images list output"
    exit 1
fi
rm -r $CRAY_CONFIG_DIR
echo "... OK"

echo "Checking to see whether any hosts are labeled and ready to run UAIs"
NODES=(`kubectl get node --show-labels -l uas | grep Ready | awk '{ print $1 }'`)
if [ "${#NODES[@]}" -eq 0 ]; then
    echo "No nodes in Ready state with the uas=True label"
    exit 1
else
    echo "UAIs are deployable to nodes: ${NODES[*]}"
fi
echo "... OK"

echo "Ensuring that all host filesystems are mounted on all nodes labeled with UAS=true"
HOSTFS=$(kubectl describe cm -n services cray-uas-mgr-cfgmap | grep host_path | grep -v ^# | awk '{ print $2 }')
for NODE in "${NODES[@]}"
do
    echo "Checking filesystems on $NODE"
    for FS in ${HOSTFS}
    do
        echo "Looking for ${FS} on $NODE"
        ssh $NODE "ls ${FS}"
    done
    echo "... OK"
done

echo "Checking that the ${DEFAULT_IMAGE} is available on all nodes labeled with UAS=true"
for NODE in "${NODES[@]}"
do
    echo "Checking for Docker image ${DEFAULT_IMAGE} on $NODE"
    ssh $NODE "docker images ${DEFAULT_IMAGE} | grep -v ^REPOSITORY"
    echo "... OK"
done

echo "Checking that the macvlan interface is available and online"
for NODE in "${NODES[@]}"
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
kubectl get pods -n services -l app=keycloak-database | grep Running
if [ $? -ne 0 ]; then
    echo "Keycloak Database pods are not in a Running state."
    exit 1
fi
kubectl get pods -n services -l app=keycloak | grep Running
if [ $? -ne 0 ]; then
    echo "Keycloak pods are not in a Running state."
    exit 1
fi
echo "... OK"

echo "All checks completed successfully"
exit 0
