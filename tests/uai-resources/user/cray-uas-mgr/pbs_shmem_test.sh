#!/bin/bash
# Copyright 2019 Cray Inc. All Rights Reserved.
#PBS -l walltime=00:00:30
#PBS -l nodes=2

echo start job $(date)

module load cray-openshmemx

echo "################"
echo "PWD: $PWD"
echo "################"

echo "cray mpiexec -n 2 -ppn 1 --transfer -wdir /tmp ./shmem_hello"
cray mpiexec -n 2 -ppn 1 --transfer  -wdir /tmp ./shmem_hello

echo end job $(date)
