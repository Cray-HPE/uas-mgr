#!/bin/bash

# test-network-config-check.sh - Unit tests for the network-config-check.py script
# Copyright 2019, Cray Inc.  All Rights Reserved.

# To run these tests you will need to have PyYAML installed into your local Python
# environment or active virtual environment.

HAS_ERRORS=0


echo -n "Verify using a completely unparseable file...   "
OUTPUT=$(echo -e "\x02\xc5\xd8" | python3 network-config-check.py 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -ne 3 ]; then
	echo "FAILED with an unexpected edit code; expected 2 got ${EXIT_CODE}"
else
	echo "SUCCESS"
fi


echo -n "Verify using valid YAML, but an incorrect structure...   "
OUTPUT=$(echo "\
---
fake: true
file: network-check-config.py
" | python3 network-config-check.py 2>&1
)
EXIT_CODE=$?
if [ $EXIT_CODE -ne 4 ]; then
	echo "FAILED with an unexpected edit code; expected 3 got ${EXIT_CODE}"
	HAS_ERRORS=1
else
	echo "SUCCESS"
fi


echo -n "Verify using a valid file with correct data...    "
OUTPUT=$(echo "\
---
networks:
  node_management:
    blocks:
      ipv4:
        - label: river
          network: 10.2.0.0/16
          gateway: 10.2.255.254
          subnets:
            - label: default
              network: 10.1.0.0/16
              gateway: 10.2.255.254
              dhcp:
                start: 10.2.50.0
                end: 10.2.99.252
            - label: uai_macvlan
              network: 10.2.100.0/24
              gateway: 10.2.255.254
" | python3 network-config-check.py 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
	echo "FAILED with an unexpected edit code; expected 0 got ${EXIT_CODE}"
	HAS_ERRORS=1
else
	echo "SUCCESS"
fi


echo -n "Verify using an invalid network entry in a non-uai_macvlan subnet...   "
OUTPUT=$(echo "\
---
networks:
  node_management:
    blocks:
      ipv4:
        - label: river
          network: 10.2.0.0/16
          gateway: 10.2.255.254
          subnets:
            - label: default
              network: 10.4.0.0/16
              gateway: 10.2.255.254
              dhcp:
                start: 10.2.50.0
                end: 10.2.99.252
            - label: metallb
              network: 10.2.100.0/24
              gateway: 10.2.255.254
" | python3 network-config-check.py 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
	echo "FAILED with an unexpected edit code; expected 0 got ${EXIT_CODE}"
	HAS_ERRORS=1
else
	if [[ "$OUTPUT" != *"WARNING"* ]]; then
		echo "FAILED to find warnings in the command output"
		HAS_ERRORS=1
	else
		echo "SUCCESS"
	fi
fi


echo -n "Verify using an invalid DHCP start entry in a non-uai_macvlan subnet...   "
OUTPUT=$(echo "\
---
networks:
  node_management:
    blocks:
      ipv4:
        - label: river
          network: 10.2.0.0/16
          gateway: 10.2.255.254
          subnets:
            - label: default
              network: 10.2.0.0/16
              gateway: 10.2.255.254
              dhcp:
                start: 10.1.50.0
                end: 10.2.99.252
" | python3 network-config-check.py 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
	echo "FAILED with an unexpected edit code; expected 2 got ${EXIT_CODE}"
	HAS_ERRORS=1
else
	if [[ "$OUTPUT" != *"WARNING"* ]]; then
		echo "FAILED to find warnings in the command output"
		HAS_ERRORS=1
	else
		echo "SUCCESS"
	fi
fi

echo -n "Verify using an invalid DHCP end entry in a non-uai_macvlan subnet...   "
OUTPUT=$(echo "\
---
networks:
  node_management:
    blocks:
      ipv4:
        - label: river
          network: 10.2.0.0/16
          gateway: 10.2.255.254
          subnets:
            - label: default
              network: 10.2.0.0/16
              gateway: 10.2.255.254
              dhcp:
                start: 10.2.50.0
                end: 10.3.99.252
" | python3 network-config-check.py 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
	echo "FAILED with an unexpected edit code; expected 2 got ${EXIT_CODE}"
	HAS_ERRORS=1
else
	if [[ "$OUTPUT" != *"WARNING"* ]]; then
		echo "FAILED to find warnings in the command output"
		HAS_ERRORS=1
	else
		echo "SUCCESS"
	fi
fi


echo -n "Verify using an invalid network entry in a uai_macvlan subnet...   "
OUTPUT=$(echo "\
---
networks:
  node_management:
    blocks:
      ipv4:
        - label: river
          network: 10.2.0.0/16
          gateway: 10.2.255.254
          subnets:
            - label: uai_macvlan
              network: 10.4.0.0/16
              gateway: 10.2.255.254
              dhcp:
                start: 10.2.50.0
                end: 10.2.99.252
" | python3 network-config-check.py 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -ne 2 ]; then
	echo "FAILED with an unexpected edit code; expected 2 got ${EXIT_CODE}"
	HAS_ERRORS=1
else
	echo "SUCCESS"
fi


echo -n "Verify using an invalid DHCP start entry in a uai_macvlan subnet...   "
OUTPUT=$(echo "\
---
networks:
  node_management:
    blocks:
      ipv4:
        - label: river
          network: 10.2.0.0/16
          gateway: 10.2.255.254
          subnets:
            - label: uai_macvlan
              network: 10.2.0.0/16
              gateway: 10.2.255.254
              dhcp:
                start: 10.1.50.0
                end: 10.2.99.252
" | python3 network-config-check.py 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -ne 2 ]; then
	echo "FAILED with an unexpected edit code; expected 2 got ${EXIT_CODE}"
	HAS_ERRORS=1
else
	echo "SUCCESS"
fi


echo -n "Verify using an invalid DHCP end entry in a uai_macvlan subnet...   "
OUTPUT=$(echo "\
---
networks:
  node_management:
    blocks:
      ipv4:
        - label: river
          network: 10.2.0.0/16
          gateway: 10.2.255.254
          subnets:
            - label: uai_macvlan
              network: 10.2.0.0/16
              gateway: 10.2.255.254
              dhcp:
                start: 10.2.50.0
                end: 10.3.99.252
" | python3 network-config-check.py 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -ne 2 ]; then
	echo "FAILED with an unexpected edit code; expected 2 got ${EXIT_CODE}"
	HAS_ERRORS=1
else
	echo "SUCCESS"
fi


exit $HAS_ERRORS
