#!/bin/bash

set -ex

python3 -m swagger_server &
sleep 5
curl --fail http://localhost:8080/v1/mgr-info
