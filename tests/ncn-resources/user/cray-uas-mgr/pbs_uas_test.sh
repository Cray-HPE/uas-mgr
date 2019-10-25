#!/bin/bash
# Copyright 2019 Cray Inc. All Rights Reserved.
#PBS -l walltime=00:00:30
#PBS -l nodes=1

echo start job $(date)
export CRAY_CONFIG_DIR=$(mktemp -d)
cray init --no-auth --overwrite --hostname https://api-gw-service-nmn.local
cray auth login --username uastest --password uastestpwd

echo "cray mpiexec hostname"
cray mpiexec hostname

echo "cray mpiexec sleep 10"
cray mpiexec sleep 10

echo end job $(date)
