#!/bin/bash -x
#  this file contains defaults for currently generated source tarball of systemtap

set -e

# TAPSET
export PROJECT_NAME="hg"
export REPO_NAME="icedtea8"
export VERSION="9d464368e06d"
export COMPRESSION=xz
export OPENJDK_URL=http://icedtea.classpath.org
export FILE_NAME_ROOT=${PROJECT_NAME}-${REPO_NAME}-${VERSION}
export TO_COMPRESS="*/tapset"
# warning, filename  and filenameroot creation is duplicated here from generate_source_tarball.sh
CLONED_FILENAME=${FILE_NAME_ROOT}.tar.${COMPRESSION}
TAPSET_VERSION=3.2
TAPSET=systemtap_"$TAPSET_VERSION"_tapsets_$CLONED_FILENAME
if [ ! -f ${TAPSET} ] ; then
  if [ ! -f ${CLONED_FILENAME} ] ; then
  echo "Generating ${CLONED_FILENAME}"
    sh ./generate_singlerepo_source_tarball.sh
  else 
    echo "exists exists exists exists exists exists exists "
    echo "reusing reusing reusing reusing reusing reusing "
    echo ${CLONED_FILENAME}
  fi
  mv -v $CLONED_FILENAME  $TAPSET
else 
  echo "exists exists exists exists exists exists exists "
  echo "reusing reusing reusing reusing reusing reusing "
  echo ${TAPSET}
fi
