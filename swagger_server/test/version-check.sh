#!/bin/sh

grep version: swagger_server/swagger.yaml | awk '{print $2}' | tr -d '\"' > .swagger.version
diff .version .swagger.version
rm -f .swagger.version