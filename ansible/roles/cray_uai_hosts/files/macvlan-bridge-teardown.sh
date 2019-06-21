#!/bin/sh
# 
# This script removes the mac0 bridge interface on UAI hosts. 
#

# Check for existence of mac0 link
ip a | grep mac0@vlan002 > /dev/null 2>&1
# Only teardown mac0 bridge if it already exists
if [ $? -eq 0 ]; then
    ip link delete mac0
fi
