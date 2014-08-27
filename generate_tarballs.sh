#!/bin/bash

VERSION=3506c375241e
ICEDTEA_URL=http://icedtea.classpath.org/hg/icedtea7/

wget -O icedtea7.tar.gz ${ICEDTEA_URL}/archive/${VERSION}.tar.gz
tar xzf icedtea7.tar.gz
rm -f icedtea7.tar.gz
pushd icedtea7-${VERSION}

# desktop files
#mv jconsole.desktop ../jconsole.desktop.in
#mv policytool.desktop ../policytool.desktop.in
# Icons were generally cloned fromicedtea, but now are mucvh more specific

# tapsets
mv tapset/hotspot{,-1.8.0}.stp.in || exit 1
mv tapset/hotspot_gc{,-1.8.0}.stp.in || exit 1
mv tapset/hotspot_jni{,-1.8.0}.stp.in || exit 1
mv tapset/jstack{,-1.8.0}.stp.in || exit 1
tar cvzf systemtap-tapset.tar.gz tapset
mv systemtap-tapset.tar.gz ../

popd
rm -rf icedtea7-${VERSION}
