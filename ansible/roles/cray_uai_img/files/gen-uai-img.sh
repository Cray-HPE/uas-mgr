#!/bin/bash

# MIT License
#
# (C) Copyright [2020] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

TARBALL=$1
TAG=$2
REPO=cos-1.3-sle-15sp1-compute

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
mkdir certs cmds

cp /usr/share/pki/trust/anchors/*.crt certs
if [ -f /usr/bin/kubectl ]; then
  cp /usr/bin/kubectl cmds
fi

cat << EOF > Dockerfile
FROM $BASE_IMG
COPY certs/*.crt /usr/share/pki/trust/anchors/
COPY cmds/* /usr/bin
RUN update-ca-certificates; \
    zypper addrepo https://packages.local/repository/$REPO $REPO; \
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
