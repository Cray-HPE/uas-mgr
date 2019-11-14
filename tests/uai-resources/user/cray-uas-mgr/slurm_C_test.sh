#!/bin/bash
# Copyright 2019 Cray Inc. All Rights Reserved.
#SBATCH --job-name=slurm_C
#SBATCH --nodes=2 
#SBATCH --time=00:0:30 

echo start job $(date)

# Run 2 processes on 2 nodes,
echo "srun -n 2 -N 2 $RESOURCES/user/cray-uas-mgr/C_hello"
srun -n 2 -N 2 $RESOURCES/user/cray-uas-mgr/C_hello

echo end job $(date)
