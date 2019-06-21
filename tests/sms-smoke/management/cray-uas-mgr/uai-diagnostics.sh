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

echo "Checking that default image is available"
export CRAY_CONFIG_DIR=$(mktemp -d)
cray init --hostname https://api-gw-service-nmn.local --no-auth
cray auth login --username uastest --password uastestpwd

DEFAULT_IMAGE=$(cray uas images list | grep ^default_image | awk '{ print $3 }' | sed 's/"//g')
echo "Looking for ${DEFAULT_IMAGE} in docker"
docker images ${DEFAULT_IMAGE} | grep -v ${DEFAULT_IMAGE}
rm -r $CRAY_CONFIG_DIR
echo "... OK"

echo "Ensuring that all host filesystems are mounted on any sms node labeled with UAS=true"
HOSTFS=$(kubectl describe cm -n services cray-uas-mgr-cfgmap | grep host_path | grep -v ^# | awk '{ print $2 }')
NODES=$(kubectl get node --show-labels -l uas | grep Ready | awk '{ print $1 }')
for NODE in ${NODES}
do
    echo "Checking filesystems on $NODE"
    for FS in ${HOSTFS}
    do
        echo "Looking for ${FS} on $NODE"
        ssh $NODE "ls ${FS}"
    done
    echo "... OK"
done

echo "All checks completed successfully"
exit 0
