#!/bin/bash

#
# Copyright 2020, Cray Inc.  All Rights Reserved.
#

TARBALL=$1
TAG=$2
SLES=sles15sp1

BASE_IMG="uai_base_img:latest"

if [ -z $TARBALL ]; then
  echo "Please specify a path to a tar file"
  echo "Usage: ./gen-uai-img.sh <tar_file> <tag>"
  exit 1
fi

if [ -z $TAG ]; then
  echo "Please specify an image tag"
  echo "Usage: ./gen-uai-img.sh <tar_file> <tag>"
  exit 1
fi

if ! [ -f $TARBALL ]; then
  echo "Could not find tar file $TARBALL"
  exit 1
fi

# Import the Tarball as a Docker image
echo "docker import $TARBALL $BASE_IMG"
if ! docker import $TARBALL $BASE_IMG; then
  echo "Failed to run docker import"
  exit 1
fi

workspace=$(mktemp -d)
echo "Created temporary workspace $workspace"
pushd $workspace > /dev/null

cp /usr/share/pki/trust/anchors/*.crt .

cat << EOF > Dockerfile
FROM $BASE_IMG
ADD *.crt /usr/share/pki/trust/anchors/
RUN update-ca-certificates; \
    zypper addrepo https://api-gw-service-nmn.local/repositories/cray-$SLES-ncn cray-$SLES-ncn; \
    zypper --non-interactive --gpg-auto-import-keys --no-gpg-checks install cray-uai-util
RUN rm /etc/security/limits.d/99-cray-network.conf
ENTRYPOINT /usr/bin/uai-ssh.sh
EOF

# Build the new UAI
echo "docker build -t $TAG ."
if ! docker build -t $TAG .; then
  echo "Failed to run docker build"
  popd > /dev/null
  rm -r $workspace
  exit 1
fi

echo "Pushing the image. This could take awhile..."
echo "docker push $TAG"
docker push $TAG

popd > /dev/null
rm -r $workspace

exit 0
