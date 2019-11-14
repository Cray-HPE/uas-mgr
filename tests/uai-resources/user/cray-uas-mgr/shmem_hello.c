/* SHMEM program hello */
/* Copyright 2019 Cray Inc. All Rights Reserved. */

#include <stdio.h>
#include <shmem.h>

int main(void)
{
    shmem_init();            
    int me   = shmem_my_pe();            
    int npes = shmem_n_pes();            
    printf("Hello World from Shmem #%d of %d\n", me, npes);            
    shmem_finalize();            
    return 0; 
} 
