#!/bin/bash
#
# uai-common-lib.sh - UAI common functions
# Copyright 2019 Cray Inc. All Rights Reserved.

# Global variables
API_GATEWAY="api-gw-service-nmn.local"
FN_COMMON="uai-common-lib"
MAX_TRY=30
TEST_DIR="$RESOURCES/user/cray-uas-mgr"
JOB_OUT="$TEST_DIR/job$$.out"
USERNAME="uastest"
USERNAMEPWD="uastestpwd"

# Test case header
function TEST_CASE_HEADER {
    ((TEST_CASE++))
    echo ""
    echo "#########################################################################################"
    echo "# Test case $TEST_CASE: $1"
    echo "#########################################################################################"
}

# which_wlm returns a string of the running wlm
# It is defined in /opt/cray/tests/uai-resources/bin
WLM_NAME=$(source which_wlm)

# Auth Initialization
function AUTH_INIT {

    TEST_CASE_HEADER "Auth Initialization"
    export CRAY_CONFIG_DIR=$(mktemp -d)
    echo "CRAY_CONFIG_DIR: $CRAY_CONFIG_DIR"
    echo "cray init --overwrite --hostname https://api-gw-service-nmn.local --no-auth"
    cray init --overwrite --hostname https://api-gw-service-nmn.local --no-auth
    if [[ $? == 0 ]]; then
        # uastest will be changed to a new system account once it is available
        echo "cray auth login --username $USERNAME --password $USERNAMEPWD"
        cray auth login --username $USERNAME --password $USERNAMEPWD
        if [[ $? == 0 ]]; then
            echo "SUCCESS: [$FN_COMMON] Auth Initialization"
        else
            echo "FAIL: [$FN_COMMON] Auth Initialization. Skipping check..."
            exit 123
        fi
    else
        echo "FAIL: [$FN_COMMON] cray init. Skipping check..."
        exit 123
    fi
}

# Compile a test appliation
function COMPILE_TEST_APP {

    TEST_CASE_HEADER "Compile and run a MPI application"
    USER_NAME=$(whoami)

    # $1 is for a test application
    APP=$1

    # $2 is for a test application type
    APP_TYPE=$2

    # Make sure that a test application exists in $TEST_DIR
    if [[ -f $TEST_DIR/$APP.$APP_TYPE ]]; then
        if [[ $APP_TYPE == c ]]; then
            COMPILER="cc"
            COMPILER_OPTION="-dynamic"
        elif [[ $APP_TYPE == cc ]]; then
            COMPILER="CC"
            COMPILER_OPTION="-dynamic"
        elif [[ $APP_TYPE == f ]]; then
            COMPILER="ftn"
            COMPILER_OPTION=""
        else
            echo "WARNING: No support compiler type, $APP_TYPE. Skipping check..."
            exit 123
        fi

        # Compile a test application with the dynamic link option
        echo "$COMPILER $COMPILER_OPTION -o $TEST_DIR/$APP $TEST_DIR/$APP.$APP_TYPE"
        $COMPILER $COMPILER_OPTION -o $TEST_DIR/$APP $TEST_DIR/$APP.$APP_TYPE

        # Verify that a test application is compiled successfully
        if [[ -x $TEST_DIR/$APP ]]; then
            echo "SUCCESS: $TEST_DIR/$APP is compiled successfully"
            echo "cp -f $TEST_DIR/$APP $SHARED_FS/$USER_NAME/."
            cp -f $TEST_DIR/$APP $SHARED_FS/$USER_NAME/.
            if [[ -x $SHARED_FS/$USER_NAME/$APP ]]; then
                echo "SUCCESS: $SHARED_FS/$USER_NAME/$APP exists"
            else
                echo "FAIL: $SHARED_FS/$USER_NAME/$APP doesn't exist. Skipping check..."
                exit 123
            fi
        else
            echo "FAIL: $TEST_DIR/$APP is not compiled"
            exit 1
        fi
    else
        echo "WARNING: $TEST_DIR/$APP.$APP_TYPE doesn't exist. Skipping check..."
        exit 123
    fi
}

# Launch a test appliation by a job script
function TEST_BATCH_JOB {

    TEST_CASE_HEADER "Test a batch job"

    JOB_SCRIPT=$1
    EXP_OUTPUT=$2
    EXP_NUM_NODE=$3

    if [[ $WLM_NAME == "slurm" ]]; then
        batch_command="sbatch"
        jobstate_command="squeue"
        jobcancel_command="scancel"
        # sbatch --parsable option will output only the jobid and cluster name (if present),
        # separated by semicolon, only on successful submission.
        batch_command_option1="--parsable"
        batch_command_option2="-j"
    fi

    if [[ $WLM_NAME == "pbs" ]]; then
        batch_command="qsub"
        jobstate_command="qstat"
        jobcancel_command="qdel"
        batch_command_option1=""
        batch_command_option2="-f"
    fi

    # Make sure that a job script exists in $TEST_DIR
    if [[ -f $TEST_DIR/$JOB_SCRIPT ]]; then
        echo "$batch_command $batch_command_option1 -o $JOB_OUT $TEST_DIR/$JOB_SCRIPT"
        jobid=$($batch_command $batch_command_option1 -o $JOB_OUT $TEST_DIR/$JOB_SCRIPT)

        job_done=0
        echo "Checking job status..."

        for ((try = 1; try <= $MAX_TRY; try++))
        do
            sleep 1
            echo "$jobstate_command $batch_command_option2 $jobid | grep $jobid"
            $jobstate_command $batch_command_option2 $jobid | grep $jobid
            check_RC=$?
            echo "check_RC: $check_RC"
            if (( check_RC != 0 )); then
                job_done=1
                echo "Job $jobid completed."
                break;
            fi
        done

        echo "Job done flag: $job_done with try: $try"

        if (( job_done == 0 )); then
            echo "$jobcancel_command $jobid"
            $jobcancel_command $jobid

            echo "$jobstate_command:"
            $jobstate_command
            echo "FAIL: Job $jobid has taken too long to complete."
            # Cleanup
            CLEANUP_TEST
            exit 1
        else
            echo "Job $jobid completed."
            imax_try=10
            for ((itry = 1; itry <= $imax_try; itry++))
            do
                sleep 1
                echo "itry: $itry"
                echo "ls -ltr $TEST_DIR"
                ls -ltr $TEST_DIR
                echo "chmod 744 $JOB_OUT"
                chmod 744 $JOB_OUT
                # Make sure that the job runs well
                if [[ -f $JOB_OUT ]]; then
                    cat $JOB_OUT
                    grep -i error $JOB_OUT
                    if [[ $? == 0 ]]; then
                        echo "Try: $itry"
                        echo "FAIL: $batch_command has an error."
                        # Cleanup
                        CLEANUP_TEST
                        exit 1
                    else
                        # $2 is for a set of expected output
                        output_lc=$(grep $EXP_OUTPUT $JOB_OUT | wc -l)
                        # $3 is for expected number of nodes
                        if [[ $output_lc == $EXP_NUM_NODE ]]; then
                            echo "Try: $itry"
                            echo "SUCCESS: $batch_command job runs on expected number of nodes, $EXP_NUM_NODE"
                            break;
                        else
                             echo "FAIL: $batch_command job didn't run on expected number of nodes, $EXP_NUM_NODE"
                             echo "Output lines found: ${output_lc}"
                             # Cleanup
                             CLEANUP_TEST
                             exit 1
                        fi
                    fi
                fi
            done

            if ((itry > imax_try))
            then
                echo "Try: $itry"
                if [[ -f $JOB_OUT ]]; then
                    echo "cat $JOB_OUT"
                    cat $JOB_OUT
                else
                    echo "FAIL: Cannot find output file, $JOB_OUT"
                    # Cleanup
                    CLEANUP_TEST
                    exit 1
                fi
            fi
        fi
    else
        # Cleanup
        CLEANUP_TEST
        echo "WARNING: Cannot find $TEST_DIR/$JOB_SCRIPT. Skipping check..."
        exit 123
    fi
}

# WLM smoke test
function WLM_SMOKE_TEST {

    # First argument is for testing WLM commands
    if [[ $1 != "" ]]; then
        TEST_CASE_HEADER "Test $1"
        CMD="$1"
        echo "$CMD"
        $CMD
        if [[ $? == 0 ]]; then
            echo "SUCCESS: $CMD works well."
        else
            echo "FAIL: $CMD doesn't work"
            # Cleanup
            CLEANUP_TEST
            exit 1
        fi
    else
        echo "WARNING: No first argument, WLM commands, supplied. Skipping check..."
        exit 123
    fi
}

# Cleanup
function CLEANUP_TEST {
    if [[ -d $CRAY_CONFIG_DIR ]]; then
        echo "rm -rf $CRAY_CONFIG_DIR"
        rm -rf $CRAY_CONFIG_DIR
    fi
}
