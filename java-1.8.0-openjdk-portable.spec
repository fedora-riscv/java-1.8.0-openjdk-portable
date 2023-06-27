# RPM conditionals so as to be able to dynamically produce
# slowdebug/release builds. See:
# http://rpm.org/user_doc/conditional_builds.html
#
# Examples:
#
# Produce release, fastdebug *and* slowdebug builds on x86_64 (default):
# $ rpmbuild -ba java-1.8.0-openjdk.spec
#
# Produce only release builds (no slowdebug builds) on x86_64:
# $ rpmbuild -ba java-1.8.0-openjdk.spec --without slowdebug --without fastdebug
#
# Only produce a release build on x86_64:
# $ fedpkg mockbuild --without slowdebug --without fastdebug
#
# Only produce a debug build on x86_64:
# $ fedpkg local --without release
#
# Enable fastdebug builds by default on relevant arches.
%bcond_without fastdebug
# Enable slowdebug builds by default on relevant arches.
%bcond_without slowdebug
# Enable release builds by default on relevant arches.
%bcond_without release
# Remove build artifacts by default
%bcond_with artifacts
# Build a fresh libjvm.so for use in a copy of the bootstrap JDK
%bcond_without fresh_libjvm
# Build with system libraries
%bcond_without system_libs

%global unpacked_licenses %{_datarootdir}/licenses
%define  debug_package %{nil}

# Define whether to use the bootstrap JDK directly or with a fresh libjvm.so
%if %{with fresh_libjvm}
%global build_hotspot_first 1
%else
%global build_hotspot_first 0
%endif

%global is_system_jdk 0

# The -g flag says to use strip -g instead of full strip on DSOs or EXEs.
# This fixes detailed NMT and other tools which need minimal debug info.
# See: https://bugzilla.redhat.com/show_bug.cgi?id=1520879
%global _find_debuginfo_opts -g

# note: parametrized macros are order-sensitive (unlike not-parametrized) even with normal macros
# also necessary when passing it as parameter to other macros. If not macro, then it is considered a switch
# see the difference between global and define:
# See https://github.com/rpm-software-management/rpm/issues/127 to comments at  "pmatilai commented on Aug 18, 2017"
# (initiated in https://bugzilla.redhat.com/show_bug.cgi?id=1482192)
%global debug_suffix_unquoted -slowdebug
%global fastdebug_suffix_unquoted -fastdebug
# quoted one for shell operations
%global debug_suffix "%{debug_suffix_unquoted}"
%global fastdebug_suffix "%{fastdebug_suffix_unquoted}"
%global normal_suffix ""

%global debug_warning This package is unoptimised with full debugging. Install only as needed and remove ASAP.
%global fastdebug_warning This package is optimised with full debugging. Install only as needed and remove ASAP.
%global debug_on unoptimised with full debugging on
%global fastdebug_on optimised with full debugging on
%global for_fastdebug for packages with debugging on and optimisation
%global for_debug for packages with debugging on and no optimisation

%if %{with release}
%global include_normal_build 1
%else
%global include_normal_build 0
%endif

%if %{include_normal_build}
%global normal_build %{normal_suffix}
%else
%global normal_build %{nil}
%endif

%global aarch64         aarch64 arm64 armv8
# we need to distinguish between big and little endian PPC64
%global ppc64le         ppc64le
%global ppc64be         ppc64 ppc64p7
# Set of architectures which support multiple ABIs
%global multilib_arches %{power64} sparc64 x86_64
# Set of architectures for which we build slowdebug builds
%global debug_arches    %{ix86} x86_64 sparcv9 sparc64 %{aarch64} %{power64}
# Set of architectures for which we build fastdebug builds
%global fastdebug_arches x86_64 ppc64le aarch64
# Set of architectures with a Just-In-Time (JIT) compiler
%global jit_arches      %{aarch64} %{ix86} %{power64} sparcv9 sparc64 x86_64
# Set of architectures which use the Zero assembler port (!jit_arches)
%global zero_arches %{arm} ppc s390 s390x
# Set of architectures which run a full bootstrap cycle
%global bootstrap_arches %{jit_arches} %{zero_arches}
# Set of architectures which support SystemTap tapsets
%global systemtap_arches %{jit_arches}
# Set of architectures which support the serviceability agent
%global sa_arches       %{ix86} x86_64 sparcv9 sparc64 %{aarch64}
# Set of architectures which support class data sharing
# See https://bugzilla.redhat.com/show_bug.cgi?id=513605
# MetaspaceShared::generate_vtable_methods is not implemented for the PPC JIT
%global share_arches    %{ix86} x86_64 sparcv9 sparc64 %{aarch64}
# Set of architectures which support JFR
%global jfr_arches      %{jit_arches}
# Set of architectures for which alt-java has SSB mitigation
%global ssbd_arches x86_64
# Set of architectures where we verify backtraces with gdb
%global gdb_arches %{jit_arches} %{zero_arches}

# By default, we build a debug build during main build on JIT architectures
%if %{with slowdebug}
%ifarch %{debug_arches}
%global include_debug_build 1
%else
%global include_debug_build 0
%endif
%else
%global include_debug_build 0
%endif

# By default, we build a fastdebug build during main build only on fastdebug architectures
%if %{with fastdebug}
%ifarch %{fastdebug_arches}
%global include_fastdebug_build 1
%else
%global include_fastdebug_build 0
%endif
%else
%global include_fastdebug_build 0
%endif

%if %{include_debug_build}
%global slowdebug_build %{debug_suffix}
%else
%global slowdebug_build %{nil}
%endif

%if %{include_fastdebug_build}
%global fastdebug_build %{fastdebug_suffix}
%else
%global fastdebug_build %{nil}
%endif

# If you disable all builds, then the build fails
# Build and test slowdebug first as it provides the best diagnostics
%global build_loop  %{slowdebug_build} %{fastdebug_build} %{normal_build}

%if 0%{?flatpak}
%global bootstrap_build false
%else
%ifarch %{bootstrap_arches}
%global bootstrap_build true
%else
%global bootstrap_build false
%endif
%endif

%global bootstrap_targets images
%global release_targets images docs-zip
%global debug_targets images
# Target to use to just build HotSpot
%global hotspot_target hotspot

# JDK to use for bootstrapping
# Use OpenJDK 7 where available (on RHEL) to avoid
# having to use the rhel-7.x-java-unsafe-candidate hack
%if ! 0%{?fedora} && 0%{?rhel} <= 7
%global buildjdkver 1.7.0
%else
%global buildjdkver 1.8.0
%endif
%global bootjdk /usr/lib/jvm/java-%{buildjdkver}-openjdk

# Disable LTO as this causes build failures at the moment.
# See RHBZ#1861401
%define _lto_cflags %{nil}

# Filter out flags from the optflags macro that cause problems with the OpenJDK build
# We filter out -O flags so that the optimization of HotSpot is not lowered from O3 to O2
# We filter out -Wall which will otherwise cause HotSpot to produce hundreds of thousands of warnings (100+mb logs)
# We replace it with -Wformat (required by -Werror=format-security) and -Wno-cpp to avoid FORTIFY_SOURCE warnings
# We filter out -fexceptions as the HotSpot build explicitly does -fno-exceptions and it's otherwise the default for C++
%global ourflags %(echo %optflags | sed -e 's|-Wall|-Wformat -Wno-cpp|' | sed -r -e 's|-O[0-9]*||' | sed -e 's|-g ||')
%global ourcppflags %(echo %ourflags | sed -e 's|-fexceptions||' | sed -e 's|-fasynchronous-unwind-tables||' | sed -e 's|-g ||')
%global ourldflags %{nil}

# With disabled nss is NSS deactivated, so NSS_LIBDIR can contain the wrong path
# the initialization must be here. Later the pkg-config have buggy behavior
# looks like openjdk RPM specific bug
# Always set this so the nss.cfg file is not broken
%global NSS_LIBDIR %(pkg-config --variable=libdir nss)
%global NSS_LIBS %(pkg-config --libs nss)
%global NSS_CFLAGS %(pkg-config --cflags nss-softokn)
# see https://bugzilla.redhat.com/show_bug.cgi?id=1332456
%global NSSSOFTOKN_BUILDTIME_NUMBER %(pkg-config --modversion nss-softokn || : )
%global NSS_BUILDTIME_NUMBER %(pkg-config --modversion nss || : )
# this is workaround for processing of requires during srpm creation
%global NSSSOFTOKN_BUILDTIME_VERSION %(if [ "x%{NSSSOFTOKN_BUILDTIME_NUMBER}" == "x" ] ; then echo "" ;else echo ">= %{NSSSOFTOKN_BUILDTIME_NUMBER}" ;fi)
%global NSS_BUILDTIME_VERSION %(if [ "x%{NSS_BUILDTIME_NUMBER}" == "x" ] ; then echo "" ;else echo ">= %{NSS_BUILDTIME_NUMBER}" ;fi)

# In some cases, the arch used by the JDK does
# not match _arch.
# Also, in some cases, the machine name used by SystemTap
# does not match that given by _target_cpu
%ifarch x86_64
%global archinstall amd64
%global stapinstall x86_64
%endif
%ifarch ppc
%global archinstall ppc
%global stapinstall powerpc
%endif
%ifarch %{ppc64be}
%global archinstall ppc64
%global stapinstall powerpc
%endif
%ifarch %{ppc64le}
%global archinstall ppc64le
%global stapinstall powerpc
%endif
%ifarch %{ix86}
%global archinstall i386
%global stapinstall i386
%endif
%ifarch ia64
%global archinstall ia64
%global stapinstall ia64
%endif
%ifarch s390
%global archinstall s390
%global stapinstall s390
%endif
%ifarch s390x
%global archinstall s390x
%global stapinstall s390
%endif
%ifarch %{arm}
%global archinstall arm
%global stapinstall arm
%endif
%ifarch %{aarch64}
%global archinstall aarch64
%global stapinstall arm64
%endif
# 32 bit sparc, optimized for v9
%ifarch sparcv9
%global archinstall sparc
%global stapinstall %{_target_cpu}
%endif
# 64 bit sparc
%ifarch sparc64
%global archinstall sparcv9
%global stapinstall %{_target_cpu}
%endif
# Need to support noarch for srpm build
%ifarch noarch
%global archinstall %{nil}
%global stapinstall %{nil}
%endif

# Always off in portables
%ifarch %{systemtap_arches}
%global with_systemtap 0
%else
%global with_systemtap 0
%endif

# New Version-String scheme-style defines
%global majorver 8


# Standard JPackage naming and versioning defines
%global origin          openjdk
%global origin_nice     OpenJDK
%global top_level_dir_name   %{origin}

# Settings for local security configuration
%global security_file %{top_level_dir_name}/jdk/src/share/lib/security/java.security-%{_target_os}
%global cacerts_file /etc/pki/java/cacerts

# Define vendor information used by OpenJDK
%global oj_vendor Red Hat, Inc.
%global oj_vendor_url "https://www.redhat.com/"
# Define what url should JVM offer in case of a crash report
# order may be important, epel may have rhel declared
%if 0%{?epel}
%global oj_vendor_bug_url  https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora%20EPEL&component=%{component}&version=epel%{epel}
%else
%if 0%{?fedora}
# Does not work for rawhide, keeps the version field empty
%global oj_vendor_bug_url  https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora&component=%{component}&version=%{fedora}
%else
%if 0%{?rhel}
%global oj_vendor_bug_url  https://bugzilla.redhat.com/enter_bug.cgi?product=Red%20Hat%20Enterprise%20Linux%20%{rhel}&component=%{component}
%else
%global oj_vendor_bug_url  https://bugzilla.redhat.com/enter_bug.cgi
%endif
%endif
%endif

# note, following three variables are sedded from update_sources if used correctly. Hardcode them rather there.
%global shenandoah_project      openjdk
%global shenandoah_repo         shenandoah-jdk8u
%global openjdk_revision        jdk8u372-b07
%global shenandoah_revision     shenandoah-%{openjdk_revision}
# Define old aarch64/jdk8u tree variables for compatibility
%global project         %{shenandoah_project}
%global repo            %{shenandoah_repo}
%global revision        %{shenandoah_revision}
# Define IcedTea version used for SystemTap tapsets and desktop file
%global icedteaver      3.15.0
# Define current Git revision for the FIPS support patches
%global fipsver 6d1aade0648
# Define current Git revision for the cacerts patch
%global cacertsver 8139f2361c2

# e.g. aarch64-shenandoah-jdk8u212-b04-shenandoah-merge-2019-04-30 -> aarch64-shenandoah-jdk8u212-b04
%global version_tag     %(VERSION=%{revision}; echo ${VERSION%%-shenandoah-merge*})
# eg # jdk8u60-b27 -> jdk8u60 or # aarch64-jdk8u60-b27 -> aarch64-jdk8u60  (dont forget spec escape % by %%)
%global whole_update    %(VERSION=%{version_tag}; echo ${VERSION%%-*})
# eg  jdk8u60 -> 60 or aarch64-jdk8u60 -> 60
%global updatever       %(VERSION=%{whole_update}; echo ${VERSION##*u})
# eg jdk8u60-b27 -> b27
%global buildver        %(VERSION=%{version_tag}; echo ${VERSION##*-})
%global rpmrelease      5
# Define milestone (EA for pre-releases, GA ("fcs") for releases)
# Release will be (where N is usually a number starting at 1):
# - 0.N%%{?extraver}%%{?dist} for EA releases,
# - N%%{?extraver}{?dist} for GA releases
%global is_ga           1
%if %{is_ga}
%global milestone          fcs
%global milestone_version  %{nil}
%global extraver %{nil}
%global eaprefix %{nil}
%else
%global milestone          ea
%global milestone_version  "-ea"
%global extraver .%{milestone}
%global eaprefix 0.
%endif
# priority must be 7 digits in total; up to openjdk 1.8
%if %is_system_jdk
%global priority        1800%{updatever}
%else
# for techpreview, using 1, so slowdebugs can have 0
%global priority        0000001
%endif

%global javaver         1.%{majorver}.0

# parametrized macros are order-sensitive
%global compatiblename  %{name}
%global fullversion     %{compatiblename}-%{version}-%{release}
# images directories from upstream build
%global jdkimage       j2sdk-image
%global jreimage       j2re-image
# output dir stub
%define buildoutputdir() %{expand:build/jdk8.build%{?1}}
%define installoutputdir() %{expand:install/jdk8.install%{?1}}
# we can copy the javadoc to not arched dir, or make it not noarch
%define uniquejavadocdir()    %{expand:%{fullversion}%{?1}}
# main id and dir of this jdk
%define uniquesuffix()        %{expand:%{fullversion}.%{_arch}%{?1}}
%if (0%{?rhel} > 0 && 0%{?rhel} < 8)
%define jreportablenameimpl() %(echo %{uniquesuffix ""} | sed "s;el7\\(_[0-9]\\)*;portable%{1}.jre.;g" | sed "s;openjdkportable;el;g")
%define jdkportablenameimpl() %(echo %{uniquesuffix ""} | sed "s;el7\\(_[0-9]\\)*;portable%{1}.jdk.;g" | sed "s;openjdkportable;el;g")
%define jdkportablesourcesnameimpl() %(echo %{uniquesuffix ""} | sed "s;el7\\(_[0-9]\\)*;portable%{1}.sources.;g" | sed "s;openjdkportable;el;g" | sed "s;.%{_arch};.noarch;g")
%else
%define jreportablenameimpl() %(echo %{uniquesuffix ""} | sed "s;fc\\([0-9]\\)*;\\0.portable%{1}.jre;g" | sed "s;openjdkportable;el;g")
%define jdkportablenameimpl() %(echo %{uniquesuffix ""} | sed "s;fc\\([0-9]\\)*;\\0.portable%{1}.jdk;g" | sed "s;openjdkportable;el;g")
%define jdkportablesourcesnameimpl() %(echo %{uniquesuffix ""} | sed "s;fc\\([0-9]\\)*;\\0.portable%{1}.sources;g" | sed "s;openjdkportable;el;g" | sed "s;.%{_arch};.noarch;g")
%endif
%define jreportablearchive()  %{expand:%{jreportablenameimpl -- %%{1}}.tar.xz}
%define jdkportablearchive()  %{expand:%{jdkportablenameimpl -- %%{1}}.tar.xz}
%define jdkportablesourcesarchive()  %{expand:%{jdkportablesourcesnameimpl -- %%{1}}.tar.xz}
%define jreportablename()     %{expand:%{jreportablenameimpl -- %%{1}}}
%define jdkportablename()     %{expand:%{jdkportablenameimpl -- %%{1}}}
%define jdkportablesourcesname()     %{expand:%{jdkportablesourcesnameimpl -- %%{1}}}

# RPM 4.19 no longer accept our double percentaged %%{nil} passed to %%{1}
# so we have to pass in "" but evaluate it, otherwise files record will include it
%define jreportablearchiveForFiles()  %(echo %{jreportablearchive -- ""})
%define jdkportablearchiveForFiles()  %(echo %{jdkportablearchive -- ""})
%define jdkportablesourcesarchiveForFiles()  %(echo %{jdkportablesourcesarchive -- ""})

#################################################################
# fix for https://bugzilla.redhat.com/show_bug.cgi?id=1111349
#         https://bugzilla.redhat.com/show_bug.cgi?id=1590796#c14
#         https://bugzilla.redhat.com/show_bug.cgi?id=1655938
%global _privatelibs libattach[.]so.*|libawt_headless[.]so.*|libawt[.]so.*|libawt_xawt[.]so.*|libdt_socket[.]so.*|libfontmanager[.]so.*|libhprof[.]so.*|libinstrument[.]so.*|libj2gss[.]so.*|libj2pcsc[.]so.*|libj2pkcs11[.]so.*|libjaas_unix[.]so.*|libjava_crw_demo[.]so.*|libjdwp[.]so.*|libjli[.]so.*|libjsdt[.]so.*|libjsoundalsa[.]so.*|libjsound[.]so.*|liblcms[.]so.*|libmanagement[.]so.*|libmlib_image[.]so.*|libnet[.]so.*|libnio[.]so.*|libnpt[.]so.*|libsaproc[.]so.*|libsctp[.]so.*|libsplashscreen[.]so.*|libsunec[.]so.*|libsystemconf[.]so.*|libunpack[.]so.*|libzip[.]so.*|lib[.]so\\(SUNWprivate_.*
%global _publiclibs libjawt[.]so.*|libjava[.]so.*|libjvm[.]so.*|libverify[.]so.*|libjsig[.]so.*

%global __provides_exclude ^(%{_privatelibs})$
%global __requires_exclude ^(%{_privatelibs})$


%global etcjavasubdir     %{_sysconfdir}/java/java-%{javaver}-%{origin}
%define etcjavadir()      %{expand:%{etcjavasubdir}/%{uniquesuffix -- %{?1}}}
# Standard JPackage directories and symbolic links.
%global sdkdir()        %{expand:%{uniquesuffix -- %{?1}}}
%global jrelnk()        %{expand:jre-%{javaver}-%{origin}-%{version}-%{release}.%{_arch}%1}

%global jredir()        %{expand:%{sdkdir -- %{?1}}/jre}
%global sdkbindir()     %{expand:%{_jvmdir}/%{sdkdir -- %{?1}}/bin}
%global jrebindir()     %{expand:%{_jvmdir}/%{jredir -- %{?1}}/bin}
%global alt_java_name     alt-java
%global jvmjardir()     %{expand:%{_jvmjardir}/%{uniquesuffix %%1}}

%global rpm_state_dir %{_localstatedir}/lib/rpm-state/

# For flatpack builds hard-code /usr/sbin/alternatives,
# otherwise use %%{_sbindir} relative path.
%if 0%{?flatpak}
%global alternatives_requires /usr/sbin/alternatives
%else
%global alternatives_requires %{_sbindir}/alternatives
%endif

%global family %{name}.%{_arch}
%global family_noarch  %{name}

%if %{with_systemtap}
# Where to install systemtap tapset (links)
# We would like these to be in a package specific sub-dir,
# but currently systemtap doesn't support that, so we have to
# use the root tapset dir for now. To distinguish between 64
# and 32 bit architectures we place the tapsets under the arch
# specific dir (note that systemtap will only pickup the tapset
# for the primary arch for now). Systemtap uses the machine name
# aka target_cpu as architecture specific directory name.
%global tapsetroot /usr/share/systemtap
%global tapsetdirttapset %{tapsetroot}/tapset/
%global tapsetdir %{tapsetdirttapset}/%{stapinstall}
%endif

# x86 is no longer supported
%if 0%{?java_arches:1}
ExclusiveArch:  %{java_arches}
%else
ExcludeArch: %{ix86}
%endif

%global __jar_repack 0

# portables have grown out of its component, moving back to java-x-vendor
# this expression, when declared as global, filled component with java-x-vendor portable
%define component %(echo %{name} | sed "s;-portable;;g")

Name:    java-%{javaver}-%{origin}-portable
Version: %{javaver}.%{updatever}.%{buildver}
Release: %{?eaprefix}%{rpmrelease}%{?extraver}%{?dist}
# java-1.5.0-ibm from jpackage.org set Epoch to 1 for unknown reasons
# and this change was brought into RHEL-4. java-1.5.0-ibm packages
# also included the epoch in their virtual provides. This created a
# situation where in-the-wild java-1.5.0-ibm packages provided "java =
# 1:1.5.0". In RPM terms, "1.6.0 < 1:1.5.0" since 1.6.0 is
# interpreted as 0:1.6.0. So the "java >= 1.6.0" requirement would be
# satisfied by the 1:1.5.0 packages. Thus we need to set the epoch in
# JDK package >= 1.6.0 to 1, and packages referring to JDK virtual
# provides >= 1.6.0 must specify the epoch, "java >= 1:1.6.0".

Epoch:   1
Summary: %{origin_nice} %{majorver} Runtime Environment portable edition
Group:   Development/Languages

# HotSpot code is licensed under GPLv2
# JDK library code is licensed under GPLv2 with the Classpath exception
# The Apache license is used in code taken from Apache projects (primarily JAXP & JAXWS)
# DOM levels 2 & 3 and the XML digital signature schemas are licensed under the W3C Software License
# The JSR166 concurrency code is in the public domain
# The BSD and MIT licenses are used for a number of third-party libraries (see THIRD_PARTY_README)
# The OpenJDK source tree includes the JPEG library (IJG), zlib & libpng (zlib), giflib and LCMS (MIT)
# The test code includes copies of NSS under the Mozilla Public License v2.0
# The PCSClite headers are under a BSD with advertising license
# The elliptic curve cryptography (ECC) source code is licensed under the LGPLv2.1 or any later version
License:  ASL 1.1 and ASL 2.0 and BSD and BSD with advertising and GPL+ and GPLv2 and GPLv2 with exceptions and IJG and LGPLv2+ and MIT and MPLv2.0 and Public Domain and W3C and zlib
URL:      http://openjdk.java.net/

# Shenandoah HotSpot
# aarch64-port/jdk8u-shenandoah contains an integration forest of
# OpenJDK 8u, the aarch64 port and Shenandoah
# To regenerate, use:
# VERSION=%%{shenandoah_revision}
# FILE_NAME_ROOT=%%{shenandoah_project}-%%{shenandoah_repo}-${VERSION}
# REPO_ROOT=<path to checked-out repository> generate_source_tarball.sh
# where the source is obtained from http://hg.openjdk.java.net/%%{project}/%%{repo}
Source0: %{shenandoah_project}-%{shenandoah_repo}-%{shenandoah_revision}-4curve.tar.xz

# Custom README for -src subpackage
Source2:  README.md

# Release notes
Source7: NEWS

# Use 'icedtea_sync.sh' to update the following
# They are based on code contained in the IcedTea project (3.x).
# Systemtap tapsets. Zipped up to keep it small.
# Disabled in portables
#Source8: tapsets-icedtea-%%{icedteaver}.tar.xz

# Desktop files. Adapted from IcedTea
# Disabled in portables
#Source9: jconsole.desktop.in
#Source10: policytool.desktop.in

# nss configuration file
Source11: nss.cfg.in

# Removed libraries that we link instead
# Disabled in portables
#Source12: %%{name}-remove-intree-libraries.sh

# Ensure we aren't using the limited crypto policy
Source13: TestCryptoLevel.java

# Ensure ECDSA is working
Source14: TestECDSA.java

# Verify system crypto (policy) can be disabled via a property
Source15: TestSecurityProperties.java

# Ensure vendor settings are correct
Source16: CheckVendor.java

# nss fips configuration file
Source17: nss.fips.cfg.in

# Ensure translations are available for new timezones
Source18: TestTranslations.java

# Disabled in portables
#Source20: repackReproduciblePolycies.sh

# New versions of config files with aarch64 support. This is not upstream yet.
Source100: config.guess
Source101: config.sub

############################################
#
# RPM/distribution specific patches
#
# This section includes patches specific to
# Fedora/RHEL which can not be upstreamed
# either in their current form or at all.
############################################

# Turn on AssumeMP by default on RHEL systems
Patch534: rh1648246-always_instruct_vm_to_assume_multiple_processors_are_available.patch
# RH1582504: Use RSA as default for keytool, as DSA is disabled in all crypto policies except LEGACY
Patch1003: rh1582504-rsa_default_for_keytool.patch
# RH1648249: Add PKCS11 provider to java.security
Patch1000: rh1648249-add_commented_out_nss_cfg_provider_to_java_security.patch

# Crypto policy and FIPS support patches
# Patch is generated from the fips tree at https://github.com/rh-openjdk/jdk8u/tree/fips
# as follows: git diff %%{openjdk_revision} common jdk > fips-8u-$(git show -s --format=%h HEAD).patch
# Diff is limited to src and make subdirectories to exclude .github changes
# Fixes currently included:
# PR3183, RH1340845: Support Fedora/RHEL8 system crypto policy
# PR3655: Allow use of system crypto policy to be disabled by the user
# RH1655466: Support RHEL FIPS mode using SunPKCS11 provider
# RH1760838: No ciphersuites available for SSLSocket in FIPS mode
# RH1860986: Disable TLSv1.3 with the NSS-FIPS provider until PKCS#11 v3.0 support is available
# RH1906862: Always initialise JavaSecuritySystemConfiguratorAccess
# RH1929465: Improve system FIPS detection
# RH1996182: Login to the NSS software token in FIPS mode
# RH1991003: Allow plain key import unless com.redhat.fips.plainKeySupport is set to false
# RH2021263: Resolve outstanding FIPS issues
# RH2052819: Fix FIPS reliance on crypto policies
# RH2051605: Detect NSS at Runtime for FIPS detection
# RH2036462: sun.security.pkcs11.wrapper.PKCS11.getInstance breakage
# RH2090378: Revert to disabling system security properties and FIPS mode support together
Patch1001: fips-8u-%{fipsver}.patch

#############################################
#
# Upstreamable patches
#
# This section includes patches which need to
# be reviewed & pushed to the current development
# tree of OpenJDK.
#############################################
# PR2737: Allow multiple initialization of PKCS11 libraries
Patch5: pr2737-allow_multiple_pkcs11_library_initialisation_to_be_a_non_critical_error.patch
# Turn off strict overflow on IndicRearrangementProcessor{,2}.cpp following 8140543: Arrange font actions
Patch512: rh1649664-awt2dlibraries_compiled_with_no_strict_overflow.patch
# RH1337583, PR2974: PKCS#10 certificate requests now use CRLF line endings rather than system line endings
Patch523: pr2974-rh1337583-add_systemlineendings_option_to_keytool_and_use_line_separator_instead_of_crlf_in_pkcs10.patch
# PR3083, RH1346460: Regression in SSL debug output without an ECC provider
Patch528: pr3083-rh1346460-for_ssl_debug_return_null_instead_of_exception_when_theres_no_ecc_provider.patch
# PR2888: OpenJDK should check for system cacerts database (e.g. /etc/pki/java/cacerts)
# PR3575, RH1567204: System cacerts database handling should not affect jssecacerts
Patch539: pr2888-openjdk_should_check_for_system_cacerts_database_eg_etc_pki_java_cacerts.patch
# enable build of speculative store bypass hardened alt-java
Patch600: rh1750419-redhat_alt_java.patch
# JDK-8218811: replace open by os::open in hotspot coding
# This fixes a GCC 10 build issue
Patch111: jdk8218811-perfMemory_linux.patch
# JDK-8281098, PR3836: Extra compiler flags not passed to adlc build
Patch112: jdk8281098-pr3836-pass_compiler_flags_to_adlc.patch

#############################################
#
# Arch-specific upstreamable patches
#
# This section includes patches which need to
# be reviewed & pushed upstream and are specific
# to certain architectures. This usually means the
# current OpenJDK development branch, but may also
# include other trees e.g. for the AArch64 port for
# OpenJDK 8u.
#############################################
# s390: PR3593: Use "%z" for size_t on s390 as size_t != intptr_t
Patch103: pr3593-s390_use_z_format_specifier_for_size_t_arguments_as_size_t_not_equals_to_int.patch
# x86: S8199936, PR3533: HotSpot generates code with unaligned stack, crashes on SSE operations (-mstackrealign workaround)
Patch105: jdk8199936-pr3533-enable_mstackrealign_on_x86_linux_as_well_as_x86_mac_os_x.patch
# S390 ambiguous log2_intptr calls
Patch107: s390-8214206_fix.patch

#############################################
#
# Patches which need backporting to 8u
#
# This section includes patches which have
# been pushed upstream to the latest OpenJDK
# development tree, but need to be backported
# to OpenJDK 8u.
#############################################
# S8074839, PR2462: Resolve disabled warnings for libunpack and the unpack200 binary
# This fixes printf warnings that lead to build failure with -Werror=format-security from optflags
Patch502: pr2462-resolve_disabled_warnings_for_libunpack_and_the_unpack200_binary.patch
# PR3591: Fix for bug 3533 doesn't add -mstackrealign to JDK code
Patch571: jdk8199936-pr3591-enable_mstackrealign_on_x86_linux_as_well_as_x86_mac_os_x_jdk.patch
# 8143245, PR3548: Zero build requires disabled warnings
Patch574: jdk8143245-pr3548-zero_build_requires_disabled_warnings.patch
# s390: JDK-8203030, Type fixing for s390
Patch102: jdk8203030-zero_s390_31_bit_size_t_type_conflicts_in_shared_code.patch
# 8035341: Allow using a system installed libpng
Patch202: jdk8035341-allow_using_system_installed_libpng.patch
# 8042159: Allow using a system-installed lcms2
Patch203: jdk8042159-allow_using_system_installed_lcms2-root.patch
Patch204: jdk8042159-allow_using_system_installed_lcms2-jdk.patch
# JDK-8257794: Zero: assert(istate->_stack_limit == istate->_thread->last_Java_sp() + 1) failed: wrong on Linux/x86_32
Patch581: jdk8257794-remove_broken_assert.patch
# JDK-8282231: x86-32: runtime call to SharedRuntime::ldiv corrupts registers
Patch582: jdk8282231-x86_32-missing_call_effects.patch

#############################################
#
# Patches appearing in 8u382
#
# This section includes patches which are present
# in the listed OpenJDK 8u release and should be
# able to be removed once that release is out
# and used by this RPM.
#############################################
# JDK-8271199, RH2175317: Mutual TLS handshake fails signing client certificate with custom sensitive PKCS11 key
Patch2001: jdk8271199-rh2175317-custom_pkcs11_provider_support.patch

#############################################
#
# Patches ineligible for 8u
#
# This section includes patches which are present
# upstream, but ineligible for upstream 8u backport.
#############################################
# 8043805: Allow using a system-installed libjpeg
Patch201: jdk8043805-allow_using_system_installed_libjpeg.patch

#############################################
#
# Shenandoah fixes
#
# This section includes patches which are
# specific to the Shenandoah garbage collector
# and should be upstreamed to the appropriate
# trees.
#############################################

#############################################
#
# Non-OpenJDK fixes
#
# This section includes patches to code other
# that from OpenJDK.
#############################################

#############################################
#
# Dependencies
#
#############################################
BuildRequires: make
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: alsa-lib-devel
BuildRequires: binutils
BuildRequires: cups-devel
BuildRequires: desktop-file-utils
# elfutils only are OK for build without AOT
BuildRequires: elfutils-devel
BuildRequires: fontconfig-devel
BuildRequires: freetype-devel
BuildRequires: gcc-c++
BuildRequires: libstdc++-static
BuildRequires: gdb
BuildRequires: libxslt
BuildRequires: libX11-devel
BuildRequires: libXext-devel
BuildRequires: libXi-devel
BuildRequires: libXinerama-devel
BuildRequires: libXrender-devel
BuildRequires: libXt-devel
BuildRequires: libXtst-devel
# Requirement for setting up nss.cfg and nss.fips.cfg
BuildRequires: nss-devel
# Requirement for system security property test
#BuildRequires: crypto-policies
BuildRequires: pkgconfig
BuildRequires: xorg-x11-proto-devel
BuildRequires: zip
BuildRequires: tar
BuildRequires: unzip
# Require a boot JDK which doesn't fail due to RH1482244
BuildRequires: java-%{buildjdkver}-openjdk-devel >= 1.7.0.151-2.6.11.3
# Zero-assembler build requirement
%ifarch %{zero_arches}
BuildRequires: libffi-devel
%endif
# 2023c required as of JDK-8305113
BuildRequires: tzdata-java >= 2023c
# Earlier versions have a bug in tree vectorization on PPC
BuildRequires: gcc >= 4.8.3-8

# cacerts build requirement.
BuildRequires: ca-certificates
BuildRequires: openssl
%if %{with_systemtap}
BuildRequires: systemtap-sdt-devel
%endif


%description
The %{origin_nice} %{majorver} runtime environment - portable edition

%if %{include_normal_build}
%package devel
Summary: %{origin_nice} %{majorver} Development Environment portable edition
Group:   Development/Tools
%description devel
The %{origin_nice} %{majorver} development tools - portable edition
%endif

%if %{include_debug_build}
%package slowdebug
Summary: %{origin_nice} %{majorver} Runtime Environment portable edition %{debug_on}
Group:   Development/Languages
%description slowdebug
The %{origin_nice} %{majorver} runtime environment - portable edition
%{debug_warning}

%package devel-slowdebug
Summary: %{origin_nice} %{majorver} Development Environment portable edition %{debug_on}
Group:   Development/Tools
%description devel-slowdebug
The %{origin_nice} %{majorver} development tools - portable edition
%{debug_warning}
%endif

%if %{include_fastdebug_build}
%package fastdebug
Summary: %{origin_nice} %{majorver} Runtime Environment portable edition %{fastdebug_on}
Group:   Development/Languages
%description fastdebug
The %{origin_nice} %{majorver} runtime environment - portable edition
%{fastdebug_warning}

%package devel-fastdebug
Summary: %{origin_nice} %{majorver} Development Environment portable edition %{fastdebug_on}
Group:   Development/Tools
%description devel-fastdebug
The %{origin_nice} %{majorver} development tools - portable edition
%{fastdebug_warning}
%endif

%package sources
Summary: %{origin_nice} %{majorver} full patched sources of portable JDK

%description sources
The %{origin_nice} %{majorver} full patched sources of portable JDK to build, attach to debuggers or for debuginfo
%prep
if [ %{include_normal_build} -eq 0 -o  %{include_normal_build} -eq 1 ] ; then
  echo "include_normal_build is %{include_normal_build}"
else
  echo "include_normal_build is %{include_normal_build}, that is invalid. Use 1 for yes or 0 for no"
  exit 11
fi
if [ %{include_debug_build} -eq 0 -o  %{include_debug_build} -eq 1 ] ; then
  echo "include_debug_build is %{include_debug_build}"
else
  echo "include_debug_build is %{include_debug_build}, that is invalid. Use 1 for yes or 0 for no"
  exit 12
fi
if [ %{include_fastdebug_build} -eq 0 -o  %{include_fastdebug_build} -eq 1 ] ; then
  echo "include_fastdebug_build is %{include_fastdebug_build}"
else
  echo "include_fastdebug_build is %{include_fastdebug_build}, that is invalid. Use 1 for yes or 0 for no"
  exit 13
fi
if [ %{include_debug_build} -eq 0 -a  %{include_normal_build} -eq 0 -a  %{include_fastdebug_build} -eq 0 ] ; then
  echo "You have disabled all builds (normal,fastdebug,slowdebug). That is a no go."
  exit 14
fi

echo "Update version: %{updatever}"
echo "Build number: %{buildver}"
echo "Milestone: %{milestone}"
%setup -q -c -n %{uniquesuffix ""} -T -a 0
# https://bugzilla.redhat.com/show_bug.cgi?id=1189084
prioritylength=`expr length %{priority}`
if [ $prioritylength -ne 7 ] ; then
 echo "priority must be 7 digits in total, violated"
 exit 14
fi
# For old patches
ln -s %{top_level_dir_name} jdk8

cp %{SOURCE2} .

# replace outdated configure guess script
#
# the configure macro will do this too, but it also passes a few flags not
# supported by openjdk configure script
cp %{SOURCE100} %{top_level_dir_name}/common/autoconf/build-aux/
cp %{SOURCE101} %{top_level_dir_name}/common/autoconf/build-aux/

# OpenJDK patches

# portables uses in tree versions
# Remove libraries that are linked
#sh %{SOURCE12}

# Do not enable them, they do not work properly with bundled option
# System library fixes
#%patch201
#%patch202
#%patch203
#%patch204

%patch5

# s390 build fixes
%patch102
%patch103
%patch107

# AArch64 fixes

# x86 fixes
%patch105

# Upstreamable fixes
%patch502
%patch512
%patch523
%patch528
%patch571
%patch574
%patch111
%patch112
%patch581
%patch582

pushd %{top_level_dir_name}
# Add crypto policy and FIPS support
%patch1001 -p1
# nss.cfg PKCS11 support; must come last as it also alters java.security
%patch1000 -p1
# 8u382 fix
%patch2001 -p1
popd

# RPM-only fixes
%patch539
%patch600
%patch1003

# RHEL-only patches
%if ! 0%{?fedora} && 0%{?rhel} <= 7
%patch534
%endif

# Shenandoah patches

# Extract systemtap tapsets
%if %{with_systemtap}
tar --strip-components=1 -x -I xz -f %{SOURCE8}
%if %{include_debug_build}
cp -r tapset tapset%{debug_suffix}
%endif
%if %{include_fastdebug_build}
cp -r tapset tapset%{fastdebug_suffix}
%endif


for suffix in %{build_loop} ; do
  for file in "tapset"$suffix/*.in; do
    OUTPUT_FILE=`echo $file | sed -e "s:\.stp\.in$:-%{version}-%{release}.%{_arch}.stp:g"`
    sed -e "s:@ABS_SERVER_LIBJVM_SO@:%{_jvmdir}/%{sdkdir -- $suffix}/jre/lib/%{archinstall}/server/libjvm.so:g" $file > $file.1
# TODO find out which architectures other than i686 have a client vm
%ifarch %{ix86}
    sed -e "s:@ABS_CLIENT_LIBJVM_SO@:%{_jvmdir}/%{sdkdir -- $suffix}/jre/lib/%{archinstall}/client/libjvm.so:g" $file.1 > $OUTPUT_FILE
%else
    sed -e "/@ABS_CLIENT_LIBJVM_SO@/d" $file.1 > $OUTPUT_FILE
%endif
    sed -i -e "s:@ABS_JAVA_HOME_DIR@:%{_jvmdir}/%{sdkdir -- $suffix}:g" $OUTPUT_FILE
    sed -i -e "s:@INSTALL_ARCH_DIR@:%{archinstall}:g" $OUTPUT_FILE
    sed -i -e "s:@prefix@:%{_jvmdir}/%{sdkdir -- $suffix}/:g" $OUTPUT_FILE
  done
done
# systemtap tapsets ends
%endif

# Prepare desktop files
# Portables do not have desktop integration

# Setup nss.cfg
sed -e "s:@NSS_LIBDIR@:%{NSS_LIBDIR}:g" %{SOURCE11} > nss.cfg

# Setup nss.fips.cfg
sed -e "s:@NSS_LIBDIR@:%{NSS_LIBDIR}:g" %{SOURCE17} > nss.fips.cfg

# Setup security policy
#Commented because NA to portable
#sed -i -e "s:^security.systemCACerts=.*:security.systemCACerts=%{cacerts_file}:" %{security_file}

%build

# How many CPU's do we have?
export NUM_PROC=%(/usr/bin/getconf _NPROCESSORS_ONLN 2> /dev/null || :)
export NUM_PROC=${NUM_PROC:-1}
%if 0%{?_smp_ncpus_max}
# Honor %%_smp_ncpus_max
[ ${NUM_PROC} -gt %{?_smp_ncpus_max} ] && export NUM_PROC=%{?_smp_ncpus_max}
%endif

%ifarch s390x sparc64 alpha %{power64} %{aarch64}
export ARCH_DATA_MODEL=64
%endif
%ifarch alpha
export CFLAGS="$CFLAGS -mieee"
%endif

# We use ourcppflags because the OpenJDK build seems to
# pass EXTRA_CFLAGS to the HotSpot C++ compiler...
EXTRA_CFLAGS="%ourcppflags -Wno-error"
EXTRA_CPP_FLAGS="%ourcppflags -fno-tree-vrp"
%ifarch %{power64} ppc
# fix rpmlint warnings
EXTRA_CFLAGS="$EXTRA_CFLAGS -fno-strict-aliasing"
%endif
EXTRA_ASFLAGS="${EXTRA_CFLAGS} -Wa"
export EXTRA_CFLAGS EXTRA_ASFLAGS

(cd %{top_level_dir_name}/common/autoconf
 bash ./autogen.sh
)

function buildjdk() {
    local outputdir=${1}
    local buildjdk=${2}
    local maketargets=${3}
    local debuglevel=${4}

    local top_srcdir_abs_path=$(pwd)/%{top_level_dir_name}
    # Variable used in hs_err hook on build failures
    local top_builddir_abs_path=$(pwd)/${outputdir}

    echo "Using output directory: ${outputdir}";
    echo "Checking build JDK ${buildjdk} is operational..."
    ${buildjdk}/bin/java -version
    echo "Building 8u%{updatever}-%{buildver}, milestone %{milestone}"

    mkdir -p ${outputdir}
    pushd ${outputdir}

    bash ${top_srcdir_abs_path}/configure \
%ifarch %{jfr_arches}
    --enable-jfr \
%else
    --disable-jfr \
%endif
%ifarch %{zero_arches}
    --with-jvm-variants=zero \
%endif
    --with-native-debug-symbols=$debug_symbols \
    --with-milestone=%{milestone} \
    --with-update-version=%{updatever} \
    --with-build-number=%{buildver} \
    --with-vendor-name="%{oj_vendor}" \
    --with-vendor-url="%{oj_vendor_url}" \
    --with-vendor-bug-url="%{oj_vendor_bug_url}" \
    --with-vendor-vm-bug-url="%{oj_vendor_bug_url}" \
    --with-boot-jdk=${buildjdk} \
    --with-debug-level=${debuglevel} \
    --disable-sysconf-nss \
    --enable-unlimited-crypto \
    --with-zlib=bundled \
    --with-giflib=bundled \
    --with-stdc++lib=static \
    --with-extra-cxxflags="$EXTRA_CPP_FLAGS" \
    --with-extra-cflags="$EXTRA_CFLAGS" \
    --with-extra-asflags="$EXTRA_ASFLAGS" \
    --with-extra-ldflags="%{ourldflags}" \
    --with-num-cores="$NUM_PROC"

    cat spec.gmk
    cat hotspot-spec.gmk

    make \
    LOG=trace \
    SCTP_WERROR= \
    $maketargets || ( pwd; find ${top_srcdir_abs_path} ${top_builddir_abs_path} -name "hs_err_pid*.log" | xargs cat && false )
   popd
}

function installjdk() {
    local outputdir=${1}
    local installdir=${2}
    #Changed as far portable need. We use this for setting JAVA_HOME and JRE_HOME
    local imagepath=$(pwd)/${installdir}
    
    local toplevel_build_dir=$(pwd)
    local top_builddir_abs_path=$(pwd)/${outputdir}

    echo "Installing build from ${outputdir} to ${installdir}..."
    mkdir -p ${installdir}
    echo "Installing images..."
    mv ${outputdir}/images ${installdir}
    if [ -d ${outputdir}/bundles ] ; then
	echo "Installing bundles...";
	mv ${outputdir}/bundles ${installdir} ;
    fi
    if [ -d ${outputdir}/docs ] ; then
	echo "Installing docs...";
	mv ${outputdir}/docs ${installdir} ;
    fi

%if !%{with artifacts}
    echo "Removing output directory...";
    rm -rf ${outputdir}
%endif

    # the build (erroneously) removes read permissions from some jars
    # this is a regression in OpenJDK 7 (our compiler):
    # http://icedtea.classpath.org/bugzilla/show_bug.cgi?id=1437
    find ${imagepath}/images/%{jdkimage} -iname '*.jar' -exec chmod ugo+r {} \;
    chmod ugo+r ${imagepath}/images/%{jdkimage}/lib/ct.sym

    # Build screws up permissions on binaries
    # https://bugs.openjdk.java.net/browse/JDK-8173610
    find ${imagepath}/images/%{jdkimage} -iname '*.so' -exec chmod +x {} \;
    find ${imagepath}/images/%{jdkimage}/bin/ -exec chmod +x {} \;

    # Install nss.cfg right away as we will be using the JRE above
    export JAVA_HOME=${imagepath}/images/%{jdkimage}
    export JRE_HOME=${imagepath}/images/%{jreimage} #portable specific

    install -m 644 ${toplevel_build_dir}/nss.cfg ${JAVA_HOME}/jre/lib/security/
    install -m 644 ${toplevel_build_dir}/nss.cfg ${JRE_HOME}/lib/security/ #portable specific
    # Install nss.fips.cfg: NSS configuration for global FIPS mode (crypto-policies)
    install -m 644 ${toplevel_build_dir}/nss.fips.cfg ${JAVA_HOME}/jre/lib/security/
    install -m 644 ${toplevel_build_dir}/nss.fips.cfg ${JRE_HOME}/lib/security/ #portable specific
    
    # System security properties are disabled by default on portable.
    # Turn on system security properties
    #sed -i -e "s:^security.useSystemPropertiesFile=.*:security.useSystemPropertiesFile=true:" \
    #${imagepath}/jre/lib/security/java.security

  pushd ${imagepath}/images
   if [ "x$suffix" == "x" ] ; then
     nameSuffix=""
   else
     nameSuffix=`echo "$suffix"| sed s/-/./`
   fi
    cp  %{SOURCE7} %{jreimage}/
    cp  %{SOURCE7} %{jdkimage}/
    for dir in %{jdkimage} %{jreimage} ; do
      # add alt-java man page
      echo "Hardened java binary recommended for launching untrusted code from the Web e.g. javaws" > "$dir"/man/man1/%{alt_java_name}.1
      cat "$dir"/man/man1/java.1 >> "$dir"/man/man1/%{alt_java_name}.1
    done
  popd #images

  # Print release information
  # Tweaked as per portable directory structure
  cat ${imagepath}/images/%{jreimage}/release
}

tar -cJf  ../%{jdkportablesourcesarchive -- ""} --transform "s|^|%{jdkportablesourcesname -- ""}/|" openjdk nss*
sha256sum ../%{jdkportablesourcesarchive -- ""} > ../%{jdkportablesourcesarchive -- ""}.sha256sum

%if %{build_hotspot_first}
  # Build a fresh libjvm.so first and use it to bootstrap
  cp -LR --preserve=mode,timestamps %{bootjdk} newboot
  systemjdk=$(pwd)/newboot
  buildjdk build/newboot ${systemjdk} %{hotspot_target} "release" "bundled"
  mv build/newboot/hotspot/dist/jre/lib/%{archinstall}/server/libjvm.so newboot/jre/lib/%{archinstall}/server
%else
  systemjdk=%{bootjdk}
%endif

for suffix in %{build_loop} ; do
if [ "x$suffix" = "x" ] ; then
  debugbuild=release
  debug_symbols=external
else
  # change --something to something
  debugbuild=`echo $suffix  | sed "s/-//g"`
  debug_symbols=internal
fi

builddir=%{buildoutputdir -- $suffix}
bootbuilddir=boot${builddir}
installdir=%{installoutputdir -- $suffix}
bootinstalldir=boot${installdir}

# Debug builds don't need same targets as release for
# build speed-up. We also avoid bootstrapping these
# slower builds.
if echo $debugbuild | grep -q "debug" ; then
  maketargets="%{debug_targets}"
  run_bootstrap=false
else
  maketargets="%{release_targets}"
  run_bootstrap=%{bootstrap_build}
fi

if ${run_bootstrap} ; then
  buildjdk ${bootbuilddir} ${systemjdk} "%{bootstrap_targets}" ${debugbuild}
  installjdk ${bootbuilddir} ${bootinstalldir}
  buildjdk ${builddir} $(pwd)/${bootinstalldir}/images/%{jdkimage} "${maketargets}" ${debugbuild} ${link_opt}
  installjdk ${builddir} ${installdir}
  %{!?with_artifacts:rm -rf ${bootinstalldir}}
else
  buildjdk ${builddir} ${systemjdk} "${maketargets}" ${debugbuild}
  installjdk ${builddir} ${installdir}
fi
pushd $(pwd)/${installdir}/images
  mv %{jreimage} %{jreportablename -- "$nameSuffix"}
  mv %{jdkimage} %{jdkportablename -- "$nameSuffix"}


    tar -cJf ../../../../../%{jreportablearchive -- "$nameSuffix"}  --exclude='**.debuginfo' %{jreportablename -- "$nameSuffix"} 
    sha256sum ../../../../../%{jreportablearchive -- "$nameSuffix"} > ../../../../../%{jreportablearchive -- "$nameSuffix"}.sha256sum
    if [ "x$suffix" == "x" ] ; then
      dnameSuffix="$nameSuffix".debuginfo
      tar -cJf ../../../../../%{jreportablearchive -- "$dnameSuffix"} $(find %{jreportablename -- "$nameSuffix"}/ -name \*.debuginfo)
      sha256sum ../../../../../%{jreportablearchive -- "$dnameSuffix"} > ../../../../../%{jreportablearchive -- "$dnameSuffix"}.sha256sum
    fi

    srcs=$(find %{jdkportablename -- "$nameSuffix"} | grep -v /demo/ | grep /src.zip$)
    test `echo "$srcs" | wc -l` -eq 1
    tar -cJf ../../../../../%{jdkportablearchive -- "$nameSuffix"}  --exclude='**.debuginfo' %{jdkportablename -- "$nameSuffix"}
    sha256sum ../../../../../%{jdkportablearchive -- "$nameSuffix"} > ../../../../../%{jdkportablearchive -- "$nameSuffix"}.sha256sum
    if [ "x$suffix" == "x" ] ; then
      dnameSuffix="$nameSuffix".debuginfo
      tar -cJf ../../../../../%{jdkportablearchive -- "$dnameSuffix"} $(find %{jdkportablename -- "$nameSuffix"}/ -name \*.debuginfo)
      sha256sum ../../../../../%{jdkportablearchive -- "$dnameSuffix"} > ../../../../../%{jdkportablearchive -- "$dnameSuffix"}.sha256sum
    fi
    mv %{jdkportablename -- "$nameSuffix"} %{jdkimage}
    mv %{jreportablename -- "$nameSuffix"} %{jreimage}
  popd #images

# build cycles
done

mkdir -p $RPM_BUILD_ROOT%{unpacked_licenses}
%check

# We test debug first as it will give better diagnostics on a crash
for suffix in %{build_loop} ; do

export JAVA_HOME=$(pwd)/%{installoutputdir -- $suffix}/images/%{jdkimage}

# Check unlimited policy has been used
$JAVA_HOME/bin/javac -d . %{SOURCE13}
$JAVA_HOME/bin/java TestCryptoLevel

# Check ECC is working
$JAVA_HOME/bin/javac -d . %{SOURCE14}
$JAVA_HOME/bin/java $(echo $(basename %{SOURCE14})|sed "s|\.java||")

# Check system crypto (policy) is active and can be disabled
# Test takes a single argument - true or false - to state whether system
# security properties are enabled or not.
$JAVA_HOME/bin/javac -d . %{SOURCE15}
export PROG=$(echo $(basename %{SOURCE15})|sed "s|\.java||")
export SEC_DEBUG="-Djava.security.debug=properties"
# Portable specific: set false whereas its true for upstream
$JAVA_HOME/bin/java ${SEC_DEBUG} ${PROG} false
$JAVA_HOME/bin/java ${SEC_DEBUG} -Djava.security.disableSystemPropertiesFile=true ${PROG} false

# Check correct vendor values have been set
$JAVA_HOME/bin/javac -d . %{SOURCE16}
$JAVA_HOME/bin/java $(echo $(basename %{SOURCE16})|sed "s|\.java||") "%{oj_vendor}" %{oj_vendor_url} %{oj_vendor_bug_url}

# Check java launcher has no SSB mitigation
if ! nm $JAVA_HOME/bin/java | grep set_speculation ; then true ; else false; fi

# Check alt-java launcher has SSB mitigation on supported architectures
%ifarch %{ssbd_arches}
nm $JAVA_HOME/bin/%{alt_java_name} | grep set_speculation
%else
if ! nm $JAVA_HOME/bin/%{alt_java_name} | grep set_speculation ; then true ; else false; fi
%endif

# Check translations are available for new timezones
$JAVA_HOME/bin/javac -d . %{SOURCE18}
$JAVA_HOME/bin/java $(echo $(basename %{SOURCE18})|sed "s|\.java||") JRE

# debug-symbols are only in debug build
if [ "x$suffix" == "x" ] ; then 
  invert="-v"
else
  invert=""
fi
# Check debug symbols are present and can identify code
SERVER_JVM="$JAVA_HOME/jre/lib/%{archinstall}/server/libjvm.so"
if [ -f "$SERVER_JVM" ] ; then
  nm -aCl "$SERVER_JVM" | grep $invert javaCalls.cpp
fi
CLIENT_JVM="$JAVA_HOME/jre/lib/%{archinstall}/client/libjvm.so"
if [ -f "$CLIENT_JVM" ] ; then
  nm -aCl "$CLIENT_JVM" | grep $invert javaCalls.cpp
fi
ZERO_JVM="$JAVA_HOME/jre/lib/%{archinstall}/zero/libjvm.so"
if [ -f "$ZERO_JVM" ] ; then
  nm -aCl "$ZERO_JVM" | grep $invert javaCalls.cpp
fi

# debug-symbols are only in debug portable build
if [ "x$suffix" == "x" ] ; then
  so_suffix="debuginfo"
else
  so_suffix="so"
fi

# Check debug symbols are present and can identify code
find "$JAVA_HOME" -iname "*.$so_suffix" -print0 | while read -d $'\0' lib
do
  if [ -f "$lib" ] ; then
    echo "Testing $lib for debug symbols"
    # All these tests rely on RPM failing the build if the exit code of any set
    # of piped commands is non-zero.

    # Test for .debug_* sections in the shared object. This is the main test
    # Stripped objects will not contain these
    eu-readelf -S "$lib" | grep "] .debug_"
    test $(eu-readelf -S "$lib" | grep -E "\]\ .debug_(info|abbrev)" | wc --lines) == 2

    # Test FILE symbols. These will most likely be removed by anything that
    # manipulates symbol tables because it's generally useless. So a nice test
    # that nothing has messed with symbols
    old_IFS="$IFS"
    IFS=$'\n'
    for line in $(eu-readelf -s "$lib" | grep "00000000      0 FILE    LOCAL  DEFAULT")
    do
     # We expect to see .cpp files, except for architectures like aarch64 and
     # s390 where we expect .o and .oS files
      echo "$line" | grep -E "ABS ((.*/)?[-_a-zA-Z0-9]+\.(c|cc|cpp|cxx|o|oS))?$"
    done
    IFS="$old_IFS"

    # If this is the JVM, look for javaCalls.(cpp|o) in FILEs, for extra sanity checking
    if [ "`basename $lib`" = "libjvm.so" ]; then
      eu-readelf -s "$lib" | \
        grep -E "00000000      0 FILE    LOCAL  DEFAULT      ABS javaCalls.(cpp|o)$"
    fi

    # Test that there are no .gnu_debuglink sections pointing to another
    # debuginfo file. There shouldn't be any debuginfo files, so the link makes
    # no sense either
    eu-readelf -S "$lib" | grep 'gnu'
    if eu-readelf -S "$lib" | grep '] .gnu_debuglink' | grep PROGBITS; then
      echo "bad .gnu_debuglink section."
      eu-readelf -x .gnu_debuglink "$lib"
      false
    fi
  fi
done

# Make sure gdb can do a backtrace based on line numbers on libjvm.so
# javaCalls.cpp:58 should map to:
# http://hg.openjdk.java.net/jdk8u/jdk8u/hotspot/file/ff3b27e6bcc2/src/share/vm/runtime/javaCalls.cpp#l58 
# Using line number 1 might cause build problems. See:
# https://bugzilla.redhat.com/show_bug.cgi?id=1539664
# https://bugzilla.redhat.com/show_bug.cgi?id=1538767
gdb -q "$JAVA_HOME/bin/java" <<EOF | tee gdb.out
handle SIGSEGV pass nostop noprint
handle SIGILL pass nostop noprint
set breakpoint pending on
break javaCalls.cpp:58
commands 1
backtrace
quit
end
run -version
EOF

%ifarch %{gdb_arches}
grep 'JavaCallWrapper::JavaCallWrapper' gdb.out
%endif

# Check src.zip has all sources. See RHBZ#1130490
jar -tf $JAVA_HOME/src.zip | grep 'sun.misc.Unsafe'

# Check class files include useful debugging information
$JAVA_HOME/bin/javap -l java.lang.Object | grep "Compiled from"
$JAVA_HOME/bin/javap -l java.lang.Object | grep LineNumberTable
$JAVA_HOME/bin/javap -l java.lang.Object | grep $invert LocalVariableTable

# Check generated class files include useful debugging information
$JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep "Compiled from"
$JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep LineNumberTable
$JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep $invert LocalVariableTable

# build cycles check
done

%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT%{_jvmdir}
mv ../%{jdkportablesourcesarchive -- ""} $RPM_BUILD_ROOT%{_jvmdir}/
mv ../%{jdkportablesourcesarchive -- ""}.sha256sum $RPM_BUILD_ROOT%{_jvmdir}/

for suffix in %{build_loop} ; do
  if [ "x$suffix" == "x" ] ; then
    nameSuffix=""
  else
    nameSuffix=`echo "$suffix"| sed s/-/./`
  fi
  mkdir -p $RPM_BUILD_ROOT%{_jvmdir}/%{jredir}
  mv ../../%{jreportablearchive -- "$nameSuffix"} $RPM_BUILD_ROOT%{_jvmdir}/
  mv ../../%{jreportablearchive -- "$nameSuffix"}.sha256sum $RPM_BUILD_ROOT%{_jvmdir}/
  mv ../../%{jdkportablearchive -- "$nameSuffix"} $RPM_BUILD_ROOT%{_jvmdir}/
  mv ../../%{jdkportablearchive -- "$nameSuffix"}.sha256sum $RPM_BUILD_ROOT%{_jvmdir}/
  if [ "x$suffix" == "x" ] ; then
      dnameSuffix="$nameSuffix".debuginfo
      mv ../../%{jreportablearchive -- "$dnameSuffix"} $RPM_BUILD_ROOT%{_jvmdir}/
      mv ../../%{jreportablearchive -- "$dnameSuffix"}.sha256sum $RPM_BUILD_ROOT%{_jvmdir}/
      mv ../../%{jdkportablearchive -- "$dnameSuffix"} $RPM_BUILD_ROOT%{_jvmdir}/
      mv ../../%{jdkportablearchive -- "$dnameSuffix"}.sha256sum $RPM_BUILD_ROOT%{_jvmdir}/
  fi
  mkdir -p $RPM_BUILD_ROOT%{unpacked_licenses}/%{jdkportablesourcesarchive -- "%{normal_suffix}"}
  cp -af openjdk/{ASSEMBLY_EXCEPTION,LICENSE,THIRD_PARTY_README} $RPM_BUILD_ROOT%{unpacked_licenses}/%{jdkportablesourcesarchive -- "%{normal_suffix}"}
# To show sha in the build log-
for file in `ls $RPM_BUILD_ROOT%{_jvmdir}/*.sha256sum` ; do ls -l $file ; cat $file ; done
done

# printenv

%if %{include_normal_build}
%files
# main package builds always
%{_jvmdir}/%{jreportablearchiveForFiles}
%{_jvmdir}/%{jreportablearchive -- .debuginfo}
%{_jvmdir}/%{jreportablearchiveForFiles}.sha256sum
%{_jvmdir}/%{jreportablearchive -- .debuginfo}.sha256sum
%license %{unpacked_licenses}/%{jdkportablesourcesarchiveForFiles}
%else
%files
# placeholder
%endif

%if %{include_normal_build}
%files devel
%{_jvmdir}/%{jdkportablearchiveForFiles}
%{_jvmdir}/%{jdkportablearchive -- .debuginfo}
%{_jvmdir}/%{jdkportablearchiveForFiles}.sha256sum
%{_jvmdir}/%{jdkportablearchive -- .debuginfo}.sha256sum
%license %{unpacked_licenses}/%{jdkportablesourcesarchiveForFiles}
%endif

%if %{include_debug_build}
%files slowdebug
%{_jvmdir}/%{jreportablearchive -- .slowdebug}
%{_jvmdir}/%{jreportablearchive -- .slowdebug}.sha256sum
%license %{unpacked_licenses}/%{jdkportablesourcesarchiveForFiles}

%files devel-slowdebug
%{_jvmdir}/%{jdkportablearchive -- .slowdebug}
%{_jvmdir}/%{jdkportablearchive -- .slowdebug}.sha256sum
%license %{unpacked_licenses}/%{jdkportablesourcesarchiveForFiles}
%endif
%if %{include_fastdebug_build}
%files fastdebug
%{_jvmdir}/%{jreportablearchive -- .fastdebug}
%{_jvmdir}/%{jreportablearchive -- .fastdebug}.sha256sum
%license %{unpacked_licenses}/%{jdkportablesourcesarchiveForFiles}

%files devel-fastdebug
%{_jvmdir}/%{jdkportablearchive -- .fastdebug}
%{_jvmdir}/%{jdkportablearchive -- .fastdebug}.sha256sum
%license %{unpacked_licenses}/%{jdkportablesourcesarchiveForFiles}
%endif

%files sources
%{_jvmdir}/%{jdkportablesourcesarchiveForFiles}
%{_jvmdir}/%{jdkportablesourcesarchiveForFiles}.sha256sum
%license %{unpacked_licenses}/%{jdkportablesourcesarchiveForFiles}

%changelog
* Mon Jun 26 2023 Jiri Andrlik <jandrlik@redhat.com> - 1:1.8.0.372.b07-5
- moving the creation of tar archives to after the build and installation phase to save some resources 

* Sun Jun 18 2023 Jiri Andrlik <jandrlik@redhat.com> - 1:1.8.0.372.b07-4
- adding the sources subpkg for purposes of repack

* Thu Jun 17 2023 Jayashree Huttanagoudar <jhuttana@redhat.com> - 1:1.8.0.372.b07-3
- no longer using system cacerts during build
- they are already mv-ed as .upstream in rpms
 
* Sat Jun 17 2023 Jiri Andrlik <jandrlik@redhat.com> - 1:1.8.0.372.b07-2
- Redeclared ForFiles release sections as %%nil no longer works with %%1
- RPM 4.19 no longer accept our double percentaged %%{nil} passed to %%{1}
- so we have to pass in "" but evaluate it, otherwise files record will include it

* Tue Apr 18 2023 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.372.b07-1
- Update to shenandoah-jdk8u372-b07 (GA)
- Update release notes for shenandoah-8u372-b07.
- Fix broken links and missing release notes in older releases.
- Drop JDK-8195607/PR3776/RH1760437 now this is upstream
- Require tzdata 2022g due to inclusion of JDK-8296108, JDK-8296715 & JDK-8297804
- Require tzdata 2023c due to inclusion of JDK-8305113 in 8u372-b07
- Drop tzdata patches for 2022d & 2022e (JDK-8294357 & JDK-8295173) which are now upstream
- Update TestTranslations.java to test the new America/Ciudad_Juarez zone
- Drop RH1163501 patch which is not upstream or in 11, 17 & 19 packages and seems obsolete
  - Patch was broken by inclusion of "JDK-8293554: Enhanced DH Key Exchanges"
  - Patch was added for a specific corner case of a 4096-bit DH key on a Fedora host that no longer exists
  - Fedora now appears to be using RSA and the JDK now supports ECC in preference to large DH keys
- Update generate_tarball.sh to add support for passing a boot JDK to the configure run
- Add POSIX-friendly error codes to generate_tarball.sh and fix whitespace
- Remove .jcheck and GitHub support when generating tarballs, as done in upstream release tarballs
- Include JDK-8271199 backport early ahead of 8u382 (RH2175317)

* Fri Feb 03 2023 Jiri Andrlik <jandrlik@redhat.com> - 1:1.8.0.352.b08-1.1
- fixing build for f37 and above - exclude of ix86 archs

* Thu Jan 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.0.352.b08-1.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Fri Nov 11 2022 Jiri Andrlik <jandrlik@redhat.com> - 1:1.8.0.352.b08-1
 - new package
 - Related: rhbz#2141984

