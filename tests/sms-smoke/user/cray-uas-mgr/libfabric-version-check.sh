#!/bin/bash
# MIT License
#
# (C) Copyright [2020] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# Check for libfabric version matches - from DST-1870 issue

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
