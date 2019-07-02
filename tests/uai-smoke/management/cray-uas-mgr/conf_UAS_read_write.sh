#!/bin/bash
#
# Copyright 2018, 2019 Cray Inc. All Rights Reserved.
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

: "${TMPDIR:=/tmp}"

line="Confidence Test Suite test file on $HOSTNAME"
echo ${line} > $TMPDIR/confidencetest$$.txt

# put contents of confidencetest.txt into variable fileContents
fileContents=$(cat $TMPDIR/confidencetest$$.txt)

if [[ $line == $fileContents ]] ; then
    echo "PASS  The contents of $TMPDIR/confidencetest$$.txt are as expected."
else
    echo "FAIL  The contents of $TMPDIR/confidencetest$$.txt are not as expected. fileContents=$fileContents."
fi

rm $TMPDIR/confidencetest$$.txt
