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
###############################################################
#
#     OS Testing - Cray Inc.
#
#     TEST IDENTIFIER   : Test_BMCs_from_UAI
#
#     TEST TITLE        : Test for connection BMCs from a UAI
#
#     DESIGN DESCRIPTION
#       The tests will verify that BMCs cannot be connected 
#       from a UAI.
#
###############################################################

set -o xtrace

List_of_BMCs="" # List of BMCs 

# List of BMCs on SMS node
List_of_BMCs=$(grep -i bmc /etc/hosts | grep -v '#' | grep -v uan | awk '{print $1}')

# Convert newlines into space
List_of_BMCs=$(echo $List_of_BMCs | sed 's/\n/ /g')

# Make sure that BMCs are available on a system 
if [[ -z ${List_of_BMCs} ]]; then
    echo "WARN: If BMCs are not available on a system, skipping check."
    exit 123
fi

# Make sure that UAI is available 
if [ -z "${UAI}" ]; then
    echo "WARN: UAI is unavailable, skipping check"
    exit 123
fi

# Verify that BMCs cannot be connected from a UAI
for i_BMC in ${List_of_BMCs}
do
    echo "ssh ${UAI} ping -c 1 $i_BMC"
    ssh ${UAI} ping -c 1 $i_BMC
    if [[ $? != 0 ]]; then
        echo "PASS: BMC, $i_BMC, is not connected from a UAI"
    else
        echo "FAIL: BMC, $i_BMC, is connected from a UAI. It should be not connected from a UAI."
        echo "It is failed due to known bug, DST-2897: A user can interact with BMCs from a UAI."
        echo "TO-DO: After DST-2897 is fixed, need to change exit 123 to exit 1"
        exit 123
    fi
done

exit 0


