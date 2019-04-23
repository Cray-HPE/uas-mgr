#!/bin/bash
#
# Check for libfabric version matches - from DST-1870 issue
# Copyright 2019 Cray Inc. All Rights Reserved.

function cleanup {
    echo "Cleaning up UAI $1"
    cray uas delete --uai-list $1
}

LF_VER_NID=$(ssh nid000001 ls -1 /opt/cray/libfabric/)
if [ -z "${LF_VER_NID}" ]; then
    echo "Unable to check libfabric version on nid000001, skipping check"
    exit 123
fi

UAI_info=$(cray uas create --username root --publickey ~/.ssh/id_rsa.pub)
UAI_connect=$(echo "$UAI_info" | grep ua.*_connect_string | awk '{print $3, $4, $5, $6, $7}' | sed 's/"//g' | sed 's/,//g')
UAI_name=$(echo "$UAI_info" | grep ua.*_name | awk '{print $2}' | sed 's/"//g' | sed 's/,//g')
pod_ready=0
# wait up to 5 minutes for the Pod to be ready
for i in {1..20}
do
    status=$(cray uas uais list | grep -B3 ${UAI_name} | grep uai_status | awk '{print $2 $3}' | sed 's/"//g' | sed 's/,//g')
    if [ ${status} == "Running:Ready" ]; then
        pod_ready=1
        break
    else
         sleep 15
         echo -ne ". "
    fi
done

if (( pod_ready == 0 )) ; then
    echo "Waiting for UAI pod timed out after 5 minutes."
    echo "Skipping UAI tests. Deleting UAI"
    cleanup $UAI_name
    exit 1
fi

LF_VER_UAI=$(ssh $UAI_connect ls -1 /opt/cray/libfabric/)
if [ -z "${LF_VER_UAI}" ]; then
    echo "Unable to check libfabric version on UAI, skipping check"
    exit 123
else
    DIFF=$(diff -u <(echo "${LF_VER_NID}") <(echo "${LF_VER_UAI}"))
    if [ $? -eq 0 ]; then
        echo "libfabric versions on compute node and UAI match (${LF_VER_NID})"
        cleanup $UAI_name
        exit 0
    else
        echo "libfabric versions on compute node do NOT match, diff follows:"
        echo "${DIFF}"
        echo "MPI jobs may not be able to run"
        cleanup $UAI_name
        exit 1
    fi
fi
