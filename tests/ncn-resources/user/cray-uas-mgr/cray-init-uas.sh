#!/bin/bash
# Copyright 2019 Cray Inc. All Rights Reserved.
# Auth Initialization

export CRAY_CONFIG_DIR=$(mktemp -d)
cray init --overwrite --hostname https://api-gw-service-nmn.local --no-auth
if [[ $? == 0 ]]; then
    cray auth login --username $1 --password $2
    if [[ $? == 0 ]]; then
        echo "SUCCESS: Auth Initialization"
        return 0
    else
        echo "FAIL: Auth Initialization."
        return 1
    fi
else
    echo "FAIL: cray init"
    return 1
fi
