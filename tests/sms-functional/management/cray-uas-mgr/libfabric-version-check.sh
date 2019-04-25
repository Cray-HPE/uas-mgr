#!/bin/bash
#
# Check for libfabric version matches - from DST-1870 issue
# Copyright 2019 Cray Inc. All Rights Reserved.

UAI_name=""
function cleanup {
    if [ -n "$UAI_name" ]; then
        echo "Cleaning up UAI $UAI_name"
        cray uas delete --uai-list $UAI_name
    fi
}
trap cleanup INT QUIT EXIT

function create_uai {
    UAI_info=$(cray uas create --username root --publickey ~/.ssh/id_rsa.pub)
    UAI_connect=$(python -c "x=$(echo $UAI_info); print x['uai_connect_string']")
    UAI_name=$(python -c "x=$(echo $UAI_info); print x['uai_name']")
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
        exit 1
    fi
}

LF_VER_NID=$(ssh nid000001 ls -1 /opt/cray/libfabric/)
if [ -z "${LF_VER_NID}" ]; then
    echo "Unable to check libfabric version on nid000001, skipping check"
    exit 123
fi

create_uai

LF_VER_UAI=$(ssh $UAI_connect ls -1 /opt/cray/libfabric/)
if [ -z "${LF_VER_UAI}" ]; then
    echo "Unable to check libfabric version on UAI, skipping check"
    exit 123
else
    DIFF=$(diff -u <(echo "${LF_VER_NID}") <(echo "${LF_VER_UAI}"))
    if [ $? -eq 0 ]; then
        echo "libfabric versions on compute node and UAI match (${LF_VER_NID})"
        exit 0
    else
        echo "libfabric versions on compute node do NOT match, diff follows:"
        echo "${DIFF}"
        echo "MPI jobs may not be able to run"
        exit 1
    fi
fi
