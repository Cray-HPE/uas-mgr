#!/bin/bash

# uan-smoke.sh - UAN Smoke
# Copyright 2019 Cray Inc. All Rights Reserved.

# See if Role="Application" for UAN is in the Node Map
cray hsm Defaults NodeMaps list | grep Application
if [[ $? == 0 ]]; then 
    echo "Role=Application for UAN is in the Node Map"
else
    echo "Role=Application for UAN is not in the Node Map. Skipping check..."
    echo "After an automated installation of UAN is done, we need to change exit 123 to exit 1"
    exit 123
fi

# Get ID for UAN
ID_UANs=$(cray hsm Defaults NodeMaps list | grep ID | grep -v NID | awk '{print $3}' | sed 's/"//g')
for id in $ID_UANs
do
    cray hsm Inventory Hardware describe $id
    if [[ $? == 0 ]]; then
        echo "UAN is installed on a system."
    else
        echo "FAIL: UAN is not installed on a system. Skipping check..."
        echo "After an automated installation of UAN is done, we need to change exit 123 to exit 1"
        exit 123
    fi
done

# Test ssh to UAN
List_UANs=$(cat /etc/ansible/hosts/uan | grep -v "\[")

for i_uan in $List_UANs
do
    ssh $i_uan cat /etc/motd
    if [[ $? == 0 ]]; then
        echo "PASS: ssh to UAN works well"
    else
        echo "FAIL: ssh to UAN doesn't work."
        exit 1	
    fi
done

exit 0

