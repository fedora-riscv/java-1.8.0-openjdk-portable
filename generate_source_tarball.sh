#!/bin/bash
# Generates the 'source tarball' for JDK 8 projects.
#
# Usage: generate_source_tarball.sh project_name repo_name tag
#
# Examples:
#  sh generate_source_tarball.sh jdk8u jdk8u40 jdk8u40-b25
#   ./generate_source_tarball.sh jdk8 jdk8 jdk8-b79
#   ./generate_source_tarball.sh jdk8u jdk8u jdk8u5-b13
#   ./generate_source_tarball.sh aarch64-port jdk8 aarch64-${DATE}
#   ./generate_source_tarball.sh aarch64-port jdk8 aarch64-jdk8u60-b24.2
#	./generate_source_tarball.sh jdk8u jdk8u60 jdk8u60-b27

# This script creates a single source tarball out of the repository
# based on the given tag and removes code not allowed in fedora. For
# consistency, the source tarball will always contain 'openjdk' as the top
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

mv "${REPO_NAME}-${VERSION}" openjdk
pushd openjdk

repos="corba hotspot jdk jaxws jaxp langtools nashorn"
if [ aarch64-port = $PROJECT_NAME ] ; then
#tmp disable because of jdk8-aarch64-jdk8u60-b24.2
echo NOT 
#repos="hotspot"
fi;

for subrepo in $repos
do
    wget "${REPO_ROOT}/${subrepo}/archive/${VERSION}.tar.gz"
    tar xf "${VERSION}.tar.gz"
    rm "${VERSION}.tar.gz"
    mv "${subrepo}-${VERSION}" "${subrepo}"
done

echo "Removing EC source code we don't build"
rm -vrf jdk/src/share/native/sun/security/ec/impl

#get this file http://icedtea.classpath.org/hg/icedtea/raw-file/tip/patches/pr2126.patch (from http://icedtea.classpath.org//hg/icedtea?cmd=changeset;node=8d2c9a898f50)
#from most correct tag
#and use it like below. Do not push it or publish it (see http://icedtea.classpath.org/bugzilla/show_bug.cgi?id=2126)
pwd
echo "Syncing EC list with NSS"
patch -Np1 < ../../pr2126.patch

popd

tar cJf ${REPO_NAME}-${VERSION}.tar.xz openjdk

popd

mv "${REPO_NAME}/${REPO_NAME}-${VERSION}.tar.xz" .
