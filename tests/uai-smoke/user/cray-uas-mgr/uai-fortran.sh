#!/bin/bash

# uai-fortran.sh - Compile/launch Fortran application
# Copyright 2019 Cray Inc. All Rights Reserved.

# UAS common functions to test
# $RESOURCES is set to /opt/cray/tests/uai-resources
if [[ -f $RESOURCES/user/cray-uas-mgr/uai-common-lib.sh ]]; then
    echo "source $RESOURCES/user/cray-uas-mgr/uai-common-lib.sh"
    source $RESOURCES/user/cray-uas-mgr/uai-common-lib.sh
else
    echo "FAIL: Cannot find uai-common-lib.sh. Skipping check..."
    exit 123
fi

TEST_CASE_HEADER "Verify that Cray PE is installed"
module is-loaded craype
if [[ $? == 0 ]]; then
    echo ""
    echo "SUCCESS: Cray PE is installed."
else
    echo ""
    echo "FAIL: Cray PE is not installed."
    exit 1
fi

# Test auth Initialization
AUTH_INIT

# If PBS is running on the system, need to do module load cray-pmi
if [[ $WLM_NAME == "pbs" ]]; then
    echo "PBS: module load cray-pmi; module load cray-pmi-lib"
    module load cray-pmi
    module load cray-pmi-lib
fi

# Compile Fortran application
COMPILE_TEST_APP fortran_hello f

# WLM_NAME is defined in $RESOURCES/user/cray-uas-mgr/uai-common-lib.sh
if [[ $WLM_NAME == "slurm" ]]; then

    # Run a test appliation by sbatch
    # TEST_BATCH_JOB <name of job script> <expected output> <expected number of nodes to run> 
    TEST_BATCH_JOB slurm_fortran_test.sh Hello 2

elif [[ $WLM_NAME == "pbs" ]]; then

    # TEST_BATCH_JOB <name of job script> <expected output> <expected number of nodes to run>
    TEST_BATCH_JOB pbs_fortran_test.sh Hello 2

else
    echo "WARNING: Cannot find WLM. Skipping check..."
    exit 123
fi

# Cleanup 
CLEANUP_TEST

exit 0

