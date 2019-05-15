#!/bin/sh
# 
# This script sets up the mac0 bridge interface on sms03. 
#
# Without the mac0 bridge, the UAI will not be able to communicate
# any services running on the same host as the UAI.
#

# Check for existence of mac0 link to vlan002
ip a | grep mac0@vlan002 > /dev/null 2>&1
# Only create mac0 link to vlan002 if it doesn't exist
if [ $? -ne 0 ]; then
    ip link add mac0 link vlan002 type macvlan mode bridge
    ip a add 10.2.200.201/32 dev mac0
    ip link set mac0 up
    ip route add 10.2.200.0/24 dev mac0
fi