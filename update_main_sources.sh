#!/bin/bash -x
# Generates the 'source tarball' for JDK 8 projects and update spec infrastructure
# By default, this script regenerate source as they are currently used. 
# so if the version of sources change, this file changes and is pushed
#
# In any case you have to set PROJECT_NAME REPO_NAME and VERSION. eg:
# PROJECT_NAME=jdk8u   OR   aarch64-port 
# REPO_NAME=jdk8u60    OR   jdk8u60 
# VERSION=jdk8u60-b27  OR aarch64-jdk8u65-b17 OR for head, keyword 'tip' should do the job there
# 
# If you don't, default are used and so already uploaded tarball regenerated
# They are used to create correct name and are used in construction of sources url (unless REPO_ROOT is set)
# 
# For other useful variables see generate_source_tarball.sh
#
# the used values are then substituted to spec and sources

if [ ! "x$PR2126" = "x" ] ; then
  if [ ! -f "$PR2126" ] ; then
    echo "You have specified PR2126 as $PR2126 but it does not exists. exiting"
    exit 1
  fi
fi

set -e

if [ "x$PROJECT_NAME" = "x" ] ; then
    PROJECT_NAME="aarch64-port"
fi
if [ "x$REPO_NAME" = "x" ] ; then
    REPO_NAME="jdk8u-shenandoah"
fi
if [ "x$VERSION" = "x" ] ; then
    VERSION="aarch64-shenandoah-jdk8u181-b15"
fi

if [ "x$COMPRESSION" = "x" ] ; then
# rhel 5 needs tar.gz
    COMPRESSION=xz
fi
if [ "x$FILE_NAME_ROOT" = "x" ] ; then
    FILE_NAME_ROOT=${PROJECT_NAME}-${REPO_NAME}-${VERSION}
fi
if [ "x$PKG" = "x" ] ; then
    URL=`cat .git/config  | grep url`
    PKG=${URL##*/}
fi
if [ "x$SPEC" = "x" ] ; then
    SPEC=${PKG}.spec
fi
if [ "x$RELEASE" = "x" ] ; then
    RELEASE=1
fi

FILENAME=${FILE_NAME_ROOT}.tar.${COMPRESSION}

if [ ! -f ${FILENAME} ] ; then
echo "Generating ${FILENAME}"
. ./generate_source_tarball.sh
else 
echo "${FILENAME} already exists, using"
fi


echo "Touching spec: $SPEC"
echo sed -i "s/^%global\s\+project.*/%global project         ${PROJECT_NAME}/" $SPEC 
echo sed -i "s/^%global\s\+repo.*/%global repo            ${REPO_NAME}/" $SPEC 
echo sed -i "s/^%global\s\+revision.*/%global revision        ${VERSION}/" $SPEC 
# updated sources, resetting release
echo sed -i "s/^Release:.*/Release: $RELEASE.%{buildver}%{?dist}/" $SPEC

echo "New sources"
cat sources
a_sources=`cat sources | sed "s/.*(//g" | sed "s/).*//g" | sed "s/.*\s\+//g"`
echo "    you can get inspired by following %changelog template:"
user_name=`whoami`
user_record=$(getent passwd $user_name)
user_gecos_field=$(echo "$user_record" | cut -d ':' -f 5)
user_full_name=$(echo "$user_gecos_field" | cut -d ',' -f 1)
spec_date=`date +"%a %b %d %Y"`
# See spec:
revision_helper=`echo ${MAIN_VERSION%-*}`
updatever=`echo ${revision_helper##*u}`
buildver=`echo ${MAIN_VERSION##*-}`
echo "* $spec_date $user_full_name <$user_name@redhat.com> - 1:1.8.0.$updatever-$RELEASE.$buildver" 
echo "- updated to $MAIN_VERSION (from $PROJECT_NAME/$MAIN_REPO_NAME)"
echo "- updated to $VERSION (from $PROJECT_NAME/$REPO_NAME) of hotspot"
echo "- used $FILENAME as new sources"
echo "- used $FILENAME_SH as new sources for hotspot"

echo "    execute:"
echo "fedpkg/rhpkg new-sources "$a_sources
echo "    to upload sources"
echo "you can verify by fedpkg/rhpkg prep --arch XXXX on all architectures: x86_64 i386 i586 i686 ppc ppc64 ppc64le s390 s390x aarch64 armv7hl"

