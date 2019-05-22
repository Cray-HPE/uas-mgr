#!/bin/bash

# uas-smoke.sh - UAS Manager Smoke
# Copyright 2019 Cray Inc. All Rights Reserved.

set -x
set -e

# Set a temp directory for the craycli config
# and auth token
export CRAY_CONFIG_DIR=$(mktemp -d)

cray init --hostname https://api-gw-service-nmn.local --no-auth
cray auth login --username uastest --password uastestpwd

cray uas mgr-info list

cray uas images list

cray uas uais list

rm -r $CRAY_CONFIG_DIR

exit 0
