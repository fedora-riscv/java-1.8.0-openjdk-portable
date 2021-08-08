#!/bin/bash
# Generates the 'source tarball' for JDK 8 projects.
#
# Example:
# When used from local repo set REPO_ROOT pointing to file:// with your repo
# If your local repo follows upstream forests conventions, it may be enough to set OPENJDK_URL
# If you want to use a local copy of patch PR3822, set the path to it in the PR3822 variable
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

SCRIPT_DIR=$(dirname $0)
JCONSOLE_JS_PATCH_DEFAULT=${SCRIPT_DIR}/jconsole-plugin.patch

if [ ! "x$PR3822" = "x" ] ; then
  if [ ! -f "$PR3822" ] ; then
    echo "You have specified PR3822 as $PR3822 but it does not exist. Exiting"
    exit 1
  fi
fi

if [ "x${JCONSOLE_JS_PATCH}" != "x" ] ; then
    if [ ! -f "${JCONSOLE_JS_PATCH}" ] ; then
	echo "You have specified the jconsole.js patch as ${JCONSOLE_JS_PATCH} but it does not exist. Exiting.";
	exit 2;
    fi
else
    JCONSOLE_JS_PATCH=${JCONSOLE_JS_PATCH_DEFAULT}
fi

set -e

OPENJDK_URL_DEFAULT=http://hg.openjdk.java.net
COMPRESSION_DEFAULT=xz
# jdk is last for its size
REPOS_DEFAULT="hotspot corba jaxws jaxp langtools nashorn jdk"

if [ "x$1" = "xhelp" ] ; then
    echo -e "Behaviour may be specified by setting the following variables:\n"
    echo "VERSION - the version of the specified OpenJDK project"
    echo "PROJECT_NAME -- the name of the OpenJDK project being archived (optional; only needed by defaults)"
    echo "REPO_NAME - the name of the OpenJDK repository (optional; only needed by defaults)"
    echo "OPENJDK_URL - the URL to retrieve code from (optional; defaults to ${OPENJDK_URL_DEFAULT})"
    echo "COMPRESSION - the compression type to use (optional; defaults to ${COMPRESSION_DEFAULT})"
    echo "FILE_NAME_ROOT - name of the archive, minus extensions (optional; defaults to PROJECT_NAME-REPO_NAME-VERSION)"
    echo "REPO_ROOT - the location of the Mercurial repository to archive (optional; defaults to OPENJDK_URL/PROJECT_NAME/REPO_NAME)"
    echo "PR3822 - the path to the PR3822 patch to apply (optional; downloaded if unavailable)"
    echo "JCONSOLE_JS_PATCH - the path to a patch to fix non-availiability of jconsole.js (optional; defaults to ${JCONSOLE_JS_PATCH_DEFAULT})"
    echo "REPOS - specify the repositories to use (optional; defaults to ${REPOS_DEFAULT})"
    exit 1;
fi


if [ "x$VERSION" = "x" ] ; then
    echo "No VERSION specified"
    exit -2
fi
echo "Version: ${VERSION}"
    
# REPO_NAME is only needed when we default on REPO_ROOT and FILE_NAME_ROOT
if [ "x$FILE_NAME_ROOT" = "x" -o "x$REPO_ROOT" = "x" ] ; then
    if [ "x$PROJECT_NAME" = "x" ] ; then
	echo "No PROJECT_NAME specified"
	exit -1
    fi
    echo "Project name: ${PROJECT_NAME}"
    if [ "x$REPO_NAME" = "x" ] ; then
	echo "No REPO_NAME specified"
	exit -3
    fi
    echo "Repository name: ${REPO_NAME}"
fi

if [ "x$OPENJDK_URL" = "x" ] ; then
    OPENJDK_URL=${OPENJDK_URL_DEFAULT}
    echo "No OpenJDK URL specified; defaulting to ${OPENJDK_URL}"
else
    echo "OpenJDK URL: ${OPENJDK_URL}"
fi

if [ "x$COMPRESSION" = "x" ] ; then
# rhel 5 needs tar.gz
    COMPRESSION=${COMPRESSION_DEFAULT}
fi
echo "Creating a tar.${COMPRESSION} archive"

if [ "x$FILE_NAME_ROOT" = "x" ] ; then
    FILE_NAME_ROOT=${PROJECT_NAME}-${REPO_NAME}-${VERSION}
    echo "No file name root specified; default to ${FILE_NAME_ROOT}"
fi
if [ "x$REPO_ROOT" = "x" ] ; then
    REPO_ROOT="${OPENJDK_URL}/${PROJECT_NAME}/${REPO_NAME}"
    echo "No repository root specified; default to ${REPO_ROOT}"
fi;
if [ "x$REPOS" = "x" ] ; then
    REPOS=${REPOS_DEFAULT}
    echo "No repositories specified; defaulting to ${REPOS}"
fi;

echo -e "Settings:"
echo -e "\tVERSION: ${VERSION}"
echo -e "\tPROJECT_NAME: ${PROJECT_NAME}"
echo -e "\tREPO_NAME: ${REPO_NAME}"
echo -e "\tOPENJDK_URL: ${OPENJDK_URL}"
echo -e "\tCOMPRESSION: ${COMPRESSION}"
echo -e "\tFILE_NAME_ROOT: ${FILE_NAME_ROOT}"
echo -e "\tREPO_ROOT: ${REPO_ROOT}"
echo -e "\tPR3822: ${PR3822}"
echo -e "\tJCONSOLE_JS_PATCH: ${JCONSOLE_JS_PATCH}"
echo -e "\tREPOS: ${REPOS}"

mkdir "${FILE_NAME_ROOT}"
pushd "${FILE_NAME_ROOT}"

echo "Cloning ${VERSION} root repository from ${REPO_ROOT}"
hg clone ${REPO_ROOT} openjdk -r ${VERSION}
pushd openjdk
	
for subrepo in ${REPOS}
do
    echo "Cloning ${VERSION} ${subrepo} repository from ${REPO_ROOT}"
    hg clone ${REPO_ROOT}/${subrepo} -r ${VERSION}
done

# UnderlineTaglet.java has a BSD license with a field-of-use restriction, making it non-Free
if [ -d langtools ] ; then
    echo "Removing langtools test case with non-Free license"
    rm -vf langtools/test/tools/javadoc/api/basic/TagletPathTest.java
    rm -vf langtools/test/tools/javadoc/api/basic/taglets/UnderlineTaglet.java
fi
if [ -d jdk ]; then
# jconsole.js has a BSD license with a field-of-use restriction, making it non-Free
echo "Removing jconsole-plugin file with non-Free license"
rm -vf jdk/src/share/demo/scripting/jconsole-plugin/src/resources/jconsole.js
echo "Removing EC source code we don't build"
rm -vf jdk/src/share/native/sun/security/ec/impl/ec2.h
rm -vf jdk/src/share/native/sun/security/ec/impl/ec2_163.c
rm -vf jdk/src/share/native/sun/security/ec/impl/ec2_193.c
rm -vf jdk/src/share/native/sun/security/ec/impl/ec2_233.c
rm -vf jdk/src/share/native/sun/security/ec/impl/ec2_aff.c
rm -vf jdk/src/share/native/sun/security/ec/impl/ec2_mont.c
rm -vf jdk/src/share/native/sun/security/ec/impl/ecp_192.c
rm -vf jdk/src/share/native/sun/security/ec/impl/ecp_224.c

echo "Syncing EC list with NSS"
if [ "x$PR3822" = "x" ] ; then
# get pr3822.patch (from http://icedtea.classpath.org/hg/icedtea8) from most correct tag
# Do not push it or publish it (see http://icedtea.classpath.org/bugzilla/show_bug.cgi?id=3822)
    wget -O pr3822.patch http://icedtea.classpath.org/hg/icedtea8/raw-file/tip/patches/pr3822-4curve.patch
    patch -Np1 < pr3822.patch
    rm pr3822.patch
else
    echo "Applying ${PR3822}"
    patch -Np1 < $PR3822
fi;
fi

echo "Patching out use of jconsole.js"
patch -Np1 < ${JCONSOLE_JS_PATCH}

find . -name '*.orig' -exec rm -vf '{}' ';'

popd
echo "Compressing remaining forest"
if [ "X$COMPRESSION" = "Xxz" ] ; then
    SWITCH=cJf
else
    SWITCH=czf
fi
TARBALL_NAME=${FILE_NAME_ROOT}-4curve-clean.tar.${COMPRESSION}
tar --exclude-vcs -$SWITCH ${TARBALL_NAME} openjdk
mv ${TARBALL_NAME} ..

popd
echo "Done. You may want to remove the uncompressed version."


