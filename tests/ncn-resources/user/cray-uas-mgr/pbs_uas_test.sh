#!/bin/bash
# Copyright 2019 Cray Inc. All Rights Reserved.
#PBS -l walltime=00:00:30
#PBS -l nodes=1

echo start job $(date)

echo "cray mpiexec hostname"
cray mpiexec hostname

echo "cray mpiexec sleep 10"
cray mpiexec sleep 10

echo end job $(date)
