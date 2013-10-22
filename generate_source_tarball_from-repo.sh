#!/bin/bash

set -e

VERSION=$1
JDK8_URL=http://hg.openjdk.java.net

if test "x${VERSION}" = "x"; then
    echo "No version specified. A version is of the form 'jdk8-bXX' (such as 'jdk8-b79')"
    exit -1;
fi

#for REPO_NAME in jdk8 aarch64-port
for REPO_NAME in aarch64-port
do
    mkdir ${REPO_NAME}
    pushd ${REPO_NAME}

    REPO_ROOT=${JDK8_URL}/${REPO_NAME}/jdk8

    if [[ "$REPO_NAME" == "aarch64-port" ]] ; then
        # aarch64-port does not tag trees
        # FIXME make this clone reproducible
        hg clone ${REPO_ROOT} -r ${VERSION}
    else
        hg clone ${REPO_ROOT} -r ${VERSION}
    fi
    pushd jdk8

#    for subrepo in corba hotspot jdk jaxws jaxp langtools nashorn common
#    it looks like commons have been added as separate repo for jdk8
#    but not yet for aarch64-port
    for subrepo in corba hotspot jdk jaxws jaxp langtools nashorn
    do
        if [[ "$REPO_NAME" == "aarch64-port" ]] ; then
            # aarch64-port does not tag trees
            # FIXME make this clone reproducible
            hg clone ${REPO_ROOT}/${subrepo}
        else
            hg clone ${REPO_ROOT}/${subrepo} -r ${VERSION}
        fi
    done
    rm -rvf jdk/src/share/native/sun/security/ec/impl || echo ok

    popd

    find jdk8 -type d -name ".hg" -exec rm -rf '{}' \; || echo ok
    tar cJf ${REPO_NAME}-${VERSION}.tar.xz jdk8

    popd
done

