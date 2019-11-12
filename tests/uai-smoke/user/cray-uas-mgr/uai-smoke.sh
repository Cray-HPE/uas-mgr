#!/bin/bash

# uai-smoke.sh - UAI Smoke
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

TEST_CASE_HEADER "Verify that the api gateway is accessible from a UAI"
ping -c1 $API_GATEWAY
if [[ $? == 0 ]]; then
    echo ""
    echo "SUCCESS: The api gateway, $API_GATEWAY, is accessible from a UAI."
else
    echo ""
    echo "FAIL: The api gateway, $API_GATEWAY, is not accessible from a UAI."
    exit 1
fi

TEST_CASE_HEADER "Verify that PE is installed on a UAI"
module list
if [[ $? == 0 ]]; then
    echo ""
    echo "SUCCESS: PE is installed on a UAI."
else
    echo ""
    echo "FAIL: PE is not installed on a UAI."
    exit 1
fi

# Test auth Initialization
AUTH_INIT

# WLM_NAME is defined in $RESOURCES/user/cray-uas-mgr/uai-common-lib.sh
if [[ $WLM_NAME == "slurm" ]]; then

    # SLURM smoke test
    WLM_SMOKE_TEST "sinfo -r -l --states=idle"
    WLM_SMOKE_TEST "srun -n 1 hostname"
    WLM_SMOKE_TEST "squeue"
    WLM_SMOKE_TEST "sacct"
    WLM_SMOKE_TEST "sacctmgr list account"

elif [[ $WLM_NAME == "pbs" ]]; then

    # PBS smoke test
    WLM_SMOKE_TEST "pbsnodes -a"
    WLM_SMOKE_TEST "qstat -B"

else
    echo "WARNING: Cannot find WLM on a UAI. Skipping check..."
    exit 123
fi

# cleanup
CLEANUP_TEST

exit 0

