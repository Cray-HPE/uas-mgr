#!/bin/bash

diff .version <(grep version: swagger_server/swagger.yaml | awk '{print $2}' | tr -d '\"')
