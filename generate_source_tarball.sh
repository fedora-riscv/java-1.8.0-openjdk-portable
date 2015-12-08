#!/bin/bash -x
# Generates the 'source tarball' for JDK 8 projects.
#
# Example:
# When used from local repo set REPO_ROOT pointing to file:// wth your repo
# if your local repo follows upstream forests conventions, you may be enough by setting OPENJDK_URL
# if you wont to use local copy of patch PR2126 set path to it to PR2126 variable
#
# In any case you have to set PROJECT_NAME REPO_NAME and VERSION. eg:
# PROJECT_NAME=jdk8u   OR   aarch64-port 
# REPO_NAME=jdk8u60    OR   jdk8u60 
# VERSION=jdk8u60-b27  OR aarch64-jdk8u65-b17 OR for head, keyword 'tip' should do the job there
# 
# They are used to create correct name and are used in construction of sources url (unless REPO_ROOT is set)

# This script creates a single source tarball out of the repository
# based on the given tag and removes code not allowed in fedora/rhel. For
# consistency, the source tarball will always contain 'openjdk' as the top
# level folder, name is created, based on parameter
#

set -e

if [ "x$PROJECT_NAME" = "x" ] ; then
	echo "no PROJECT_NAME"
    exit 1
fi
if [ "x$REPO_NAME" = "x" ] ; then
	echo "no REPO_NAME"
    exit 2
fi
if [ "x$VERSION" = "x" ] ; then
	echo "no VERSION"
    exit 3
fi
if [ "x$OPENJDK_URL" = "x" ] ; then
    OPENJDK_URL=http://hg.openjdk.java.net
fi

if [ "x$COMPRESSION" = "x" ] ; then
# rhel 5 needs tar.gz
    COMPRESSION=xz
fi
if [ "x$FILE_NAME_ROOT" = "x" ] ; then
    FILE_NAME_ROOT=${PROJECT_NAME}-${REPO_NAME}-${VERSION}
fi
if [ "x$REPO_ROOT" = "x" ] ; then
    REPO_ROOT="${OPENJDK_URL}/${PROJECT_NAME}/${REPO_NAME}"
fi;

mkdir "${FILE_NAME_ROOT}"
pushd "${FILE_NAME_ROOT}"

hg clone ${REPO_ROOT} openjdk -r ${VERSION}
pushd openjdk
	
#jdk is last for its size
repos="hotspot corba jaxws jaxp langtools nashorn jdk"

for subrepo in $repos
do
    hg clone ${REPO_ROOT}/${subrepo} -r ${VERSION}
done


echo "Removing EC source code we don't build"
rm -vrf jdk/src/share/native/sun/security/ec/impl

echo "Syncing EC list with NSS"
if [ "x$PR2126" = "x" ] ; then
# get pr2126.patch (from http://icedtea.classpath.org//hg/icedtea?cmd=changeset;node=8d2c9a898f50) from most correct tag
# Do not push it or publish it (see http://icedtea.classpath.org/bugzilla/show_bug.cgi?id=2126)
    wget http://icedtea.classpath.org/hg/icedtea/raw-file/tip/patches/pr2126.patch
    patch -Np1 < pr2126.patch
    rm pr2126.patch
else
    patch -Np1 < $PR2126
fi;

popd

if [ "X$COMPRESSION" = "Xxz" ] ; then
    tar --exclude-vcs -cJf ${FILE_NAME_ROOT}.tar.${COMPRESSION} openjdk
else
    tar --exclude-vcs -czf ${FILE_NAME_ROOT}.tar.${COMPRESSION} openjdk
fi

mv ${FILE_NAME_ROOT}.tar.${COMPRESSION}  ..
popd


