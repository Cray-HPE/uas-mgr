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
#     TEST IDENTIFIER   : conf_UAS_read_write
#
#     TEST TITLE        : Simple Read Write Test for Confidence Suite
#
#     DESIGN DESCRIPTION
#       These test cases are executed from the UAI.  The tests will
#       verify we can R/W files
#
###############################################################

set -o errexit
set -o xtrace

# TMPDIR is set by the CT framework
if [[ ! -z $TMPDIR ]]; then 
    echo "TMPDIR is set by the CT framework : $TMPDIR"
else
    # If TMPDIR is not set, TMPDIR=$PWD: 
    echo "TMPDIR=$PWD"
    TMPDIR=$PWD
fi

# Output 
OUTPUT="$TMPDIR/confidencetest$$.txt"

line="Confidence Test Suite test file on $HOSTNAME"
echo ${line} > $OUTPUT

# put contents of confidencetest.txt into variable fileContents
fileContents=$(cat $OUTPUT)

if [[ $line == $fileContents ]] ; then
    echo "PASS  The contents of $OUTPUT are as expected."
else
    echo "FAIL  The contents of $OUTPUT are not as expected. fileContents=$fileContents."

    # CT framework will clean up the test directory as soon as the test is done
    # However, remove $OUTPUT before exiting for just in case
    rm $OUTPUT
    exit 1
fi

rm $OUTPUT
exit 0
