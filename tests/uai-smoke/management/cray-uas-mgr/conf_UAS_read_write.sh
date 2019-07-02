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

# Set TMPDIR
# It would still be expanded to /tmp if $TMPDIR was set but to the empty string
: "${TMPDIR:=/tmp}"

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
    exit 1
fi

rm $OUTPUT
exit 0
