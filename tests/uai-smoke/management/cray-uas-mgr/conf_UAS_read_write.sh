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

# Output 
# $TMPDIR is set by the ct-driver
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
