#!/bin/bash
# Copyright 2019 Cray Inc. All Rights Reserved.
#SBATCH --job-name=slurm_fortran
#SBATCH --nodes=2 
#SBATCH --time=00:0:20 

echo start job $(date)

# Run 2 processes on 2 nodes,
echo "srun -n 2 -N 2 $RESOURCES/user/cray-uas-mgr/fortran_hello"
srun -n 2 -N 2 $RESOURCES/user/cray-uas-mgr/fortran_hello

echo end job $(date)
