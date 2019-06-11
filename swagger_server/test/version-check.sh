#!/bin/bash

diff .version <(grep version: swagger_server/swagger.yaml | head -1 | awk '{print $2}' | tr -d '\"')
