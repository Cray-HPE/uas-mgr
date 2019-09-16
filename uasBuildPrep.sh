#!/bin/bash

#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#

# Add repo for build macros
zypper --non-interactive addrepo --no-gpgcheck \
    http://car.dev.cray.com/artifactory/shasta-premium/SHASTA-OS/sle15_ncn/x86_64/dev/master/ \
    shasta-os-build-resource
