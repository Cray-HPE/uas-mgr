#!/bin/bash
# Copyright 2019 Cray Inc. All Rights Reserved.
#PBS -l walltime=00:00:30
#PBS -l nodes=2

echo start job $(date)

echo "cray mpiexec -n 2 -ppn 1 $RESOURCES/user/cray-uas-mgr/CC_hello"
cray mpiexec -n 2 -ppn 1 $RESOURCES/user/cray-uas-mgr/CC_hello

echo end job $(date)
