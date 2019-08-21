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

if [[ -n $ID_UANs ]]; then
    echo "#################################################"
    echo "ID for nodes: $ID_UANs"
    echo "#################################################"
else
    echo "FAIL: No IDs are available on a system"
    exit 1
fi

# Run cray hsm Inventory Hardware describe ID
for id in $ID_UANs
do
    echo ""
    echo "#################################################"
    echo "cray hsm Inventory Hardware describe $id"
    echo "#################################################"
    cray hsm Inventory Hardware describe $id
    if [[ $? == 0 ]]; then
        echo "UAN is installed on a system."
    else
        echo "FAIL: UAN is not installed on a system. Skipping check..."
        echo "After an automated installation of UAN is done, we need to change exit 123 to exit 1"
        exit 123
    fi
done

# Get list of UANs
if [[ -f /etc/ansible/hosts/uan ]]; then
    List_UANs=$(cat /etc/ansible/hosts/uan | grep -v "\[" | grep -v "#")
    if [[ -n $List_UANs ]]; then
        echo "List of UANs: $List_UANs"
    else
        echo "FAIL: No UANs on a system"
        exit 1
    fi
else
    echo "FAIL: /etc/ansible/hosts/uan doesn't exit"
    exit 1
fi

# Verify that ssh UAN works well
for i_uan in $List_UANs
do
    # Verify that ssh UAN cat /etc/motd works well
    ssh $i_uan cat /etc/motd
    if [[ $? == 0 ]]; then
        echo "PASS: ssh $i_uan cat /etc/motd works well"
    else
        echo "FAIL: ssh $i_uan cat /etc/motd doesn't work."
        exit 1	
    fi

    # Verify that PE is installed on UAN
    ssh $i_uan module list
    if [[ $? == 0 ]]; then
        echo "PASS: ssh $i_uan module list works well"
    else
        echo "FAIL: ssh $i_uan module list doesn't work."
        echo "After CASMUSER-1328 is fixed, need to change exit 123 to exit 1"
        exit 123
    fi
done

exit 0

