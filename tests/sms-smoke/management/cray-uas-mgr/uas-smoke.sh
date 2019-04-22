#!/bin/bash

# uas-smoke.sh - UAS Manager Smoke
# Copyright 2019 Cray Inc. All Rights Reserved.

set -x
set -e

cray uas mgr-info list

cray uas images list

cray uas uais list

exit 0
