#!/bin/bash

#VERSION=$1
VERSION=01-internal
JDK8_URL=http://hg.openjdk.java.net

if test "x${VERSION}" = "x"; then
    echo "No version specified. A version XYZ will be used as'jdk8-bXYZ"
    exit -1;
fi

for REPO_NAME in jdk8 aarch64-port
  do
  mkdir ${REPO_NAME}
  pushd ${REPO_NAME}
  
  REPO_ROOT=${JDK8_URL}/${REPO_NAME}/jdk8

  hg clone ${REPO_ROOT}
  pushd jdk8

  for subrepo in corba hotspot jdk jaxws jaxp langtools nashorn
  do
    hg clone ${REPO_ROOT}/${subrepo}
  done
  rm -rvf jdk/src/share//native/sun/security/ec/impl

  popd

  find jdk8  -name ".hg" -exec rm -rf '{}' \;
  tar cJf java-1.8.0-openjdk-${REPO_NAME}-b${VERSION}.tar.xz jdk8

  popd
done
