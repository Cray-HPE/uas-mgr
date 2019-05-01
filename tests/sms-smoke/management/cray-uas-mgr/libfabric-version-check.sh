#!/bin/bash
#
# Check for libfabric version matches - from DST-1870 issue
# Copyright 2019 Cray Inc. All Rights Reserved.

LF_VER_NID=$(ssh nid000001-nmn ls -1 /opt/cray/libfabric/)
if [ -z "${LF_VER_NID}" ]; then
    echo "Unable to check libfabric version on nid000001, skipping check"
    exit 123
fi

if [ -z "${UAI}" ]; then
    echo "UAI is unavailable, skipping check"
    exit 123
fi

LF_VER_UAI=$(ssh $UAI ls -1 /opt/cray/libfabric/)
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
