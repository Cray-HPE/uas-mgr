#!/bin/sh

#
# Copyright 2019, Cray Inc.  All Rights Reserved.
#

set -ex

python3 -m swagger_server &
sleep 5
curl --fail http://localhost:8088/v1/mgr-info
