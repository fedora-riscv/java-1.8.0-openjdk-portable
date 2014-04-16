#!/bin/bash

# Generates the 'source tarball' for JDK 8 projects.
#
# Usage: generate_source_tarball.sh project_name repo_name tag
#
# Examples:
#   ./generate_source_tarball.sh jdk8 jdk8 jdk8-b79
#   ./generate_source_tarball.sh jdk8u jdk8u jdk8u5-b13
#   ./generate_source_tarball.sh aarch64-port jdk8 aarch64-${DATE}
#
# This script creates a single source tarball out of the repository
# based on the given tag and removes code not allowed in fedora. For
# consistency, the source tarball will always contain 'jdk8' as the top
# level folder.

set -e

PROJECT_NAME="$1"
REPO_NAME="$2"
VERSION="$3"
OPENJDK_URL=http://hg.openjdk.java.net

if [[ "${PROJECT_NAME}" = "" ]] ; then
    echo "No repository specified."
    exit -1
fi
if [[ "${REPO_NAME}" = "" ]] ; then
    echo "No repository specified."
    exit -1
fi
if [[ "${VERSION}" = "" ]]; then
    echo "No version/tag specified."
    exit -1;
fi

mkdir "${REPO_NAME}"
pushd "${REPO_NAME}"

REPO_ROOT="${OPENJDK_URL}/${PROJECT_NAME}/${REPO_NAME}"

wget "${REPO_ROOT}/archive/${VERSION}.tar.gz"
tar xf "${VERSION}.tar.gz"
rm  "${VERSION}.tar.gz"

mv "${REPO_NAME}-${VERSION}" jdk8
pushd jdk8

for subrepo in corba hotspot jdk jaxws jaxp langtools nashorn
do
    wget "${REPO_ROOT}/${subrepo}/archive/${VERSION}.tar.gz"
    tar xf "${VERSION}.tar.gz"
    rm "${VERSION}.tar.gz"
    mv "${subrepo}-${VERSION}" "${subrepo}"
done

rm -vr jdk/src/share/native/sun/security/ec/impl

popd

tar cJf ${REPO_NAME}-${VERSION}.tar.xz jdk8

popd

mv "${REPO_NAME}/${REPO_NAME}-${VERSION}.tar.xz" .
