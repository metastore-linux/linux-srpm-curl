# Set to 0 for regular curl package, 1 for libcurl compatibility package
%global compat 0

# Use rpmbuild --without nss to build with OpenSSL rather than nss
%{!?_without_nss: %{!?_with_nss: %global _with_nss --with-nss}}
%{?_with_nss:		%global disable_nss 0}
%{?_without_nss:	%global disable_nss 1}

# Build with nss rather than OpenSSL for Fedora 16-26 and RHEL-7 unless OpenSSL is requested
# (older distributions don't have recent enough nss versions)
%global nss_ok %([ '(' 0%{?fedora} -gt 15 -a 0%{?fedora} -lt 27 ')' -o 0%{?rhel} -eq 7 ] && echo 1 || echo 0)
%if %{nss_ok} && !%{disable_nss}
%global ssl_provider nss
%global ssl_versionreq >= 3.14.0
%global use_nss 1
%global have_openssl_libs 0
%else
%global ssl_provider openssl
%global ssl_versionreq %{nil}
%global use_nss 0
# Have openssl-libs (with Epoch of 1) from Fedora 18, RHEL-7 onwards
%global have_openssl_libs %([ 0%{?fedora} -gt 17 -o 0%{?rhel} -gt 6 ] && echo 1 || echo 0)
%endif

# Build with Posix threaded DNS lookups rather than using c-ares from Fedora 16, RHEL-7
%global use_threads_posix %([ 0%{?fedora} -gt 15 -o 0%{?rhel} -gt 6 ] && echo 1 || echo 0)

# Also build (lib)curl-minimal from Fedora 27 onwards
%global build_minimal %([ 0%{?fedora} -gt 26 -o 0%{?rhel} -gt 7 ] && echo 1 || echo 0)

# Use libssh backend rather than libssh2 from Fedora 28 onwards
%if %([ 0%{?fedora} -gt 27 -o 0%{?rhel} -gt 7 ] && echo 1 || echo 0)
%global libssh libssh
%global libssh_minimum_version 0.7.5
%else
%global libssh libssh2
%global libssh_minimum_version 1.2
%endif

# Run the test suite using Python 3 from Fedora 28 onwards
%if %([ 0%{?fedora} -gt 27 -o 0%{?rhel} -gt 7 ] && echo 1 || echo 0)
%global test_python python3-devel
%else
%global test_python python2
%endif

Version:                7.62.0
Release:                2%{?dist}
%if %{compat}
Summary:                Curl library for compatibility with old applications
Name:                   libcurl%(echo %{version} | tr -d .)
Obsoletes:              compat-libcurl < %{version}-%{release}
Provides:               compat-libcurl = %{version}-%{release}
%else
Summary:                Utility for getting files from remote servers (FTP, HTTP, and others)
Name:                   curl
Provides:               webclient
%endif
License:                MIT

Source0:                https://curl.haxx.se/download/curl-%{version}.tar.xz

# METASTORE - [
# Signature
Source900:              https://curl.haxx.se/download/curl-%{version}.tar.xz.asc
# ] - METASTORE

# Patch making libcurl multilib ready
Patch101: 0101-curl-7.58.0-multilib.patch

# Prevent configure script from discarding -g in CFLAGS (#496778)
Patch102: 0102-curl-7.54.1-debug.patch

# Migrate tests/http_pipe.py to Python 3
Patch103: 0103-curl-7.62.0-python3.patch

# Use localhost6 instead of ip6-localhost in the curl test-suite
Patch104: 0104-curl-7.19.7-localhost6.patch

# Fix FTBFS when building curl dynamically with no libcurl.so.4 in system
Patch300: curl-7.49.0-zsh-cpl.patch

# Remove redundant compiler/linker flags from libcurl.pc
# Assumes %%{_libdir} = /usr/lib or /usr/lib64 and %%{_includedir} = /usr/include
Patch302: 0302-curl-7.47.1-pkgconfig.patch

URL:                    https://curl.haxx.se/
BuildRequires:          brotli-devel
%if ! %{use_threads_posix}
BuildRequires:          c-ares-devel >= 1.6.0
%endif
BuildRequires:          coreutils
BuildRequires:          gcc
BuildRequires:          krb5-devel
BuildRequires:          libidn2-devel
BuildRequires:          openldap-devel
BuildRequires:          pkgconfig
BuildRequires:          groff
BuildRequires:          libmetalink-devel
%if 0%{?fedora} > 22 || 0%{?rhel:1}
BuildRequires:          libnghttp2-devel
# nghttpx (an HTTP/2 proxy) is used by the upstream test-suite
BuildRequires:          nghttp2
%endif
%if 0%{?fedora} > 18 || 0%{?rhel} > 6
BuildRequires:          libpsl-devel
%endif
BuildRequires:          %{libssh}-devel >= %{libssh_minimum_version}
BuildRequires:          make
BuildRequires:          sed
BuildRequires:          %{ssl_provider}-devel %{ssl_versionreq}
BuildRequires:          zlib-devel
# Needed to compress content of tool_hugehelp.c after changing curl.1 man page
BuildRequires:          perl(IO::Compress::Gzip)
# Using an older version of libcurl could result in CURLE_UNKNOWN_OPTION
Requires:               libcurl%{?_isa} >= %{version}-%{release}
%if ! %{use_nss}
Requires:               %{_sysconfdir}/pki/tls/certs/ca-bundle.crt
%endif
# Test suite requirements
BuildRequires:          gnutls-utils
BuildRequires:          openssh-clients
BuildRequires:          openssh-server
BuildRequires:          perl-interpreter
BuildRequires:          perl(Cwd)
BuildRequires:          perl(Digest::MD5)
BuildRequires:          perl(Exporter)
BuildRequires:          perl(File::Basename)
BuildRequires:          perl(File::Copy)
BuildRequires:          perl(File::Spec)
BuildRequires:          perl(IPC::Open2)
BuildRequires:          perl(MIME::Base64)
BuildRequires:          perl(strict)
BuildRequires:          perl(Time::Local)
BuildRequires:          perl(Time::HiRes)
BuildRequires:          perl(warnings)
BuildRequires:          perl(vars)
BuildRequires:          stunnel
# python used for http-pipe tests (190x)
# requires python ≥ 2.7 but fails safely
BuildRequires:          %{test_python}

# require at least the version of libpsl that we were built against,
# to ensure that we have the necessary symbols available (#1631804)
%if 0%{?fedora} > 18 || 0%{?rhel} > 6
%global libpsl_version %(pkg-config --modversion libpsl 2>/dev/null || echo 0)
%endif

# require at least the version of libssh/libssh2 that we were built against,
# to ensure that we have the necessary symbols available (#525002, #642796)
%global libssh_version %(pkg-config --modversion %{libssh} 2>/dev/null || echo 0)

# require at least the version of openssl-libs that we were built against,
# to ensure that we have the necessary symbols available (#1462184, #1462211)
%if %{have_openssl_libs}
%global openssl_version %(pkg-config --modversion openssl 2>/dev/null || echo 0)
%endif

# same issue with c-ares
%global cares_version %(pkg-config --modversion libcares 2>/dev/null || echo 0)

%if ! %{compat}
%description
curl is a command line tool for transferring data with URL syntax, supporting
FTP, FTPS, HTTP, HTTPS, SCP, SFTP, TFTP, TELNET, DICT, LDAP, LDAPS, FILE, IMAP,
SMTP, POP3 and RTSP.  curl supports SSL certificates, HTTP POST, HTTP PUT, FTP
uploading, HTTP form based upload, proxies, cookies, user+password
authentication (Basic, Digest, NTLM, Negotiate, kerberos...), file transfer
resume, proxy tunneling and a busload of other useful tricks.

# -------------------------------------------------------------------------------------------------------------------- #
# Package: libcurl
# -------------------------------------------------------------------------------------------------------------------- #

%package -n libcurl
Summary:                A library for getting files from web servers
# c-ares adds symbols that curl uses if available, so we need to enforce
# version dependency
%if ! %{use_threads_posix}
Requires:               c-ares%{?_isa} >= %{cares_version}
%endif
%if 0%{?fedora} > 18 || 0%{?rhel} > 6
Requires:               libpsl%{?_isa} >= %{libpsl_version}
%endif
# libssh/libssh2 adds symbols that curl uses if available, so we need to enforce
# version dependency
Requires:               %{libssh}%{?_isa} >= %{libssh_version}
# same issue with openssl
%if %{have_openssl_libs}
Requires:               openssl-libs%{?_isa} >= 1:%{openssl_version}
%endif
# libnsspem.so is no longer included in the nss package from F-23 onwards (#1347336)
%if 0%{?fedora} > 22 || 0%{?rhel} > 7
%if %{use_nss}
%if 0%{?fedora} > 24 || 0%{?rhel} > 7
BuildRequires:          nss-pem%{?_isa}
Requires:               nss-pem%{?_isa}
%else
BuildRequires:          nss-pem
Requires:               nss-pem
%endif
%endif
%endif

%description -n libcurl
libcurl is a free and easy-to-use client-side URL transfer library, supporting
FTP, FTPS, HTTP, HTTPS, SCP, SFTP, TFTP, TELNET, DICT, LDAP, LDAPS, FILE, IMAP,
SMTP, POP3 and RTSP. libcurl supports SSL certificates, HTTP POST, HTTP PUT,
FTP uploading, HTTP form based upload, proxies, cookies, user+password
authentication (Basic, Digest, NTLM, Negotiate, Kerberos4), file transfer
resume, HTTP proxy tunneling and more.

# -------------------------------------------------------------------------------------------------------------------- #
# Package: libcurl-devel
# -------------------------------------------------------------------------------------------------------------------- #

%package -n libcurl-devel
Requires:               libcurl%{?_isa} = %{version}-%{release}
Requires:               %{ssl_provider}-devel %{ssl_versionreq}
Requires:               %{libssh}-devel
Summary:                Files needed for building applications with libcurl
Provides:               curl-devel = %{version}-%{release}
Provides:               curl-devel%{?_isa} = %{version}-%{release}
Obsoletes:              curl-devel < %{version}-%{release}
# From Fedora 14, %%{_datadir}/aclocal is included in the filesystem package
%if 0%{?fedora} < 14
Requires:               %{_datadir}/aclocal
%endif

%description -n libcurl-devel
The libcurl-devel package includes header files and libraries necessary for
developing programs that use the libcurl library. It contains the API
documentation of the library, too.

%if %{build_minimal}

# -------------------------------------------------------------------------------------------------------------------- #
# Package: curl-minimal
# -------------------------------------------------------------------------------------------------------------------- #

%package -n curl-minimal
Summary:                Conservatively configured build of curl for minimal installations
Provides:               curl = %{version}-%{release}
Conflicts:              curl
# Using an older version of libcurl could result in CURLE_UNKNOWN_OPTION
Requires:               libcurl%{?_isa} >= %{version}-%{release}
RemovePathPostfixes:	.minimal
# Needed for RemovePathPostfixes to work with shared libraries
%undefine __brp_ldconfig

%description -n curl-minimal
This is a replacement of the 'curl' package for minimal installations. It
comes with a limited set of features compared to the 'curl' package. On the
other hand, the package is smaller and requires fewer run-time dependencies to
be installed.

# -------------------------------------------------------------------------------------------------------------------- #
# Package: libcurl-minimal
# -------------------------------------------------------------------------------------------------------------------- #

%package -n libcurl-minimal
Summary:                Conservatively configured build of libcurl for minimal installations
Provides:               libcurl = %{version}-%{release}
Provides:               libcurl%{?_isa} = %{version}-%{release}
Conflicts:              libcurl
RemovePathPostfixes:	.minimal
%if %{have_openssl_libs}
Requires:               openssl-libs%{?_isa} >= 1:%{openssl_version}
%endif

%description -n libcurl-minimal
This is a replacement of the 'libcurl' package for minimal installations. It
comes with a limited set of features compared to the 'libcurl' package. On the
other hand, the package is smaller and requires fewer run-time dependencies to
be installed.
%endif
%else
%description
This package provides an old version of cURL's libcurl library, necessary
for some old applications that have not been rebuilt against an up to date
version of cURL.

%endif

# -------------------------------------------------------------------------------------------------------------------- #
# -----------------------------------------------------< SCRIPT >----------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

%prep
%setup -q -n curl-%{version}

# Upstream patches
# (none)

# Fedora Patches
%patch101 -p1
%patch102 -p1
%patch104 -p1

# Local Patches
%patch300
%patch302

# Make tests/*.py use Python 3 from Fedora 28 onwards
%if "%{test_python}" == "python3-devel"
%patch103
sed -e '1 s|^#!/.*python|#!%{__python3}|' -i tests/*.py
%endif

# ssh-related tests 582, 600-642, 656, 1446, 2004 fail for as-yet unknown reasons on F-12 to F-15
# Does not seem to be related to SELinux or use of POSIX threaded DNS resolver
%if 0%{?fedora} > 11 && 0%{?fedora} < 16
for test in 582 \
	600 601 602 603 604 605 606 607 608 609 \
	610 611 612 613 614 615 616 617 618 619 \
	620 621 622 623 624 625 626 627 628 629 \
	630 631     633 634 635 636 637 638 639 \
	640 641 642 \
                                656 \
	1446 1456 2004; do
	echo $test
done >> tests/data/DISABLED
%endif

# Adapt test 323 for updated OpenSSL
sed -i -e 's/^35$/35,52/' tests/data/test323

%build
%if ! %{use_nss}
export CPPFLAGS="$(pkg-config --cflags openssl)"
%endif
[ -x /usr/kerberos/bin/krb5-config ] && KRB5_PREFIX="=/usr/kerberos"
mkdir build-{full,minimal}
%global _configure ../configure
export common_configure_opts=" \
	--cache-file=../config.cache \
	--disable-static \
	--enable-symbol-hiding \
	--enable-ipv6 \
%if %{use_threads_posix}
	--enable-threaded-resolver \
%else
	--enable-ares \
%endif
	--with-gssapi${KRB5_PREFIX} \
	--with-nghttp2 \
%if %{use_nss}
	--with-nss \
	--without-ssl \
	--without-ca-bundle \
%else
	--with-ssl \
	--with-ca-bundle=%{_sysconfdir}/pki/tls/certs/ca-bundle.crt \
%endif
	"

# configure minimal build
%if %{build_minimal}
(
	cd build-minimal
	%configure $common_configure_opts \
	--disable-ldap \
	--disable-ldaps \
	--disable-manual \
	--without-brotli \
	--without-libidn2 \
	--without-libmetalink \
	--without-libpsl \
	--without-%{libssh}
)
%endif

# configure full build
(
	cd build-full
	%configure $common_configure_opts \
	--enable-ldap \
	--enable-ldaps \
	--enable-manual \
	--with-brotli \
	--with-libidn2 \
	--with-libmetalink \
	--with-libpsl \
	--with-%{libssh}
)

# Remove bogus rpath
sed -i \
	-e 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' \
	-e 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' \
%if %{build_minimal}
	build-{full,minimal}/libtool
%else
	build-full/libtool
%endif

%if %{build_minimal}
make %{_smp_mflags} V=1 -C build-minimal
%endif
make %{_smp_mflags} V=1 -C build-full

%install
%if %{build_minimal}
# Install and rename the library that will be packaged as libcurl-minimal
make DESTDIR=%{buildroot} INSTALL="install -p" install -C build-minimal/lib
rm -f %{buildroot}%{_libdir}/libcurl.{la,so}
for i in %{buildroot}%{_libdir}/*; do
	mv -v $i $i.minimal
done

# Install and rename the executable that will be packaged as curl-minimal
make DESTDIR=%{buildroot} INSTALL="install -p" install -C build-minimal/src
mv -v %{buildroot}%{_bindir}/curl{,.minimal}
%endif

# Install the executable and library that will be packaged as curl and libcurl
make DESTDIR=%{buildroot} INSTALL="install -p" install -C build-full

# Install zsh completion for curl
# (we have to override LD_LIBRARY_PATH because we eliminated rpath)
LD_LIBRARY_PATH="%{buildroot}%{_libdir}:$LD_LIBRARY_PATH" \
	make DESTDIR=%{buildroot} INSTALL="install -p" \
	install -C build-full/scripts

# --disable-static not always honoured
rm -f %{buildroot}%{_libdir}/libcurl.a
install -d %{buildroot}%{_datadir}/aclocal
install -m 644 -p docs/libcurl/libcurl.m4 %{buildroot}%{_datadir}/aclocal

%check
# Skip the (lengthy) checks on EOL Fedora releases (over ~400 days old)
# Also run on Fedora 13, have seen test failures on F12..F15
if [ -z "$(find /etc/fedora-release -mtime +400)" %{?rhel:-o rhel} -o "%{?fedora}" = "13" ]; then
	export LD_LIBRARY_PATH=%{buildroot}%{_libdir}
	cd build-full/tests
	make %{?_smp_mflags} V=1

	# Relax crypto policy for the test-suite to make it pass again (#1610888)
	export OPENSSL_SYSTEM_CIPHERS_OVERRIDE=XXX
	export OPENSSL_CONF=

	# Run the upstream test-suite
	srcdir=../../tests perl -I../../tests ../../tests/runtests.pl -a -p -v '!flaky'
	cd -
fi

%if %([ 0%{?fedora} -lt 28 -a 0%{?rhel} -lt 8 ] && echo 1 || echo 0)
%if ! %{compat}
%post -n libcurl -p /sbin/ldconfig
%postun -n libcurl -p /sbin/ldconfig
%if %{build_minimal}
%post -n libcurl-minimal -p /sbin/ldconfig
%postun -n libcurl-minimal -p /sbin/ldconfig
%endif
%else
%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig
%endif
%endif

%files
%doc CHANGES README*
%doc docs/BUGS docs/DEPRECATE.md docs/FAQ docs/FEATURES docs/SECURITY-PROCESS.md
%doc docs/TODO docs/MANUAL docs/RESOURCES docs/TheArtOfHttpScripting
%if ! %{compat}
%{_bindir}/curl
%{_datadir}/zsh/
%{_mandir}/man1/curl.1*
%else
%if 0%{?_licensedir:1}
%license COPYING
%else
%doc COPYING
%endif
%exclude %{_bindir}/curl
%exclude %{_datadir}/zsh/site-functions/_curl
%exclude %{_mandir}/man1/curl.1*
%{_libdir}/libcurl.so.*
%endif

%if ! %{compat}
%files -n libcurl
%if 0%{?_licensedir:1}
%license COPYING
%else
%doc COPYING
%endif
%{_libdir}/libcurl.so.4
%{_libdir}/libcurl.so.4.[0-9].[0-9]

%files -n libcurl-devel
%doc docs/examples/*.c docs/examples/Makefile.example docs/INTERNALS.md
%doc docs/CHECKSRC.md docs/CONTRIBUTE.md docs/libcurl/ABI docs/CODE_STYLE.md
%doc docs/GOVERNANCE.md
%{_bindir}/curl-config
%{_includedir}/curl/
%{_libdir}/*.so
%{_libdir}/pkgconfig/libcurl.pc
%{_mandir}/man1/curl-config.1*
%{_mandir}/man3/*
%{_datadir}/aclocal/libcurl.m4

%if %{build_minimal}
%files -n curl-minimal
%{_bindir}/curl.minimal
%{_mandir}/man1/curl.1*

%files -n libcurl-minimal
%license COPYING
%{_libdir}/libcurl.so.4.minimal
%{_libdir}/libcurl.so.4.[0-9].[0-9].minimal
%endif
%else
%exclude %{_bindir}/curl-config
%exclude %{_includedir}/curl/
%exclude %{_libdir}/*.so
%exclude %{_libdir}/pkgconfig/libcurl.pc
%exclude %{_mandir}/man1/curl-config.1*
%exclude %{_mandir}/man3/*
%exclude %{_datadir}/aclocal/libcurl.m4
%endif
%exclude %{_libdir}/libcurl.la

%changelog
* Sat Nov 3 2018 Kitsune Solar <kitsune.solar@gmail.com> - 7.62.0-2
- Rebuilt for EL7.

* Wed Oct 31 2018 Paul Howarth <paul@city-fan.org> - 7.62.0-1.0.cf
- Update to 7.62.0
  - multiplex: Enable by default
  - url: Default to CURL_HTTP_VERSION_2TLS if built h2-enabled
  - setopt: Add CURLOPT_DOH_URL
  - curl: --doh-url added
  - setopt: Add CURLOPT_UPLOAD_BUFFERSIZE: set upload buffer size
  - imap: Change from "FETCH" to "UID FETCH"
  - configure: Add option to disable automatic OpenSSL config loading
  - upkeep: Add a connection upkeep API: curl_easy_upkeep()
  - URL-API: Added five new functions
  - vtls: MesaLink is a new TLS backend
  - Fix SASL password overflow via integer overflow (CVE-2018-16839)
  - Fix use-after-free in handle close (CVE-2018-16840)
  - Fix warning message out-of-buffer read (CVE-2018-16842)
  - CURLOPT_DNS_USE_GLOBAL_CACHE: deprecated
  - Curl_dedotdotify(): Always nul terminate returned string
  - Curl_follow: Always free the passed new URL
  - Curl_http2_done: Fix memleak in error path
  - Curl_retry_request: Fix memory leak
  - Curl_saferealloc: Fixed typo in docblock
  - FILE: Fix CURLOPT_NOBODY and CURLOPT_HEADER output
  - GnutTLS: TLS 1.3 support
  - SECURITY-PROCESS: Mention the bountygraph program
  - VS projects: Add USE_IPV6:
  - Windows: Fixes for MinGW targeting Windows Vista
  - anyauthput: Fix compiler warning on 64-bit Windows
  - appveyor: Add WinSSL builds
  - appveyor: Run test suite (on Windows!)
  - certs: Generate tests certs with sha256 digest algorithm
  - checksrc: Enable strict mode and warnings
  - checksrc: Handle zero scoped ignore commands
  - cmake: Backport to work with CMake 3.0 again
  - cmake: Improve config installation
  - cmake: Add support for transitive ZLIB target
  - cmake: Disable -Wpedantic-ms-format
  - cmake: Don't require OpenSSL if USE_OPENSSL=OFF
  - cmake: Fixed path used in generation of docs/tests
  - cmake: Remove unused *SOCKLEN_T variables
  - cmake: Suppress MSVC warning C4127 for libtest
  - cmake: Test and set missed defines during configuration
  - comment: Fix multiple typos in function parameters
  - config: Remove unused SIZEOF_VOIDP
  - config_win32: Enable LDAPS
  - configure: Force-use -lpthreads on HPUX
  - configure: Remove CURL_CONFIGURE_CURL_SOCKLEN_T
  - configure: s/AC_RUN_IFELSE/CURL_RUN_IFELSE/
  - cookies: Remove redundant expired check
  - cookies: Fix leak when writing cookies to file
  - curl-config.in: Remove dependency on bc
  - curl.1: --ipv6 mutexes ipv4 (fixed typo)
  - curl: Enabled Windows VT Support and UTF-8 output
  - curl: Update the documentation of --tlsv1.0
  - curl_multi_wait: Call getsock before figuring out timeout
  - curl_ntlm_wb: Check aprintf() return codes
  - curl_threads: Fix classic MinGW compile break
  - darwinssl: Fix realloc memleak
  - darwinssl: More specific and unified error codes
  - data-binary.d: Clarify default content-type is x-www-form-urlencoded
  - docs/BUG-BOUNTY: Explain the bounty program
  - docs/CIPHERS: Mention the options used to set TLS 1.3 ciphers
  - docs/CIPHERS: Fix the TLS 1.3 cipher names
  - docs/CIPHERS: Mention the colon separation for OpenSSL
  - docs/examples: URL updates
  - docs: Add "see also" links for SSL options
  - example/asiohiper: Insert warning comment about its status
  - example/htmltidy: Fix include paths of tidy libraries
  - examples/Makefile.m32: Sync with core
  - examples/http2-pushinmemory: Receive HTTP/2 pushed files in memory
  - examples/parseurl.c: Show off the URL API
  - examples: Fix memory leaks from realloc errors
  - examples: Do not wait when no transfers are running
  - ftp: Include command in Curl_ftpsend sendbuffer
  - gskit: Make sure to terminate version string
  - gtls: Values stored to but never read
  - hostip: Fix check on Curl_shuffle_addr return value
  - http2: Fix memory leaks on error-path
  - http: Fix memleak in rewind error path
  - krb5: Fix memory leak in krb_auth
  - ldap: Show precise LDAP call in error message on Windows
  - lib: Fix gcc8 warning on Windows
  - memory: Add missing curl_printf header
  - memory: Ensure to check allocation results
  - multi: Fix error handling in the SENDPROTOCONNECT state
  - multi: Fix memory leak in content encoding related error path
  - multi: Make the closure handle "inherit" CURLOPT_NOSIGNAL
  - netrc: Free temporary strings if memory allocation fails
  - nss: Fix nssckbi module loading on Windows
  - nss: Try to connect even if libnssckbi.so fails to load
  - ntlm_wb: Fix memory leaks in ntlm_wb_response
  - ntlm_wb: Bail out if the response gets overly large
  - openssl: Assume engine support in 0.9.8 or later
  - openssl: Enable TLS 1.3 post-handshake auth
  - openssl: Fix gcc8 warning
  - openssl: Load built-in engines too
  - openssl: Make 'done' a proper boolean
  - openssl: Output the correct cipher list on TLS 1.3 error
  - openssl: Return CURLE_PEER_FAILED_VERIFICATION on failure to parse issuer
  - openssl: Show "proper" version number for libressl builds
  - pipelining: Deprecated
  - rand: Add comment to skip a clang-tidy false positive
  - rtmp: Fix for compiling with lwIP
  - runtests: Ignore disabled even when ranges are given
  - runtests: Skip ld_preload tests on macOS
  - runtests: Use Windows paths for Windows curl
  - schannel: Unified error code handling
  - sendf: Fix whitespace in infof/failf concatenation
  - ssh: free the session on init failures
  - ssl: Deprecate CURLE_SSL_CACERT in favour of a unified error code
  - system.h: Use proper setting with Sun C++ as well
  - test1299: Use single quotes around asterisk
  - test1452: Mark as flaky
  - test1651: Unit test Curl_extract_certinfo()
  - test320: Strip out more HTML when comparing
  - tests/negtelnetserver.py: Fix Python2-ism in neg TELNET server
  - tests: Add unit tests for url.c
  - timeval: Fix use of weak symbol clock_gettime() on Apple platforms
  - tool_cb_hdr: Handle failure of rename()
  - travis: Add a "make tidy" build that runs clang-tidy
  - travis: Add build for "configure --disable-verbose"
  - travis: Bump the Secure Transport build to use xcode
  - travis: Make distcheck scan for BOM markers
  - unit1300: Fix stack-use-after-scope AddressSanitizer warning
  - urldata: Fix "connecting" comment
  - urlglob: Improve error message on bad globs
  - vtls: Fix ssl version "or later" behaviour change for many backends
  - x509asn1: Fix SAN IP address verification
  - x509asn1: Always check return code from getASN1Element()
  - x509asn1: Return CURLE_PEER_FAILED_VERIFICATION on failure to parse cert
  - x509asn1: Suppress left shift on signed value
- Test 656 segfaults on Fedora 13 to 15 inclusive, so disable it there

* Fri Oct 12 2018 Paul Howarth <paul@city-fan.org> - 7.61.1-3.0.cf
- Enable TLS 1.3 post-handshake auth in OpenSSL
- Update the documentation of --tlsv1.0 in curl(1) man page

* Fri Oct  5 2018 Paul Howarth <paul@city-fan.org> - 7.61.1-2.0.cf
- Enforce versioned libpsl dependency for libcurl (#1631804)
- test320: Update expected output for gnutls-3.6.4
- Drop 0105-curl-7.61.0-tests-ssh-keygen.patch, no longer needed (#1622594)
- test1456: Seems to be flaky so disable it

* Wed Sep  5 2018 Paul Howarth <paul@city-fan.org> - 7.61.1-1.0.cf
- Update to 7.61.1
  - Fix NTLM password overflow via integer overflow (CVE-2018-14618)
  - CURLINFO_SIZE_UPLOAD: Fix missing counter update
  - CURLOPT_ACCEPT_ENCODING.3: List them comma-separated
  - CURLOPT_SSL_CTX_FUNCTION.3: Might cause accidental connection reuse
  - Curl_getoff_all_pipelines: Improved for multiplexed
  - DEPRECATE: Remove release date from 7.62.0
  - HTTP: Don't attempt to needlessly decompress redirect body
  - INTERNALS: Require GnuTLS ≥ 2.11.3
  - README.md: Add LGTM.com code quality grade for C/C++
  - SSLCERTS: Improve the openssl command line
  - Silence GCC 8 cast-function-type warnings
  - ares: Check for NULL in completed-callback
  - asyn-thread: Remove unused macro
  - auth: Only pick CURLAUTH_BEARER if we *have* a Bearer token
  - auth: Pick Bearer authentication whenever a token is available
  - cmake: CMake config files are defining CURL_STATICLIB for static builds
  - cmake: Respect BUILD_SHARED_LIBS
  - cmake: Update scripts to use consistent style
  - cmake: Bumped minimum version to 3.4
  - cmake: Link curl to the OpenSSL targets instead of lib absolute paths
  - configure: Conditionally enable pedantic-errors
  - configure: Fix for -lpthread detection with OpenSSL and pkg-config
  - conn: Remove the boolean 'inuse' field
  - content_encoding: Accept up to 4 unknown trailer bytes after raw deflate data
  - cookie tests: Treat files as text
  - cookies: Support creation-time attribute for cookies
  - curl: Fix segfault when -H @headerfile is empty
  - curl: Add http code 408 to transient list for --retry
  - curl: Fix time-of-check, time-of-use race in dir creation
  - curl: Use Content-Disposition before the "URL end" for -OJ
  - curl: Warn the user if a given file name looks like an option
  - curl_threads: Silence bad-function-cast warning
  - darwinssl: Add support for ALPN negotiation
  - docs/CURLOPT_URL: Fix indentation
  - docs/CURLOPT_WRITEFUNCTION: Size is always 1
  - docs/SECURITY-PROCESS: Mention bounty, drop pre-notify
  - docs/examples: Add hiperfifo example using linux epoll/timerfd
  - docs: Add disallow-username-in-url.d and haproxy-protocol.d to dist
  - docs: Clarify NO_PROXY env variable functionality
  - docs: Improved the manual pages of some callbacks
  - docs: Mention NULL is fine input to several functions
  - formdata: Remove unused macro HTTPPOST_CONTENTTYPE_DEFAULT
  - gopher: Do not translate '?' to '%%09'
  - header output: Switch off all styles, not just unbold
  - hostip: Fix unused variable warning
  - http2: Use correct format identifier for stream_id
  - http2: Abort the send_callback if not setup yet
  - http2: Avoid set_stream_user_data() before stream is assigned
  - http2: Check nghttp2_session_set_stream_user_data return code
  - http2: Clear the drain counter in Curl_http2_done
  - http2: Make sure to send after RST_STREAM
  - http2: Separate easy handle from connections better
  - http: Fix for tiny "HTTP/0.9" response
  - http_proxy: Remove unused macro SELECT_TIMEOUT
  - lib/Makefile: Only do symbol hiding if told to
  - lib1502: Fix memory leak in torture test
  - lib1522: Fix curl_easy_setopt argument type
  - libcurl-thread.3: Expand somewhat on the NO_SIGNAL motivation
  - mime: Check Curl_rand_hex's return code
  - multi: Always do the COMPLETED procedure/state
  - openssl: Assume engine support in 1.0.0 or later
  - openssl: Fix debug messages
  - projects: Improve Windows perl detection in batch scripts
  - retry: Return error if rewind was necessary but didn't happen
  - reuse_conn(): Memory leak - free old_conn->options
  - schannel: Client certificate store opening fix
  - schannel: Enable CALG_TLS1PRF for w32api ≥ 5.1
  - schannel: Fix MinGW compile break
  - sftp: Don't send post-quote sequence when retrying a connection
  - smb: Fix memory leak on early failure
  - smb: Fix memory-leak in URL parse error path
  - smb_getsock: Always wait for write socket too
  - ssh-libssh: Fix infinite connect loop on invalid private key
  - ssh-libssh: Reduce excessive verbose output about pubkey auth
  - ssh-libssh: Use FALLTHROUGH to silence gcc8
  - ssl: Set engine implicitly when a PKCS#11 URI is provided
  - sws: Handle EINTR when calling select()
  - system_win32: Fix version checking
  - telnet: Remove unused macros TELOPTS and TELCMDS
  - test1143: Disable MSYS2's POSIX path conversion
  - test1148: Disable if decimal separator is not point
  - test1307: (fnmatch testing) disabled
  - test1422: Add required file feature
  - test1531: Add timeout
  - test1540: Remove unused macro TEST_HANG_TIMEOUT
  - test214: Disable MSYS2's POSIX path conversion for URL
  - test320: Treat curl320.out file as binary
  - tests/http_pipe.py: Use /usr/bin/env to find python
  - tests: Don't use Windows path %%PWD for SSH tests
  - tests: Fixes for Windows line endings
  - tool_operate: Fix setting proxy TLS 1.3 ciphers
  - travis: Build darwinssl on macos 10.12 to fix linker errors
  - travis: Execute "set -eo pipefail" for coverage build
  - travis: Run a 'make checksrc' too
  - travis: Update to GCC-8
  - travis: Verify that man pages can be regenerated
  - upload: Allocate upload buffer on-demand
  - upload: Change default UPLOAD_BUFSIZE to 64KB
  - urldata: Remove unused pipe_broke struct field
  - vtls: Re-instantiate engine on duplicated handles
  - windows: Implement send buffer tuning
  - wolfSSL/CyaSSL: Fix memory leak in Curl_cyassl_random

* Tue Sep  4 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-8.0.cf
- Make the --tls13-ciphers option work

* Tue Aug 28 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-7.0.cf
- tests: Make ssh-keygen always produce PEM format (#1622594)

* Wed Aug 15 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-6.0.cf
- scp/sftp: Fix infinite connect loop on invalid private key (#1595135)

* Mon Aug 13 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-5.0.cf
- ssl: Set engine implicitly when a PKCS#11 URI is provided (#1219544)
- Relax crypto policy for the test-suite to make it pass again (#1610888)

* Tue Jul 31 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-3.0.cf
- Adapt test 323 for updated OpenSSL

* Fri Jul 13 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-2.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Wed Jul 11 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-1.0.cf
- Update to 7.61.0
  - CVE-2018-0500: smtp: Fix SMTP send buffer overflow
  - getinfo: Add microsecond precise timers for seven intervals
  - curl: Show headers in bold, switch off with --no-styled-output
  - httpauth: Add support for Bearer tokens
  - Add CURLOPT_TLS13_CIPHERS and CURLOPT_PROXY_TLS13_CIPHERS
  - curl: --tls13-ciphers and --proxy-tls13-ciphers
  - Add CURLOPT_DISALLOW_USERNAME_IN_URL
  - curl: --disallow-username-in-url
  - schannel: Disable client cert option if APIs not available
  - schannel: Disable manual verify if APIs not available
  - tests/libtest/Makefile: Do not unconditionally add gcc-specific flags
  - openssl: Acknowledge --tls-max for default version too
  - stub_gssapi: Fix 'unused parameter' warnings
  - examples/progressfunc: Make it build on both new and old libcurls
  - docs: Mention it is HA Proxy protocol "version 1"
  - curl_fnmatch: Only allow two asterisks for matching
  - docs: Clarify CURLOPT_HTTPGET
  - configure: Replace a AC_TRY_RUN with CURL_RUN_IFELSE
  - configure: Do compile-time SIZEOF checks instead of run-time
  - checksrc: Make sure sizeof() is used *with* parentheses
  - CURLOPT_ACCEPT_ENCODING.3: Add brotli and clarify a bit
  - schannel: Make CAinfo parsing resilient to CR/LF
  - tftp: Make sure error is zero terminated before printfing it
  - http resume: Skip body if http code 416 (range error) is ignored
  - configure: Add basic test of --with-ssl prefix
  - cmake: Set -d postfix for debug builds
  - multi: Provide a socket to wait for in Curl_protocol_getsock
  - content_encoding: Handle zlib versions too old for Z_BLOCK
  - winbuild: Only delete OUTFILE if it exists
  - winbuild: In MakefileBuild.vc fix typo DISTDIR->DIRDIST
  - schannel: Add failf calls for client certificate failures
  - cmake: Fix the test for fsetxattr and strerror_r
  - curl.1: Fix cmdline-opts reference errors
  - cmdline-opts/gen.pl: Warn if mutexes: or see-also: list non-existing options
  - cmake: Check for getpwuid_r
  - configure: Fix ssh2 linking when built with a static mbedtls
  - psl: Use latest psl and refresh it periodically
  - fnmatch: Insist on escaped bracket to match
  - KNOWN_BUGS: Restore text regarding #2101
  - INSTALL: LDFLAGS=-Wl,-R/usr/local/ssl/lib
  - configure: Override AR_FLAGS to silence warning
  - os400: Implement mime api EBCDIC wrappers
  - curl.rc: Embed manifest for correct Windows version detection
  - strictness: Correct {infof, failf} format specifiers
  - tests: Update .gitignore for libtests
  - configure: Check for declaration of getpwuid_r
  - fnmatch: Use the system one if available
  - CURLOPT_RESOLVE: Always purge old entry first
  - multi: Remove a potentially bad DEBUGF()
  - curl_addrinfo: Use same #ifdef conditions in source as header
  - build: Remove the Borland specific makefiles
  - axTLS: Not considered fit for use
  - cmdline-opts/cert-type.d: Mention "p12" as a recognized type
  - system.h: Add support for IBM xlc C compiler
  - tests/libtest: Add lib1521 to nodist_SOURCES
  - mk-ca-bundle.pl: Leave certificate name untouched
  - boringssl + schannel: undef X509_NAME in lib/schannel.h
  - openssl: Assume engine support in 1.0.1 or later
  - cppcheck: Fix warnings
  - test 46: Make test pass after year 2025
  - schannel: Support selecting ciphers
  - Curl_debug: Remove dead printhost code
  - test 1455: Unflakified
  - Curl_init_do: Handle NULL connection pointer passed in
  - progress: Remove a set of unused defines
  - mk-ca-bundle.pl: Make -u delete certdata.txt if found not changed
  - GOVERNANCE.md: Explains how this project is run
  - configure: Use pkg-config for c-ares detection
  - configure: Enhance ability to build with static openssl
  - maketgz: Fix sed issues on OSX
  - multi: Fix memory leak when stopped during name resolve
  - CURLOPT_INTERFACE.3: Interface names not supported on Windows
  - url: Fix dangling conn->data pointer
  - cmake: Allow multiple SSL backends
  - system.h: Fix for gcc on 32 bit OpenServer
  - ConnectionExists: Make sure conn->data is set when "taking" a connection
  - multi: Fix crash due to dangling entry in connect-pending list
  - CURLOPT_SSL_VERIFYPEER.3: Add performance note
  - netrc: Use a larger buffer to support longer passwords 
  - url: Check Curl_conncache_add_conn return code
  - configure: Add dependent libraries after crypto
  - easy_perform: Faster local name resolves by using *multi_timeout()
  - getnameinfo: Not used, removed all configure checks
  - travis: Add a build using the synchronous name resolver
  - CURLINFO_TLS_SSL_PTR.3: Improve the example
  - openssl: Allow TLS 1.3 by default
  - openssl: Make the requested TLS version the *minimum* wanted
  - openssl: Remove some dead code
  - telnet: Fix clang warnings
  - DEPRECATE: New doc describing planned item removals
  - example/crawler.c: Simple crawler based on libxml2
  - libssh: Goto DISCONNECT state on error, not SESSION_FREE
  - CMake: Remove unused functions
  - darwinssl: Allow High Sierra users to build the code using GCC
  - scripts: Include _curl as part of CLEANFILES
  - examples: Fix -Wformat warnings
  - curl_setup: Include <winerror.h> before <windows.h>
  - schannel: Make more cipher options conditional
  - CMake: Remove redundant and old end-of-block syntax
  - post303.d: Clarify that this is an RFC violation
- Add patch to fix builds with openssl < 1.0.1

* Tue Jul 10 2018 Paul Howarth <paul@city-fan.org> - 7.60.0-3.0.cf
- Disable flaky test 1455
- Enable support for brotli compression in libcurl-full from F-29 onwards

* Wed Jul  4 2018 Paul Howarth <paul@city-fan.org> - 7.60.0-2.0.cf
- Do not hard-wire path of the Python 3 interpreter

* Wed May 16 2018 Paul Howarth <paul@city-fan.org> - 7.60.0-1.0.cf
- Update to 7.60.0
  - Add CURLOPT_HAPROXYPROTOCOL, support for the HAProxy PROXY protocol
  - Add --haproxy-protocol for the command line tool
  - Add CURLOPT_DNS_SHUFFLE_ADDRESSES, shuffle returned IP addresses
  - FTP: Shutdown response buffer overflow CVE-2018-1000300
  - RTSP: Bad headers buffer over-read CVE-2018-1000301
  - FTP: Fix typo in recursive callback detection for seeking
  - test1208: Marked flaky
  - HTTP: Make header-less responses still count correct body size
  - user-agent.d: Mention --proxy-header as well
  - http2: fixes typo
  - cleanup: Misc typos in strings and comments
  - rate-limit: Use three second window to better handle high speeds
  - examples/hiperfifo.c: Improved
  - pause: When changing pause state, update socket state
  - multi: Improved pending transfers handling ⇒ improved performance
  - curl_version_info.3: Fix ssl_version description
  - add_handle/easy_perform: Clear errorbuffer on start if set
  - darwinssl: Fix iOS build
  - cmake: Add support for brotli
  - parsedate: Support UT timezone
  - vauth/ntlm.h: Fix the #ifdef header guard
  - lib/curl_path.h: Added #ifdef header guard
  - vauth/cleartext: Fix integer overflow check
  - CURLINFO_COOKIELIST.3: Made the example not leak memory
  - cookie.d: Mention that "-" as filename means stdin
  - CURLINFO_SSL_VERIFYRESULT.3: Fixed the example
  - http2: Read pending frames (including GOAWAY) in connection-check
  - timeval: Remove compilation warning by casting
  - cmake: Avoid warn-as-error during config checks
  - travis-ci: Enable -Werror for CMake builds
  - openldap: Fix for NULL return from ldap_get_attribute_ber()
  - threaded resolver: Track resolver time and set suitable timeout values
  - cmake: Add advapi32 as explicit link library for win32
  - docs: Fix CURLINFO_*_T examples use of CURL_FORMAT_CURL_OFF_T
  - test1148: Set a fixed locale for the test
  - cookies: When reading from a file, only remove_expired once
  - cookie: Store cookies per top-level-domain-specific hash table
  - openssl: Fix build with LibreSSL 2.7
  - tls: Fix mbedTLS 2.7.0 build + handle sha256 failures
  - openssl: RESTORED verify locations when verifypeer==0
  - file: Restore old behaviour for file:////foo/bar URLs
  - FTP: Allow PASV on IPv6 connections when a proxy is being used
  - build-openssl.bat: Allow custom paths for VS and perl
  - winbuild: Make the clean target work without build-type
  - build-openssl.bat: Refer to VS2017 as VC14.1 instead of VC15
  - curl: Retry on FTP 4xx, ignore other protocols
  - configure: Detect (and use) sa_family_t
  - examples/sftpuploadresume: Fix Windows large file seek
  - build: Clean up to fix clang warnings/errors
  - winbuild: Updated the documentation
  - lib: Silence null-dereference warnings
  - travis: Bump to clang 6 and gcc 7
  - travis: Build libpsl and make builds use it
  - proxy: Show getenv proxy use in verbose output
  - duphandle: Make sure CURLOPT_RESOLVE is duplicated
  - all: Refactor malloc+memset to use calloc
  - checksrc: Fix typo
  - system.h: Add sparcv8plus to oracle/sunpro 32-bit detection
  - vauth: Fix typo
  - ssh: Show libSSH2 error code when closing fails
  - test1148: Tolerate progress updates better
  - urldata: Make service names unconditional
  - configure: Keep LD_LIBRARY_PATH changes local
  - ntlm_sspi: Fix authentication using Credential Manager
  - schannel: Add client certificate authentication
  - winbuild: Support custom devel paths for each dependency
  - schannel: Add support for CURLOPT_CAINFO
  - http2: Handle on_begin_headers() called more than once
  - openssl: Support OpenSSL 1.1.1 verbose-mode trace messages
  - openssl: Fix subjectAltName check on non-ASCII platforms
  - http2: Avoid strstr() on data not zero terminated
  - http2: Clear the "drain counter" when a stream is closed
  - http2: Handle GOAWAY properly
  - tool_help: Clarify --max-time unit of time is seconds
  - curl.1: Clarify that options and URLs can be mixed
  - http2: Convert an assert to run-time check
  - curl_global_sslset: Always provide available backends
  - ftplistparser: Keep state between invokes
  - Curl_memchr: Zero length input can't match
  - examples/sftpuploadresume: typecast fseek argument to long
  - examples/http2-upload: Expand buffer to avoid silly warning
  - ctype: Restore character classification for non-ASCII platforms
  - mime: Avoid NULL pointer dereference risk
  - cookies: Ensure that we have cookies before writing jar
  - os400.c: Fix checksrc warnings
  - configure: Provide --with-wolfssl as an alias for --with-cyassl
  - cyassl: Adapt to libraries without TLS 1.0 support built-in
  - http2: Get rid of another strstr
  - checksrc: Force indentation of lines after an else
  - cookies: Remove unused macro
  - CURLINFO_PROTOCOL.3: Mention the existing defined names
  - tests: Provide 'manual' as a feature to optionally require
  - travis: Enable libssh2 on both macos and Linux
  - CURLOPT_URL.3: Added ENCODING section
  - wolfssl: Fix non-blocking connect
  - vtls: Don't define MD5_DIGEST_LENGTH for wolfssl
  - docs: Remove extraneous commas in man pages
  - URL: Fix ASCII dependency in strcpy_url and strlen_url
  - ssh-libssh.c: Fix left shift compiler warning
  - configure: Only check for CA bundle for file-using SSL backends
  - travis: Add an mbedtls build
  - http: Don't set the "rewind" flag when not uploading anything
  - configure: Put CURLDEBUG and DEBUGBUILD in lib/curl_config.h
  - transfer: Don't unset writesockfd on setup of multiplexed conns
  - vtls: Use unified "supports" bitfield member in backends
  - URLs: Fix one more http url
  - travis: Add a build using WolfSSL
  - openssl: Change FILE ops to BIO ops
  - travis: Add build using NSS
  - smb: Reject negative file sizes
  - cookies: Accept parameter names as cookie name
  - http2: getsock fix for uploads
  - All over: Fixed format specifiers
  - http2: Use the correct function pointer typedef

* Thu Mar 15 2018 Paul Howarth <paul@city-fan.org> - 7.59.0-3.0.cf
- Run the test suite using Python 3 from Fedora 28 onwards

* Wed Mar 14 2018 Paul Howarth <paul@city-fan.org> - 7.59.0-2.0.cf
- ftp: Fix typo in recursive callback detection for seeking

* Wed Mar 14 2018 Paul Howarth <paul@city-fan.org> - 7.59.0-1.0.cf
- Update to 7.59.0
  - curl: Add --proxy-pinnedpubkey
  - Added: CURLOPT_TIMEVALUE_LARGE and CURLINFO_FILETIME_T
  - CURLOPT_RESOLVE: Add support for multiple IP addresses per entry
  - Add option CURLOPT_HAPPY_EYEBALLS_TIMEOUT_MS
  - Add new tool option --happy-eyeballs-timeout-ms
  - Add CURLOPT_RESOLVER_START_FUNCTION and CURLOPT_RESOLVER_START_DATA
  - openldap: Check ldap_get_attribute_ber() results for NULL before using
    (fixes CVE-2018-1000121)
  - FTP: Reject path components with control codes (fixes CVE-2018-1000120)
  - readwrite: Make sure excess reads don't go beyond buffer end (fixes
    CVE-2018-1000122)
  - lib555: Drop text conversion and encode data as ASCII codes
  - lib517: Make variable static to avoid compiler warning
  - lib544: Sync ASCII code data with textual data
  - GSKit: Restore pinnedpubkey functionality
  - darwinssl: Don't import client certificates into Keychain on macOS
  - parsedate: Fix date parsing for systems with 32 bit long
  - openssl: Fix pinned public key build error in FIPS mode
  - SChannel/WinSSL: Implement public key pinning
  - cookies: Remove verbose "cookie size:" output
  - progress-bar: Don't use stderr explicitly, use bar->out
  - Fixes for MSDOS
  - build: Open VC15 projects with VS 2017
  - curl_ctype: Private is*() type macros and functions
  - configure: Set PATH_SEPARATOR to colon for PATH w/o separator
  - winbuild: Make linker generate proper PDB
  - curl_easy_reset: Clear digest auth state
  - curl/curl.h: Fix comment typo for CURLOPT_DNS_LOCAL_IP6
  - range: Commonize FTP and FILE range handling
  - progress-bar docs: Update to match implementation
  - fnmatch: Do not match the empty string with a character set
  - fnmatch: Accept an alphanum to be followed by a non-alphanum in char set
  - build: Fix termios issue on android cross-compile
  - getdate: Return -1 for out of range
  - formdata: Use the mime-content type function
  - time-cond: Fix reading the file modification time on Windows
  - build-openssl.bat: Extend VC15 support to include Enterprise and Professional
  - build-wolfssl.bat: Extend VC15 support to include Enterprise and Professional
  - openssl: Don't add verify locations when verifypeer==0
  - fnmatch: Optimize processing of consecutive *s and ?s pattern characters
  - schannel: Fix compiler warnings
  - content_encoding: Add "none" alias to "identity"
  - get_posix_time: Only check for overflows if they can happen
  - http_chunks: Don't write chunks twice with CURLOPT_HTTP_TRANSFER_DECODING
  - README: Language fix
  - sha256: Build with OpenSSL < 0.9.8
  - smtp: Fix processing of initial dot in data
  - --tlsauthtype: Works only if libcurl is built with TLS-SRP support
  - tests: New tests for http raw mode
  - libcurl-security.3: man page discussion security concerns when using libcurl
  - curl_gssapi: Make sure this file too uses our *printf()
  - BINDINGS: Fix curb link (and remove ruby-curl-multi)
  - nss: Use PK11_CreateManagedGenericObject() if available
  - travis: Add build with iconv enabled
  - ssh: Add two missing state names
  - CURLOPT_HEADERFUNCTION.3: Mention folded headers
  - http: Fix the max header length detection logic
  - header callback: Don't chop headers into smaller pieces
  - CURLOPT_HEADER.3: Clarify problems with different data sizes
  - curl --version: Show PSL if the run-time lib has it enabled
  - examples/sftpuploadresume: Resume upload via CURLOPT_APPEND
  - Return error if called recursively from within callbacks
  - sasl: Prefer PLAIN mechanism over LOGIN
  - winbuild: Use CALL to run batch scripts
  - curl_share_setopt.3: Connection cache is shared within multi handles
  - winbuild: Use macros for the names of some build utilities
  - projects/README: Remove reference to dead IDN link/package
  - lib655: Silence compiler warning
  - configure: Fix version check for OpenSSL 1.1.1
  - docs/MANUAL: formfind.pl is not accessible on the site anymore
  - unit1309: Fix warning on Windows x64
  - unit1307: Proper cleanup on OOM to fix torture tests
  - curl_ctype: Fix macro redefinition warnings
  - build: Get CFLAGS (including -werror) used for examples and tests
  - NO_PROXY: Fix for IPv6 numericals in the URL
  - krb5: Use nondeprecated functions
  - winbuild: Prefer documented zlib library names
  - http2: Mark the connection for close on GOAWAY
  - limit-rate: Kick in even before "limit" data has been received
  - HTTP: Allow "header;" to replace an internal header with a blank one
  - http2: Verbose output new MAX_CONCURRENT_STREAMS values
  - SECURITY: Distros' max embargo time is 14 days
  - curl tool: Accept --compressed also if Brotli is enabled and zlib is not
  - WolfSSL: Adding TLSv1.3
  - checksrc.pl: Add -i and -m options
  - CURLOPT_COOKIEFILE.3: "-" as file name means stdin

* Mon Mar 12 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-8.0.cf
- http2: mark the connection for close on GOAWAY

* Mon Feb 19 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-7.0.cf
- Add explicitly-used build requirements
- Fix libcurl soname version number in %%files list to avoid accidental soname
  bumps

* Thu Feb 15 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-6.0.cf
- Drop ldconfig scriptlets from Fedora 28 onwards

* Tue Feb 13 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-5.0.cf
- Drop temporary work around for ICE on x86_64 (#1540549)

* Fri Feb  9 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-4.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Wed Jan 31 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-3.0.cf
- Temporarily work around internal compiler error on x86_64 (#1540549)
- Disable brp-ldconfig to make RemovePathPostfixes work with shared libs again

* Thu Jan 25 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-2.0.cf
- Use libssh (instead of libssh2) to implement SCP/SFTP in libcurl from
  Fedora 28 onwards (#1531483)

* Wed Jan 24 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-1.0.cf
- Update to 7.58.0
  - New libssh-powered SSH SCP/SFTP back-end
  - curl-config: Add --ssl-backends
  - http2: Fix incorrect trailer buffer size (CVE-2018-1000005)
  - http: Prevent custom Authorization headers in redirects (CVE-2018-1000007)
  - travis: Add boringssl build
  - examples/xmlstream.c: Don't switch off CURL_GLOBAL_SSL
  - SSL: Avoid magic allocation of SSL backend specific data
  - lib: Don't export all symbols, just everything curl_*
  - libssh2: Send the correct CURLE error code on scp file not found
  - libssh2: Return CURLE_UPLOAD_FAILED on failure to upload
  - openssl: Enable pkcs12 in boringssl builds
  - libssh2: Remove dead code from SSH_SFTP_QUOTE
  - sasl_getmessage: Make sure we have a long enough string to pass
  - conncache: Fix several lock issues
  - threaded-shared-conn.c: New example
  - conncache: Only allow multiplexing within same multi handle
  - configure: Check for netinet/in6.h
  - URL: Tolerate backslash after drive letter for FILE:
  - openldap: Add commented out debug possibilities
  - include: Get netinet/in.h before linux/tcp.h
  - CONNECT: Keep close connection flag in http_connect_state struct
  - BINDINGS: Another PostgreSQL client
  - curl: Limit -# update frequency for unknown total size
  - configure: Add AX_CODE_COVERAGE only if using gcc
  - curl.h: Remove incorrect comment about ERRORBUFFER
  - openssl: Improve data-pending check for https proxy
  - curl: Remove __EMX__ #ifdefs
  - CURLOPT_PRIVATE.3: Fix grammar
  - sftp: Allow quoted commands to use relative paths
  - CURLOPT_DNS_CACHE_TIMEOUT.3: See also CURLOPT_RESOLVE
  - RESOLVE: Output verbose text when trying to set a duplicate name
  - openssl: Disable file buffering for Win32 SSLKEYLOGFILE
  - multi_done: Prune DNS cache
  - tests: Update .gitignore for libtests
  - tests: Mark data files as non-executable in git
  - CURLOPT_DNS_LOCAL_IP4.3: Fixed the "SEE ALSO" to not self-reference
  - curl.1: Documented two missing valid exit codes
  - curl.1: Mention http:// and https:// as valid proxy prefixes
  - vtls: Replaced getenv() with curl_getenv()
  - setopt: Less *or equal* than INT_MAX/1000 should be fine
  - examples/smtp-mail.c: Use separate defines for options and mail
  - curl: Support >256 bytes warning messages
  - conncache: Fix a return code
  - krb5: Fix a potential access of uninitialized memory
  - rand: Add a clang-analyzer work-around
  - CURLOPT_READFUNCTION.3: Refer to argument with correct name
  - brotli: Allow compiling with version 0.6.0
  - content_encoding: Rework zlib_inflate
  - curl_easy_reset: Release mime-related data
  - examples/rtsp: Fix error handling macros
  - build-openssl.bat: Added support for VC15
  - build-wolfssl.bat: Added support for VC15
  - build: Added Visual Studio 2017 project files
  - winbuild: Added support for VC15
  - curl: Support size modifiers for --max-filesize
  - examples/cacertinmem: Ignore cert-already-exists error
  - brotli: Data at the end of content can be lost
  - curl_version_info.3: Call the argument 'age'
  - openssl: Fix memory leak of SSLKEYLOGFILE filename
  - build: Remove HAVE_LIMITS_H check
  - --mail-rcpt: Fix short-text description
  - scripts: Allow all perl scripts to be run directly
  - progress: Calculate transfer speed on milliseconds if possible
  - system.h: Check __LONG_MAX__ for defining curl_off_t
  - easy: Fix connection ownership in curl_easy_pause
  - setopt: Reintroduce non-static Curl_vsetopt() for OS400 support
  - setopt: Fix SSLVERSION to allow CURL_SSLVERSION_MAX_ values
  - configure.ac: Append extra linker flags instead of prepending them
  - HTTP: Bail out on negative Content-Length: values
  - docs: Comment about CURLE_READ_ERROR returned by curl_mime_filedata
  - mime: Clone mime tree upon easy handle duplication
  - openssl: Enable SSLKEYLOGFILE support by default
  - smtp/pop3/imap_get_message: Decrease the data length too...
  - CURLOPT_TCP_NODELAY.3: Fix typo
  - SMB: Fix numeric constant suffix and variable types
  - ftp-wildcard: Fix matching an empty string with "*[^a]"
  - curl_fnmatch: only allow 5 '*' sections in a single pattern
  - openssl: Fix potential memory leak in SSLKEYLOGFILE logic
  - SSH: Fix state machine for ssh-agent authentication
  - examples/url2file.c: Add missing curl_global_cleanup() call
  - http2: Don't close connection when single transfer is stopped
  - libcurl-env.3: First version
  - curl: Progress bar refresh, get width using ioctl()
  - CONNECT_TO: Fail attempt to set an IPv6 numerical without IPv6 support

* Wed Nov 29 2017 Paul Howarth <paul@city-fan.org> - 7.57.0-1.0.cf
- Update to 7.57.0
  - auth: Add support for RFC7616 - HTTP Digest access authentication
  - share: Add support for sharing the connection cache
  - HTTP: Implement Brotli content encoding
  - Fix CVE-2017-8816: NTLM buffer overflow via integer overflow
  - Fix CVE-2017-8817: FTP wildcard out of bounds read
  - Fix CVE-2017-8818: SSL out of buffer access
  - curl_mime_filedata.3: Fix typos
  - libtest: Add required test libraries for lib1552 and lib1553
  - Fix time diffs for systems using unsigned time_t
  - ftplistparser: Memory leak fix: always free temporary memory
  - multi: Allow table handle sizes to be overridden
  - wildcards: Don't use with non-supported protocols
  - curl_fnmatch: Return error on illegal wildcard pattern
  - transfer: Fix chunked-encoding upload too early exit
  - curl_setup: Improve detection of CURL_WINDOWS_APP
  - resolvers: Only include anything if needed
  - setopt: Fix CURLOPT_SSH_AUTH_TYPES option read
  - appveyor: Add a win32 build
  - Curl_timeleft: Change return type to timediff_t
  - cmake: Export libcurl and curl targets to use by other cmake projects
  - curl: In -F option arg, comma is a delimiter for files only
  - curl: Improved ";type=" handling in -F option arguments
  - timeval: Use mach_absolute_time() on MacOS
  - curlx: The timeval functions are no longer provided as curlx_*
  - mkhelp.pl: Do not generate comment with current date
  - memdebug: Use send/recv signature for curl_dosend/curl_dorecv
  - cookie: Avoid NULL dereference
  - url: Fix CURLOPT_POSTFIELDSIZE arg value check to allow -1
  - include: Remove conncache.h inclusion from where it's not needed
  - CURLOPT_MAXREDIRS: Allow -1 as a value
  - tests: Fixed torture tests on tests 556 and 650
  - http2: Fixed OOM handling in upgrade request
  - url: Fix CURLOPT_DNS_CACHE_TIMEOUT arg value check to allow -1
  - CURLOPT_INFILESIZE: Accept -1
  - curl: Pass through [] in URLs instead of calling globbing error
  - curl: Speed up handling of many URLs
  - ntlm: Avoid malloc(0) for zero length passwords
  - url: Remove faulty arg value check from CURLOPT_SSH_AUTH_TYPES
  - HTTP: Support multiple Content-Encodings
  - travis: Add a job with brotli enabled
  - url: Remove unnecessary NULL-check
  - fnmatch: Remove dead code
  - connect: Store IPv6 connection status after valid connection
  - imap: Deal with commands case insensitively
  - --interface: Add support for Linux VRF
  - content_encoding: Fix inflate_stream for no bytes available
  - cmake: Correctly include curl.rc in Windows builds
  - cmake: Add missing setmode check
  - connect.c: Remove executable bit on file
  - SMB: Fix uninitialized local variable
  - zlib/brotli: Only include header files in modules needing them
  - URL: Return error on malformed URLs with junk after IPv6 bracket
  - openssl: Fix too broad use of HAVE_OPAQUE_EVP_PKEY
  - macOS: Fix missing connectx function with Xcode version older than 9.0
  - --resolve: Allow IP address within [] brackets
  - examples/curlx: Fix code style
  - ntlm: Remove unnecessary NULL-check to please scan-build
  - Curl_llist_remove: Fix potential NULL pointer deref
  - mime: Fix "Value stored to 'sz' is never read" scan-build error
  - openssl: Fix "Value stored to 'rc' is never read" scan-build error
  - http2: Fix "Value stored to 'hdbuf' is never read" scan-build error
  - http2: Fix "Value stored to 'end' is never read" scan-build error
  - Curl_open: Fix OOM return error correctly
  - url: Reject ASCII control characters and space in host names
  - examples/rtsp: Clear RANGE again after use
  - connect: Improve the bind error message
  - make: Fix "make distclean"
  - connect: Add support for new TCP Fast Open API on Linux
  - metalink: Fix memory leak and NULL pointer dereference
  - URL: Update "file:" URL handling
  - ssh: Remove check for a NULL pointer
  - global_init: Ignore CURL_GLOBAL_SSL's absence

* Mon Oct 23 2017 Paul Howarth <paul@city-fan.org> - 7.56.1-1.0.cf
- Update to 7.56.1
  - imap: If a FETCH response has no size, don't call write callback
    (CVE-2017-1000257)
  - ftp: UBsan fixup 'pointer index expression overflowed
  - failf: Skip the sprintf() if there are no consumers
  - fuzzer: Move to using external curl-fuzzer
  - lib/Makefile.m32: Allow customizing dll suffixes
  - docs: Fix typo in curl_mime_data_cb man page
  - darwinssl: Add support for TLSv1.3
  - build: Fix --disable-crypto-auth
  - lib/config-win32.h: Let SMB/SMBS be enabled with OpenSSL/NSS
  - openssl: Fix build without HAVE_OPAQUE_EVP_PKEY
  - strtoofft: Remove extraneous null check
  - multi_cleanup: Call DONE on handles that never got that
  - tests: Added flaky keyword to tests 587 and 644
  - pingpong: Return error when trying to send without connection
  - remove_handle: Call multi_done() first, then clear dns cache pointer
  - mime: Be tolerant about setting twice the same header list in a part
  - mime: Improve unbinding top multipart from easy handle.
  - mime: Avoid resetting a part's encoder when part's contents change
  - mime: Refuse to add subparts to one of their own descendants
  - RTSP: Avoid integer overflow on funny RTSP responses
  - curl: Don't pass semicolons when parsing Content-Disposition
  - openssl: Enable PKCS12 support for !BoringSSL
  - FAQ: s/CURLOPT_PROGRESSFUNCTION/CURLOPT_XFERINFOFUNCTION
  - CURLOPT_NOPROGRESS.3: Also refer to xferinfofunction
  - CURLOPT_XFERINFODATA.3: Fix duplicate see also
  - test298: Verify --ftp-method nowcwd with URL encoded path
  - FTP: URL decode path for dir listing in nocwd mode
  - smtp_done: Fix memory leak on send failure
  - ftpserver: Support case insensitive commands
  - test950: Verify SMTP with custom request
  - openssl: Don't use old BORINGSSL_YYYYMM macros
  - setopt: Update current connection SSL verify params
  - winbuild/BUILD.WINDOWS.txt: Mention WITH_NGHTTP2
  - curl: Reimplement stdin buffering in -F option
  - mime: Keep "text/plain" content type if user-specified
  - mime: Fix the content reader to handle >16K data properly
  - configure: Remove the C++ compiler check
  - memdebug: Trace send, recv and socket
  - runtests: Use valgrind for torture as well
  - ldap: Silence clang warning
  - makefile.m32: Allow to override gcc, ar and ranlib
  - setopt: Avoid integer overflows when setting millsecond values
  - setopt: Range check most long options
  - ftp: Reject illegal IP/port in PASV 227 response
  - mime: Do not reuse previously computed multipart size
  - vtls: Change struct Curl_ssl 'close' field name to 'close_one'
  - os400: Add missing symbols in config file
  - mime: Limit bas64-encoded lines length to 76 characters
  - mk-ca-bundle: Remove URL for aurora
  - mk-ca-bundle: Fix URL for NSS

* Wed Oct  4 2017 Paul Howarth <paul@city-fan.org> - 7.56.0-1.0.cf
- Update to 7.56.0
  - curl: Enable compression for SCP/SFTP with --compressed-ssh
  - libcurl: Enable compression for SCP/SFTP with CURLOPT_SSH_COMPRESSION
  - vtls: Added dynamic changing SSL backend with curl_global_sslset()
  - New MIME API, curl_mime_init() and friends
  - openssl: Initial SSLKEYLOGFILE implementation
  - FTP: zero terminate the entry path even on bad input (CVE-2017-1000254)
  - examples/ftpuploadresume.c: Use portable code
  - runtests: Match keywords case insensitively
  - travis: Build the examples too
  - strtoofft: Reduce integer overflow risks globally
  - zsh.pl: Produce a working completion script again
  - cmake: Remove dead code for CURL_DISABLE_RTMP
  - progress: Track total times following redirects
  - configure: Fix --disable-threaded-resolver
  - cmake: Remove dead code for DISABLED_THREADSAFE
  - configure: Fix clang version detection
  - darwinssl: Fix error: variable length array used
  - travis: Add metalink to some osx builds
  - configure: Check for __builtin_available() availability
  - http_proxy: Fix build error for CURL_DOES_CONVERSIONS
  - examples/ftpuploadresume: checksrc compliance
  - ftp: Fix CWD when doing multicwd then nocwd on same connection
  - system.h: Remove all CURL_SIZEOF_* defines
  - http: Don't wait on CONNECT when there is no proxy
  - system.h: Check for __ppc__ as well
  - http2_recv: Return error better on fatal h2 errors
  - scripts/contri*sh: Use "git log --use-mailmap"
  - tftp: Fix memory leak on too long filename
  - system.h: Fix build for hppa
  - cmake: Enable picky compiler options with clang and gcc
  - makefile.m32: Add support for libidn2
  - curl: Turn off MinGW CRT's globbing
  - request-target.d: Mention added in 7.55.0
  - curl: Shorten and clean up CA cert verification error message
  - imap: Support PREAUTH
  - CURLOPT_USERPWD.3: See also CURLOPT_PROXYUSERPWD
  - examples/threaded-ssl: Mention that this is for openssl before 1.1
  - winbuild: Fix embedded manifest option
  - tests: Make sure libtests and unittests call curl_global_cleanup()
  - system.h: include sys/poll.h for AIX
  - darwinssl: Handle long strings in TLS certs
  - strtooff: Fix build for systems with long long but no strtoll
  - asyn-thread: Improved cleanup after OOM situations
  - HELP-US.md: "How to get started helping out in the curl project"
  - curl.h: CURLSSLBACKEND_WOLFSSL used wrong value
  - unit1301: Fix error message on first test
  - ossfuzz: Moving towards the ideal integration
  - http: Fix a memory leakage in checkrtspprefix()
  - examples/post-callback: Stop returning one byte at a time
  - schannel: return CURLE_SSL_CACERT on failed verification
  - MAIL-ETIQUETTE: Added "1.9 Your emails are public"
  - http-proxy: Treat all 2xx as CONNECT success
  - openssl: Use OpenSSL's default ciphers by default
  - runtests.pl: Support attribute "nonewline" in part verify/upload
  - configure: Remove --enable-soname-bump and SONAME_BUMP
  - travis: Add c-ares enabled builds linux + osx
  - vtls: Fix WolfSSL 3.12 build problems
  - http-proxy: When not doing CONNECT, that phase is done immediately
  - configure: Fix curl_off_t check's include order
  - configure: Use -Wno-varargs on clang 3.9[.X] debug builds
  - rtsp: Do not call fwrite() with NULL pointer FILE *
  - mbedtls: Enable CA path processing
  - travis: Add build without HTTP/SMTP/IMAP
  - checksrc: Verify more code style rules
  - HTTP proxy: On connection re-use, still use the new remote port
  - tests: Add initial gssapi test using stub implementation
  - rtsp: Segfault when using WRITEDATA
  - docs: Clarify the CURLOPT_INTERLEAVE* options behavior
  - non-ascii: Use iconv() with 'char **' argument
  - server/getpart: Provide dummy function to build conversion enabled
  - conversions: Fix several compiler warnings
  - openssl: Add missing includes
  - schannel: Support partial send for when data is too large
  - socks: Fix incorrect port number in SOCKS4 error message
  - curl: Fix integer overflow in timeout options
- Re-enable temporarily disabled IDN2 test-cases

* Tue Aug 29 2017 Paul Howarth <paul@city-fan.org> - 7.55.1-5.0.cf
- Fix NetworkManager connectivity check not working (#1485702)

* Wed Aug 23 2017 Paul Howarth <paul@city-fan.org> - 7.55.1-3.0.cf
- Utilize system wide crypto policies for TLS (#1483972)

* Tue Aug 15 2017 Paul Howarth <paul@city-fan.org> - 7.55.1-2.0.cf
- Make zsh completion work again

* Mon Aug 14 2017 Paul Howarth <paul@city-fan.org> - 7.55.1-1.0.cf
- Update to 7.55.1
  - build: Fix 'make install' with configure, install docs/libcurl/* too
  - make install: Add 8 missing man pages to the installation
  - curl: Do bounds check using a double comparison
  - dist: Add dictserver.py/negtelnetserver.py to release
  - digest_sspi: Don't reuse context if the user/passwd has changed
  - gitignore: Ignore top-level .vs folder
  - build: Check out *.sln files with Windows line endings
  - travis: Verify "make install"
  - dist: Fix the cmake build by shipping cmake_uninstall.cmake.in too
  - metalink: Fix error: ‘*’ in boolean context, suggest ‘&&’ instead
  - configure: Use the threaded resolver backend by default if possible
  - mkhelp.pl: Allow executing this script directly
  - maketgz: Remove old *.dist files before making the tarball
  - openssl: Remove CONST_ASN1_BIT_STRING
  - openssl: Fix "error: this statement may fall through"
  - proxy: Fix memory leak in case of invalid proxy server name
  - curl/system.h: Support more architectures (OpenRISC, ARC)
  - docs: Fix typos
  - curl/system.h: Add Oracle Solaris Studio
  - CURLINFO_TOTAL_TIME: Could wrongly return 4200 seconds
  - docs: --connect-to clarified
  - cmake: Allow user to override CMAKE_DEBUG_POSTFIX
  - travis: Test cmake build on tarball too
  - redirect: Make it handle absolute redirects to IDN names
  - curl/system.h: Fix for gcc on PowerPC
  - curl --interface: Fixed for IPV6 unique local addresses
  - cmake: threads detection improvements

* Wed Aug  9 2017 Paul Howarth <paul@city-fan.org> - 7.55.0-1.1.cf
- Address some test suite issues

* Wed Aug  9 2017 Paul Howarth <paul@city-fan.org> - 7.55.0-1.0.cf
- Update to 7.55.0
  New Features:
  - curl: Allow --header and --proxy-header read from file
  - getinfo: Provide sizes as curl_off_t
  - curl: Prevent binary output spewed to terminal
  - curl: Added --request-target
  - libcurl: Added CURLOPT_REQUEST_TARGET
  - curl: Added --socks5-{basic,gssapi}: control socks5 auth
  - libcurl: Added CURLOPT_SOCKS5_AUTH
   Bug Fixes:
  - glob: Do not parse after a strtoul() overflow range (CVE-2017-1000101)
  - tftp: Reject file name lengths that don't fit (CVE-2017-1000100)
  - file: Output the correct buffer to the user (CVE-2017-1000099)
  - includes: Remove curl/curlbuild.h and curl/curlrules.h
  - dist: Make the hugehelp.c not get regenerated unnecessarily
  - timers: Store internal time stamps as time_t instead of doubles
  - progress: Let "current speed" be UL + DL speeds combined
  - http-proxy: Do the HTTP CONNECT process entirely non-blocking
  - lib/curl_setup.h: Remove CURL_WANTS_CA_BUNDLE_ENV
  - fuzz: Bring oss-fuzz initial code converted to C89
  - configure: Disable nghttp2 too if HTTP has been disabled
  - mk-ca-bundle.pl: Check curl's exit code after certdata download
  - test1148: Verify the -# progressbar
  - tests: Stabilize test 2032 and 2033
  - HTTPS-Proxy: Don't offer h2 for https proxy connections
  - http-proxy: Only attempt FTP over HTTP proxy
  - curl-compilers.m4: Enable vla warning for clang
  - curl-compilers.m4: Enable double-promotion warning
  - curl-compilers.m4: Enable missing-variable-declarations clang warning
  - curl-compilers.m4: Enable comma clang warning
  - Makefile.m32: Enable -W for MinGW32 build
  - CURLOPT_PREQUOTE: Not supported for SFTP
  - http2: Fix OOM crash
  - PIPELINING_SERVER_BL: Clean up the internal list use
  - mkhelp.pl: Fix script name in usage text
  - lib1521: Add curl_easy_getinfo calls to the test set
  - travis: Do the distcheck test build out-of-tree as well
  - if2ip: Fix compiler warning in ISO C90 mode
  - lib: Fix the djgpp build
  - typecheck-gcc: Add support for CURLINFO_OFF_T
  - travis: Enable typecheck-gcc warnings
  - maketgz: Switch to xz instead of lzma
  - CURLINFO_REDIRECT_URL.3: Mention the CURLOPT_MAXREDIRS case
  - curl-compilers.m4: Fix unknown-warning-option on Apple clang
  - winbuild: Fix boringssl build
  - curl/system.h: Add check for XTENSA for 32bit gcc
  - test1537: Fixed memory leak on OOM
  - test1521: Fix compiler warnings
  - curl: Fix memory leak on test 1147 OOM
  - libtest/make: Generate lib1521.c dynamically at build-time
  - curl_strequal.3: Fix typo in SYNOPSIS
  - progress: Prevent resetting t_starttransfer
  - openssl: Improve fallback seed of PRNG with a time based hash
  - http2: Improved PING frame handling
  - test1450: Add simple testing for DICT
  - make: Build the docs subdir only from within src
  - cmake: Added compatibility options for older Windows versions
  - gtls: Fix build when sizeof(long) < sizeof(void *)
  - url: Make the original string get used on subsequent transfers
  - timeval.c: Use long long constant type for timeval assignment
  - tool_sleep: Typecast to avoid macos compiler warning
  - travis.yml: Use --enable-werror on debug builds
  - test1451: Add SMB support to the testbed
  - configure: Remove checks for 5 functions never used
  - configure: Try ldap/lber in reversed order first
  - smb: Fix build for djgpp/MSDOS
  - travis: Install nghttp2 on linux builds
  - smb: Add support for CURLOPT_FILETIME
  - cmake: Fix send/recv argument scanner for windows
  - inet_pton: Fix include on windows to get prototype
  - select.h: Avoid macro redefinition harder
  - cmake: If inet_pton is used, bump _WIN32_WINNT
  - asyn-thread.c: Fix unused variable warnings on macOS
  - runtests: Support "threaded-resolver" as a feature
  - test506: Skip if threaded-resolver
  - cmake: Remove spurious "-l" from linker flags
  - cmake: Add CURL_WERROR for enabling "warning as errors"
  - memdebug: Don't setbuf() if the file open failed
  - curl_easy_escape.3: Mention the (lack of) encoding
  - test1452: Add telnet negotiation
  - CURLOPT_POSTFIELDS.3: Explain the 100-continue magic better
  - cmake: Offer CMAKE_DEBUG_POSTFIX when building with MSVC
  - tests/valgrind.supp: Suppress OpenSSL false positive seen on travis
  - curl_setup_once: Remove ERRNO/SET_ERRNO macros
  - curl-compilers.m4: Disable warning spam with Cygwin's clang
  - ldap: Fix MinGW compiler warning
  - make: Fix docs build on OpenBSD
  - curl_setup: Always define WIN32_LEAN_AND_MEAN on Windows
  - system.h: include winsock2.h before windows.h
  - winbuild: Build with warning level 4
  - rtspd: Fix MSVC level 4 warning
  - sockfilt: Suppress conversion warning with explicit cast
  - libtest: Fix MSVC warning C4706
  - darwinssl: Fix pinnedpubkey build error
  - tests/server/resolve.c: Fix deprecation warning
  - nss: Fix a possible use-after-free in SelectClientCert()
  - checksrc: Escape open brace in regex
  - multi: Mention integer overflow risk if using > 500 million sockets
  - darwinssl: Fix --tlsv1.2 regression
  - timeval: struct curltime is a struct timeval replacement
  - curl_rtmp: Fix a compiler warning
  - include.d: Clarify that it concerns the response headers
  - cmake: Support make uninstall
  - include.d: Clarify --include is only for response headers
  - libcurl: Stop using error codes defined under CURL_NO_OLDIES
  - http: Fix response code parser to avoid integer overflow
  - configure: Fix the check for IdnToUnicode
  - multi: Fix request timer management
  - curl_threads: Fix MSVC compiler warning
  - travis: Build on osx with openssl
  - travis: Build on osx with libressl
  - CURLOPT_NETRC.3: Mention the file name on Windows
  - cmake: Set MSVC warning level to 4
  - netrc: Skip lines starting with '#'
  - darwinssl: Fix curlssl_sha256sum() compiler warnings on first argument
  - BUILD.WINDOWS: Mention buildconf.bat for builds off git
  - darwinssl: Silence compiler warnings
  - travis: Build on osx with darwinssl
  - FTP: Skip unnecessary CWD when in nocwd mode
  - gssapi: Fix memory leak of output token in multi round context
  - getparameter: Avoid returning uninitialized 'usedarg'
  - curl (debug build) easy_events: Make event data static
  - curl: Detect and bail out early on parameter integer overflows
  - configure: Fix recv/send/select detection on Android
- Drop curlbuild.h multilib hacks
- Re-enable now-stabilized test 2033
- Disable test 1427 on i686 (failing just-added test)
- Manually install the libcurl manpages since upstream has accidentally stopped
  doing so

* Thu Aug  3 2017 Paul Howarth <paul@city-fan.org> - 7.54.1-8.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Mon Jul 31 2017 Paul Howarth <paul@city-fan.org> - 7.54.1-7.0.cf
- Enable separate debuginfo back

* Thu Jul 27 2017 Paul Howarth <paul@city-fan.org> - 7.54.1-5.0.cf
- Avoid build failure caused by broken RPM code that produces debuginfo
  packages (https://github.com/rpm-software-management/rpm/issues/280)

* Wed Jul 26 2017 Paul Howarth <paul@city-fan.org> - 7.54.1-3.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Jun 19 2017 Paul Howarth <paul@city-fan.org> - 7.54.1-2.0.cf
- Enforce versioned openssl-libs dependency for libcurl (#1462184)

* Wed Jun 14 2017 Paul Howarth <paul@city-fan.org> - 7.54.1-1.0.cf
- Update to 7.54.1
  - CVE-2017-9502: file: URL buffer overflow
  - curl: Show the libcurl release date in --version output
  - openssl: Fix memory leak in servercert
  - tests: Remove the html and PDF versions from the tarball
  - mbedtls: Enable NTLM (and SMB) even if MD4 support is unavailable
  - typecheck-gcc: Handle function pointers properly
  - llist: No longer uses malloc
  - gnutls: Removed some code when --disable-verbose is configured
  - lib: Fix maybe-uninitialized warnings
  - multi: Clarify condition in curl_multi_wait
  - schannel: Don't treat encrypted partial record as pending data
  - configure: Fix the -ldl check for openssl, add -lpthread check
  - configure: Accept -Og and -Ofast GCC flags
  - Makefile: Avoid use of GNU-specific form of $<
  - if2ip: Fix -Wcast-align warning
  - configure: Stop prepending to LDFLAGS, CPPFLAGS
  - curl: Set a 100K buffer size by default
  - typecheck-gcc: Fix _curl_is_slist_info
  - nss: Do not leak PKCS #11 slot while loading a key
  - nss: Load libnssckbi.so if no other trust is specified
  - examples: ftpuploadfrommem.c
  - url: Declare get_protocol_family() static
  - examples/cookie_interface.c: Changed to example.com
  - test1443: Test --remote-time
  - curl: Use utimes instead of obsolescent utime when available
  - url: Fixed a memory leak on OOM while setting CURLOPT_BUFFERSIZE
  - curl_rtmp: Fix missing-variable-declarations warnings
  - tests: Fixed OOM handling of unit tests to abort test
  - curl_setup: Ensure no more than one IDN lib is enabled
  - tool: Fix missing prototype warnings for CURL_DOES_CONVERSIONS
  - CURLOPT_BUFFERSIZE: 1024 bytes is now the minimum size
  - curl: Non-boolean command line args reject --no- prefixes
  - telnet: Write full buffer instead of byte-by-byte
  - typecheck-gcc: Add missing string options
  - typecheck-gcc: Add support for CURLINFO_SOCKET
  - opt man pages: They all have examples now
  - curl_setup_once: Use SEND_QUAL_ARG2 for swrite
  - test557: Set a known good numeric locale
  - schannel: Return a more specific error code for SEC_E_UNTRUSTED_ROOT
  - tests/server: Make string literals const
  - runtests: Use -R for random order
  - unit1305: Fix compiler warning
  - curl_slist_append.3: Clarify a NULL input creates a new list
  - tests/server: Run checksrc by default in debug-builds
  - tests: Fix -Wcast-qual warnings
  - runtests.pl: Simplify the datacheck read section
  - curl: Remove --environment and tool_writeenv.c
  - buildconf: Fix hang on IRIX
  - tftp: Silence bad-function-cast warning
  - asyn-thread: Fix unused macro warnings
  - tool_parsecfg: Fix -Wcast-qual warning
  - sendrecv: Fix MinGW-w64 warning
  - test537: Use correct variable type
  - rand: Treat fake entropy the same regardless of endianness
  - curl: Generate the --help output
  - tests: Removed redundant --trace-ascii arguments
  - multi: Assign IDs to all timers and make each timer singleton
  - multi: Use a fixed array of timers instead of malloc
  - mbedtls: Support server renegotiation request
  - pipeline: Fix mistakenly trying to pipeline POSTs
  - lib510: Don't write past the end of the buffer if it's too small
  - CURLOPT_HTTPPROXYTUNNEL.3: Clarify, add example
  - SecureTransport/DarwinSSL: Implement public key pinning
  - curl.1: Clarify --config
  - curl_sasl: Fix build error with CURL_DISABLE_CRYPTO_AUTH + USE_NTLM
  - darwinssl: Fix exception when processing a client-side certificate
  - curl.1: Mention --oauth2-bearer's <token> argument
  - mkhelp.pl: Do not add current time into curl binary
  - asiohiper.cpp / evhiperfifo.c: Deal with negative timerfunction input
  - ssh: Fix memory leak in disconnect due to timeout
  - tests: Stabilize test 1034
  - cmake: Auto detection of CURL_CA_BUNDLE/CURL_CA_PATH
  - assert: Avoid, use DEBUGASSERT instead
  - LDAP: Using ldap_bind_s on Windows with methods
  - redirect: Store the "would redirect to" URL when max redirs is reached
  - winbuild: Fix the nghttp2 build
  - examples: Fix -Wimplicit-fallthrough warnings
  - time: Fix type conversions and compiler warnings
  - mbedtls: Fix variable shadow warning
  - test557: Fix ubsan runtime error due to int left shift
  - transfer: Init the infilesize from the postfields
  - docs: Clarify NO_PROXY further
  - build-wolfssl: Sync config with wolfSSL 3.11
  - curl-compilers.m4: Enable -Wshift-sign-overflow for clang
  - example/externalsocket.c: Make it use CLOSESOCKETFUNCTION too
  - lib574.c: Use correct callback proto
  - lib583: Fix compiler warning
  - curl-compilers.m4: Fix compiler_num for clang
  - typecheck-gcc.h: Separate getinfo slist checks from other pointers
  - typecheck-gcc.h: Check CURLINFO_TLS_SSL_PTR and CURLINFO_TLS_SESSION
  - typecheck-gcc.h: Check CURLINFO_CERTINFO
  - build: Provide easy code coverage measuring
  - test1537: Dedicated tests of the URL (un)escape API calls
  - curl_endian: Remove unused functions
  - test1538: Verify the libcurl strerror API calls
  - MD(4|5): Silence cast-align clang warning
  - dedotdot: Fixed output for ".." and "." only input
  - cyassl: Define build macros before including ssl.h
  - updatemanpages.pl: Error out on too old git version
  - curl_sasl: Fix unused-variable warning
  - x509asn1: Fix implicit-fallthrough warning with GCC 7
  - libtest: Fix implicit-fallthrough warnings with GCC 7
  - BINDINGS: Add Ring binding
  - curl_ntlm_core: Pass unsigned char to toupper
  - test1262: Verify ftp download with -z for "if older than this"
  - test1521: Test all curl_easy_setopt options
  - typecheck-gcc: Allow CURLOPT_STDERR to be NULL too
  - metalink: Remove unused printf() argument
  - file: Make speedcheck use current time for checks
  - configure: Fix link with librtmp when specifying path
  - examples/multi-uv.c: Fix deprecated symbol
  - cmake: Fix inconsistency regarding mbed TLS include directory
  - setopt: Check CURLOPT_ADDRESS_SCOPE option range
  - gitignore: Ignore all vim swap files
  - urlglob: Fix division by zero
  - libressl: OCSP and intermediate certs workaround no longer needed
- New test 1446 segfaulting on builds for older distributions, so disable for
  now
- Update patches as needed

* Thu May  4 2017 Paul Howarth <paul@city-fan.org> - 7.54.0-4.0.cf
- Make curl-minimal require a new enough version of libcurl

* Sat Apr 29 2017 Paul Howarth <paul@city-fan.org> - 7.54.0-3.1.cf
- Don't require nss-pem for OpenSSL builds

* Thu Apr 27 2017 Paul Howarth <paul@city-fan.org> - 7.54.0-3.0.cf
- Switch the TLS backend back to OpenSSL for Fedora 27 onwards (#1445153)

* Tue Apr 25 2017 Paul Howarth <paul@city-fan.org> - 7.54.0-2.0.cf
- nss: use libnssckbi.so as the default source of trust
- nss: do not leak PKCS #11 slot while loading a key (#1444860)

* Wed Apr 19 2017 Paul Howarth <paul@city-fan.org> - 7.54.0-1.0.cf
- Update to 7.54.0
  - Add CURL_SSLVERSION_MAX_* constants to CURLOPT_SSLVERSION
  - Add --max-tls
  - Add CURLOPT_SUPPRESS_CONNECT_HEADERS
  - Add --suppress-connect-headers
  - CVE-2017-7468: switch off SSL session id when client cert is used
  - cmake: Replace invalid UTF-8 byte sequence
  - tests: Use consistent environment variables for setting charset
  - proxy: Fixed a memory leak on OOM
  - ftp: Removed an erroneous free in an OOM path
  - docs: De-duplicate file lists in the Makefiles
  - ftp: Fixed a NULL pointer dereference on OOM
  - gopher: Fixed detection of an error condition from Curl_urldecode
  - url: Fix unix-socket support for proxy-disabled builds
  - test1139: Allow for the possibility that the man page is not rebuilt
  - cyassl: Get library version string at runtime
  - digest_sspi: Fix compilation warning
  - tests: Enable HTTP/2 tests to run with non-default port numbers
  - warnless: Suppress compiler warning
  - darwinssl: Warn that disabling host verify also disables SNI
  - configure: Fix for --enable-pthreads
  - checksrc.bat: Ignore curl_config.h.in, curl_config.h
  - no-keepalive.d: Fix typo
  - configure: Fix --with-zlib when a path is specified
  - build: Fix gcc7 implicit fallthrough warnings
  - Fix potential use of uninitialized variables
  - CURLOPT_SSL_CTX_FUNCTION.3: Fix EXAMPLE formatting errors
  - CMake: Reorganize SSL support, separate WinSSL and SSPI
  - CMake: Add DarwinSSL support
  - CMake: Add mbedTLS support
  - ares: Return error at once if timed out before name resolve starts
  - BINDINGS: Added C++, perl, go and Scilab bindings
  - URL: Return error on malformed URLs with junk after port number
  - KNOWN_BUGS: Add DarwinSSL won't import PKCS#12 without a password
  - http2: Fix assertion error on redirect with CL=0
  - updatemanpages.pl: Update man pages to use current date and versions
  - --insecure: Clarify that this option is for server connections
  - mkhelp: Simplified the gzip code
  - build: Fixed making man page in out-of-tree tarball builds
  - tests: Disabled 1903 due to flakiness
  - openssl: Add two /* FALLTHROUGH */ to satisfy coverity
  - cmdline-opts: Fixed a few typos
  - authneg: Clear auth.multi flag at http_done
  - curl_easy_reset: Also reset the authentication state
  - proxy: Skip SSL initialization for closed connections
  - http_proxy: Ignore TE and CL in CONNECT 2xx responses
  - tool_writeout: Fixed a buffer read overrun on --write-out
  - make: Regenerate docs/curl.1 by running make in docs
  - winbuild: Add basic support for OpenSSL 1.1.x
  - build: Removed redundant DEPENDENCIES from makefiles
  - CURLINFO_LOCAL_PORT.3: Added example
  - curl: Show HTTPS-Proxy options on CURLE_SSL_CACERT
  - tests: Strip more options from non-HTTP --libcurl tests
  - tests: Fixed the documented test server port numbers
  - runtests.pl: Fixed display of the Gopher IPv6 port number
  - multi: Fix streamclose() crash in debug mode
  - cmake: Build manual pages
  - cmake: Add support for building HTML and PDF docs
  - mbedtls: Add support for CURLOPT_SSL_CTX_FUNCTION
  - make: Introduce 'test-nonflaky' target
  - CURLINFO_PRIMARY_IP.3: Add example
  - tests/README: Mention nroff for --manual tests
  - mkhelp: Disable compression if the perl gzip module is unavailable
  - openssl: Fall back on SSL_ERROR_* string when no error detail
  - asiohiper: Make sure socket is open in event_cb
  - tests/README: Make "Run" section foolproof
  - curl: Check for end of input in writeout backslash handling
  - .gitattributes: Turn off CRLF for *.am
  - multi: Fix MinGW-w64 compiler warnings
  - schannel: Fix variable shadowing warning
  - openssl: Exclude DSA code when OPENSSL_NO_DSA is defined
  - http: Fix proxy connection reuse with basic-auth
  - pause: Handle mixed types of data when paused
  - http: Do not treat FTPS over CONNECT as HTTPS
  - conncache: Make hashkey avoid malloc
  - make: Use the variable MAKE for recursive calls
  - curl: Fix callback argument inconsistency
  - NTLM: Check for features with #ifdef instead of #if
  - cmake: Add several missing files to the dist
  - select: Use correct SIZEOF_ constant
  - connect: Fix unreferenced parameter warning
  - schannel: Fix unused variable warning
  - gcc7: Fix ‘*’ in boolean context
  - http2: Silence unused parameter warnings
  - ssh: Fix narrowing conversion warning
  - telnet: (win32) Fix read callback return variable
  - docs: Explain --fail-early does not imply --fail
  - docs: Added examples for CURLINFO_FILETIME.3 and CURLOPT_FILETIME.3
  - tests/server/util: Remove in6addr_any for recent MinGW
  - multi: Make curl_multi_wait avoid malloc in the typical case
  - include: curl/system.h is a run-time version of curlbuild.h
  - easy: Silence compiler warning
  - llist: Replace Curl_llist_alloc with Curl_llist_init
  - hash: Move key into hash struct to reduce mallocs
  - url: Don't free postponed data on connection reuse
  - curl_sasl: Declare mechtable static
  - curl: Fix Windows Unicode build
  - multi: Fix queueing of pending easy handles
  - tool_operate: Fix MinGW compiler warning
  - low_speed_limit: Improved function for longer time periods
  - gtls: Fix compiler warning
  - sspi: Print out InitializeSecurityContext() error message
  - schannel: Fix compiler warnings
  - vtls: fix unreferenced variable warnings
  - INSTALL.md: Fix secure transport configure arguments
  - CURLINFO_SCHEME.3: Fix variable type
  - libcurl-thread.3: Also mention threaded-resolver
  - nss: Load CA certificates even with --insecure
  - openssl: Fix this statement may fall through
  - poll: Prefer <poll.h> over <sys/poll.h>
  - polarssl: Unbreak build with versions < 1.3.8
  - Curl_expire_latest: Ignore already expired timers
  - configure: Turn implicit function declarations into errors
  - mbedtls: Fix memory leak in error path
  - http2: Fix handle leak in error path
  - .gitattributes: Force shell scripts to LF
  - configure.ac: Ignore CR after version numbers
  - extern-scan.pl: Strip trailing CR
  - openssl: Make SSL_ERROR_to_str more future-proof
  - openssl: Fix thread-safety bugs in error-handling
  - openssl: Don't try to print nonexistant peer private keys
  - nss: Fix MinGW compiler warnings
- Switch to lzma-compressed upstream tarball

* Thu Apr 13 2017 Paul Howarth <paul@city-fan.org> - 7.53.1-7.0.cf
- Provide (lib)curl-minimal subpackages with lightweight build of (lib)curl
  (Fedora 27 onwards)

* Mon Apr 10 2017 Paul Howarth <paul@city-fan.org> - 7.53.1-5.0.cf
- Disable upstream test 2033 (flaky test for HTTP/1 pipelining)

* Fri Apr  7 2017 Paul Howarth <paul@city-fan.org> - 7.53.1-4.0.cf
- Fix out of bounds read in curl --write-out (CVE-2017-7407)
- Make the dependency on nss-pem arch-specific from F-25 onwards (#1428550)
- Drop support for EOL distributions prior to F-13
  - Drop BuildRoot: and Group: tags
  - Drop buildroot cleaning in %%install
  - Drop explicit %%clean section
  - Drop explicit dependency on pkgconfig

* Thu Mar  2 2017 Paul Howarth <paul@city-fan.org> - 7.53.1-2.0.cf
- Rebuild to sync with Rawhide

* Fri Feb 24 2017 Paul Howarth <paul@city-fan.org> - 7.53.1-1.0.cf
- Update to 7.53.1
  - cyassl: Fix typo
  - url: Improve CURLOPT_PROXY_CAPATH error handling
  - urldata: Include curl_sspi.h when Windows SSPI is enabled
  - formdata: check for EOF when reading from stdin
  - tests: Set CHARSET and LANG to UTF-8 in 1035, 2046 and 2047
  - url: Default the proxy CA bundle location to CURL_CA_BUNDLE
  - rand: Added missing #ifdef HAVE_FCNTL_H around fcntl.h header

* Wed Feb 22 2017 Paul Howarth <paul@city-fan.org> - 7.53.0-1.0.cf
- Update to 7.53.0
  - CVE-2017-2629: Make SSL_VERIFYSTATUS work again
  - unix_socket: Added --abstract-unix-socket and CURLOPT_ABSTRACT_UNIX_SOCKET
  - CURLOPT_BUFFERSIZE: Support enlarging receive buffer
  - gnutls-random: Check return code for failed random
  - openssl-random: Check return code when asking for random
  - http: Remove "Curl_http_done: called premature" message
  - cyassl: Use time_t instead of long for timeout
  - build-wolfssl: Sync config with wolfSSL 3.10
  - ftp-gss: Check for init before use
  - configure: Accept --with-libidn2 instead
  - ftp: Failure to resolve proxy should return that error code
  - curl.1: Add three more exit codes
  - docs/ciphers: Link to our own new page about ciphers
  - vtls: s/SSLEAY/OPENSSL - fixes multi_socket timeouts with openssl
  - darwinssl: Fix iOS build
  - darwinssl: Fix CFArrayRef leak
  - cmake: Use crypt32.lib when building with OpenSSL on windows
  - curl_formadd.3: CURLFORM_CONTENTSLENGTH not needed when chunked
  - digest_sspi: Copy terminating NUL as well
  - curl: Fix --remote-time incorrect times on Windows
  - curl.1: Several updates and corrections
  - content_encoding: Change return code on a failure
  - curl.h: CURLE_FUNCTION_NOT_FOUND is no longer in use
  - docs: TCP_KEEPALIVE start and interval default to 60
  - darwinssl: --insecure overrides --cacert if both settings are in use
  - TheArtOfHttpScripting: Grammar
  - CIPHERS.md: Document GSKit ciphers
  - wolfssl: Support setting cipher list
  - wolfssl: Display negotiated SSL version and cipher
  - lib506: Fix build for Open Watcom
  - asiohiper: Improved socket handling
  - examples: Make the C++ examples follow our code style too
  - tests/sws: Retry send() on EWOULDBLOCK
  - cmake: Fix passing _WINSOCKAPI_ macro to compiler
  - smtp: Fix STARTTLS denied error message
  - imap/pop3: Don't print response character in STARTTLS denied messages
  - rand: Make it work without TLS backing
  - url: Fix parsing for when 'file' is the default protocol
  - url: Allow file://X:/path URLs on windows again
  - gnutls: Check for alpn and ocsp in configure
  - IDN: Use TR46 'non-transitional' for toASCII translations
  - url: Fix NO_PROXY env var to work properly with --proxy option
  - CURLOPT_PREQUOTE.3: Takes a struct curl_slist*, not a char*
  - docs: Add note about libcurl copying strings to CURLOPT_* manpages
  - curl: Reset the easy handle at --next
  - --next docs: --trace and --trace-ascii are also global
  - --write-out docs: 'time_total' is not always shown with ms precision
  - http: Print correct HTTP string in verbose output when using HTTP/2
  - docs: Improved language in README.md HISTORY.md CONTRIBUTE.md
  - http2: Disable server push if not requested
  - nss: Use the correct lock in nss_find_slot_by_name()
  - usercertinmem.c: Improve the short description
  - CURLOPT_CONNECT_TO: Fix compile warnings
  - docs: Non-blocking SSL handshake is now supported with NSS
  - *.rc: Escape non-ASCII/non-UTF-8 character for clarity
  - mbedTLS: Fix multi interface non-blocking handshake
  - PolarSSL: Fix multi interface non-blocking handshake
  - VC: Remove the makefile.vc6 build infra
  - telnet: Fix windows compiler warnings
  - cookies: Do not assume a valid domain has a dot
  - polarssl: Fix hangs
  - gnutls: Disable TLS session tickets
  - mbedtls: Disable TLS session tickets
  - mbedtls: Implement CTR-DRBG and HAVEGE random generators
  - openssl: Don't use certificate after transferring ownership
  - cmake: Support curl --xattr when built with cmake
  - OS400: Fix symbols
  - docs: Add more HTTPS proxy documentation
  - docs: Use more HTTPS links
  - cmdline-opts: Fixed build and test in out of source tree builds
  - CHANGES.0: Removed
  - schannel: Remove incorrect SNI disabled message
  - darwinssl: Avoid parsing certificates when not in verbose mode
  - test552: Fix typos
  - telnet: Fix typos
  - transfer: Only retry nobody-requests for HTTP
  - http2: Reset push header counter fixes crash
  - nss: Make FTPS work with --proxytunnel
  - test1139: Added the --manual keyword since the manual is required
  - polarssl, mbedtls: Fix detection of pending data
  - http_proxy: Fix tiny memory leak upon edge case connecting to proxy
  - URL: Only accept ";options" in SMTP/POP3/IMAP URL schemes
  - curl.1: ftp.sunet.se is no longer an FTP mirror
  - tool_operate: Show HTTPS-Proxy options on CURLE_SSL_CACERT
  - http2: Fix memory-leak when denying push streams
  - configure: Allow disabling pthreads, fall back on Win32 threads
  - curl: Fix typo in time condition warning message
  - axtls: Adapt to API changes
  - tool_urlglob: Allow a glob range with the same start and stop
  - winbuild: Add note on auto-detection of MACHINE in Makefile.vc
  - http: Fix missing 'Content-Length: 0' while negotiating auth
  - proxy: Fix hostname resolution and IDN conversion
  - docs: Fix timeout handling in multi-uv example
  - digest_sspi: Fix nonce-count generation in HTTP digest
  - sftp: Improved checks for create dir failures
  - smb: Use getpid replacement for windows UWP builds
  - digest_sspi: Handle 'stale=TRUE' directive in HTTP digest

* Fri Feb 10 2017 Paul Howarth <paul@city-fan.org> - 7.52.1-2.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Dec 23 2016 Paul Howarth <paul@city-fan.org> - 7.52.1-1.0.cf
- Update to 7.52.1
  - CVE-2016-9594: Uninitialized random
  - lib557: Fix checksrc warnings
  - lib: Fix MSVC compiler warnings
  - lib557.c: Use a shorter MAXIMIZE representation
  - tests: Run checksrc on debug builds

* Wed Dec 21 2016 Paul Howarth <paul@city-fan.org> - 7.52.0-1.0.cf
- Update to 7.52.0
  - nss: Map CURL_SSLVERSION_DEFAULT to NSS default
  - vtls: Support TLS 1.3 via CURL_SSLVERSION_TLSv1_3
  - curl: Introduce the --tlsv1.3 option to force TLS 1.3
  - curl: Add --retry-connrefused
  - proxy: Support HTTPS proxy and SOCKS+HTTP(s)
  - Add CURLINFO_SCHEME, CURLINFO_PROTOCOL, and %%{scheme}
  - curl: Add --fail-early
  - CVE-2016-9586: printf floating point buffer overflow
  - CVE-2016-9952: Win CE schannel cert wildcard matches too much
  - CVE-2016-9953: Win CE schannel cert name out of buffer read
  - msvc: Removed a straggling reference to strequal.c
  - winbuild: Remove strcase.obj from curl build
  - examples: Bugfixed multi-uv.c
  - configure: Verify that compiler groks -Werror=partial-availability
  - mbedtls: Fix build with mbedtls versions < 2.4.0
  - dist: Add unit test CMakeLists.txt to the tarball
  - curl -w: Added more decimal digits to timing counters
  - easy: Initialize info variables on easy init and duphandle
  - cmake: Disable poll for macOS
  - http2: Don't send header fields prohibited by HTTP/2 spec
  - ssh: Check md5 fingerprints case insensitively (regression)
  - openssl: Initial TLS 1.3 adaptions
  - curl_formadd.3: *_FILECONTENT and *_FILE need the file to be kept
  - printf: Fix ".*f" handling
  - examples/fileupload.c: fclose the file as well
  - SPNEGO: Fix memory leak when authentication fails
  - realloc: Use Curl_saferealloc to avoid common mistakes
  - openssl: Make sure to fail in the unlikely event that PRNG seeding fails
  - URL-parser: For file://[host]/ URLs, the [host] must be localhost
  - timeval: Prefer time_t to hold seconds instead of long
  - Curl_rand: Fixed and moved to rand.c
  - glob: Fix [a-c] globbing regression
  - darwinssl: Fix SSL client certificate not found on MacOS Sierra
  - curl.1: Clarify --dump-header only writes received headers
  - http2: Fix address sanitizer memcpy warning
  - http2: Use huge HTTP/2 windows
  - connects: Don't mix unix domain sockets with regular ones
  - url: Fix conn reuse for local ports and interfaces
  - x509: Limit ASN.1 structure sizes to 256K
  - checksrc: Add more checks
  - winbuild: Add config option ENABLE_NGHTTP2
  - http2: Check nghttp2_session_set_local_window_size exists
  - http2: Fix crashes when parent stream gets aborted
  - CURLOPT_CONNECT_TO: Skip non-matching "connect-to" entries
  - URL parser: Reject non-numerical port numbers
  - CONNECT: Reject TE or CL in 2xx responses
  - CONNECT: Read responses one byte at a time
  - curl: Support zero-length argument strings in config files
  - openssl: Don't use OpenSSL's ERR_PACK
  - curl.1: Generated with the new man page system
  - curl_easy_recv: Improve documentation and example program
  - Curl_getconnectinfo: Avoid checking if the connection is closed
  - CIPHERS.md: Attempt to document TLS cipher names

* Mon Nov 21 2016 Paul Howarth <paul@city-fan.org> - 7.51.0-3.0.cf
- Map CURL_SSLVERSION_DEFAULT to NSS default, add support for TLS 1.3
  (#1396719)

* Tue Nov 15 2016 Paul Howarth <paul@city-fan.org> - 7.51.0-2.0.cf
- Stricter host name checking for file:// URLs
- ssh: Check md5 fingerprints case insensitively

* Wed Nov  2 2016 Paul Howarth <paul@city-fan.org> - 7.51.0-1.0.cf
- Update to 7.51.0
  - nss: Additional cipher suites are now accepted by CURLOPT_SSL_CIPHER_LIST
  - New option: CURLOPT_KEEP_SENDING_ON_ERROR
  - CVE-2016-8615: Cookie injection for other servers
  - CVE-2016-8616: Case insensitive password comparison
  - CVE-2016-8617: OOB write via unchecked multiplication
  - CVE-2016-8618: Double-free in curl_maprintf
  - CVE-2016-8619: Double-free in krb5 code
  - CVE-2016-8620: glob parser write/read out of bounds
  - CVE-2016-8621: curl_getdate read out of bounds
  - CVE-2016-8622: URL unescape heap overflow via integer truncation
  - CVE-2016-8623: Use-after-free via shared cookies
  - CVE-2016-8624: Invalid URL parsing with '#'
  - CVE-2016-8625: IDNA 2003 makes curl use wrong host
  - openssl: Fix per-thread memory leak using 1.0.1 or 1.0.2
  - http: Accept "Transfer-Encoding: chunked" for HTTP/2 as well
  - LICENSE-MIXING.md: Update with mbedTLS dual licensing
  - examples/imap-append: Set size of data to be uploaded
  - test2048: Fix url
  - darwinssl: Disable RC4 cipher-suite support
  - CURLOPT_PINNEDPUBLICKEY.3: Fix the AVAILABILITY formatting
  - openssl: Don’t call CRYTPO_cleanup_all_ex_data
  - libressl: Fix version output
  - easy: Reset all statistical session info in curl_easy_reset
  - curl_global_cleanup.3: Don't unload the lib with sub threads running
  - dist: Add CurlSymbolHiding.cmake to the tarball
  - docs: Remove that --proto is just used for initial retrieval
  - configure: Fixed builds with libssh2 in a custom location
  - curl.1: --trace supports %% for sending to stderr!
  - cookies: Same domain handling changed to match browser behaviour
  - formpost: Trying to attach a directory no longer crashes
  - CURLOPT_DEBUGFUNCTION.3: Fixed unused argument warning
  - formpost: Avoid silent snprintf() truncation
  - ftp: Fix Curl_ftpsendf
  - mprintf: Return error on too many arguments
  - smb: Properly check incoming packet boundaries
  - GIT-INFO: Remove the Mac 10.1-specific details
  - resolve: Add error message when resolving using SIGALRM
  - cmake: Add nghttp2 support
  - dist: Remove PDF and HTML converted docs from the releases
  - configure: Disable poll() in macOS builds
  - vtls: Only re-use session-ids using the same scheme
  - pipelining: Skip to-be-closed connections when pipelining
  - win: Fix Universal Windows Platform build
  - curl: Do not set CURLOPT_SSLENGINE to DEFAULT automatically
  - maketgz: Make it support "only" generating version info
  - Curl_socket_check: Add extra check to avoid integer overflow
  - gopher: Properly return error for poll failures
  - curl: Set INTERLEAVEDATA too
  - polarssl: Clear thread array at init
  - polarssl: Fix unaligned SSL session-id lock
  - polarssl: Reduce #ifdef madness with a macro
  - curl_multi_add_handle: Set timeouts in closure handles
  - configure: Set min version flags for builds on mac
  - INSTALL: Converted to markdown => INSTALL.md
  - curl_multi_remove_handle: Fix a double-free
  - multi: Fix infinite loop in curl_multi_cleanup()
  - nss: Fix tight loop in non-blocking TLS handshake over proxy
  - mk-ca-bundle: Change URL retrieval to HTTPS-only by default
  - mbedtls: Stop using deprecated include file
  - docs: Fix req->data in multi-uv example
  - configure: Fix test syntax for monotonic clock_gettime
  - CURLMOPT_MAX_PIPELINE_LENGTH.3: Clarify it's not for HTTP/2
- Use libidn2 from Fedora 25 onwards

* Fri Oct  7 2016 Paul Howarth <paul@city-fan.org> - 7.50.3-2.0.cf
- Use the just-built version of libcurl while generating zsh completion

* Wed Sep 14 2016 Paul Howarth <paul@city-fan.org> - 7.50.3-1.0.cf
- Update to 7.50.3
  - CVE-2016-7167: Escape and unescape integer overflows
  - mk-ca-bundle.pl: Use SHA256 instead of SHA1
  - checksrc: Detect strtok() use
  - errors: New alias CURLE_WEIRD_SERVER_REPLY
  - http2: Support > 64bit sized uploads
  - openssl: Fix bad memory free (regression)
  - CMake: Hide private library symbols
  - http: Refuse to pass on response body when NO_NODY was set
  - cmake: Fix curl-config --static-libs
  - mbedtls: Switch off NTLM in build if md4 isn't available
  - curl: --create-dirs on Windows groks both forward and backward slashes

* Wed Sep  7 2016 Paul Howarth <paul@city-fan.org> - 7.50.2-1.0.cf
- Update to 7.50.2
  - nss: Fix incorrect use of a previously loaded certificate from file
    (CVE-2016-7141)
  - nss: Work around race condition in PK11_FindSlotByName()
  - mbedtls: Added support for NTLM
  - SSH: Fixed SFTP/SCP transfer problems
  - multi: Make Curl_expire() work with 0 ms timeouts
  - mk-ca-bundle.pl: -m keeps ca cert meta data in output
  - TFTP: Fix upload problem with piped input
  - CURLOPT_TCP_NODELAY: now enabled by default
  - mbedtls: Set verbose TLS debug when MBEDTLS_DEBUG is defined
  - http2: Always wait for readable socket
  - cmake: Enable win32 large file support by default
  - cmake: Enable win32 threaded resolver by default
  - winbuild: Avoid setting redundant CFLAGS to compile commands
  - curl.h: Make CURL_NO_OLDIES define CURL_STRICTER
  - docs: Make more markdown files use .md extension
  - docs: CONTRIBUTE and LICENSE-MIXING were converted to markdown
  - winbuild: Allow changing C compiler via environment variable CC
  - rtsp: Accept any RTSP session id
  - HTTP: Retry failed HEAD requests on reused connections too
  - configure: Add zlib search with pkg-config
  - openssl: Accept subjectAltName iPAddress if no dNSName match
  - MANUAL: Remove invalid link to LDAP documentation
  - socks: Improved connection procedure
  - proxy: Reject attempts to use unsupported proxy schemes
  - proxy: Bring back use of "Proxy-Connection:"
  - curl: Allow "pkcs11:" prefix for client certificates
  - spnego_sspi: Fix memory leak in case *outlen is zero
  - SOCKS: Improve verbose output of SOCKS5 connection sequence
  - SOCKS: Display the hostname returned by the SOCKS5 proxy server
  - http/sasl: Query authentication mechanism supported by SSPI before using
  - sasl: Don't use GSSAPI authentication when domain name not specified
  - win: Basic support for Universal Windows Platform apps
  - ftp: Fix wrong poll on the secondary socket
  - openssl: Build warning-free with 1.1.0 (again)
  - HTTP: Stop parsing headers when switching to unknown protocols
  - test219: Add http as a required feature
  - TLS: random file/egd doesn't have to match for conn reuse
  - schannel: Disable ALPN for Wine since it is causing problems
  - http2: Make sure stream errors don't needlessly close the connection
  - http2: Return CURLE_HTTP2_STREAM for unexpected stream close
  - darwinssl: --cainfo is intended for backward compatibility only
  - Speed caps: Not based on average speeds anymore
  - configure: Make the cpp -P detection not clobber CPPFLAGS
  - http2: Use named define instead of magic constant in read callback
  - http2: Skip the content-length parsing, detect unknown size
  - http2: Return EOF when done uploading without known size
  - darwinssl: Test for errSecSuccess in PKCS12 import rather than noErr
  - openssl: Fix CURLINFO_SSL_VERIFYRESULT
- Disable various ssh tests for F12..F15, which are failing for reasons unknown
- Build with c-ares rather than POSIX threaded DNS resolver for F12..F15,
  which resolves some other test failures, and allows dropping of workaround
  patch for old applications on F12 and F13
- Update patches as needed

* Fri Aug 26 2016 Paul Howarth <paul@city-fan.org> - 7.50.1-2.0.cf
- Work around race condition in PK11_FindSlotByName()
- Fix incorrect use of a previously loaded certificate from file
  (related to CVE-2016-5420)

* Wed Aug  3 2016 Paul Howarth <paul@city-fan.org> - 7.50.1-1.0.cf
- Update to 7.50.1
  - TLS: Switch off SSL session id when client cert is used (CVE-2016-5419)
  - TLS: Only reuse connections with the same client cert (CVE-2016-5420)
  - curl_multi_cleanup: Clear connection pointer for easy handles
    (CVE-2016-5421)
  - Include the CURLINFO_HTTP_VERSION(3) man page into the release tarball
  - Include the http2-server.pl script in the release tarball
  - test558: Fix test by stripping file paths from FD lines
  - spnego: Corrected misplaced * in Curl_auth_spnego_cleanup() declaration
  - tests: Fix for http/2 feature
  - cmake: Fix for schannel support
  - curl.h: Make public types void * again
  - win32: Fix a potential memory leak in Curl_load_library
  - travis: Fix OSX build by re-installing libtool
  - mbedtls: Fix debug function name

* Wed Jul 27 2016 Paul Howarth <paul@city-fan.org> - 7.50.0-2.0.cf
- Use upstream fix for HTTP2 test confusion

* Fri Jul 22 2016 Paul Howarth <paul@city-fan.org> - 7.50.0-1.1.cf
- Fix confusion in test suite about whether or not HTTP2 support is available
- Use the default ports for the test suite; it's not robust enough to support
  running under different ports

* Thu Jul 21 2016 Paul Howarth <paul@city-fan.org> - 7.50.0-1.0.cf
- Update to 7.50.0
  - http: Add CURLINFO_HTTP_VERSION and %%{http_version}
  - memdebug: Fix MSVC crash with -DMEMDEBUG_LOG_SYNC
  - openssl: Fix build with OPENSSL_NO_COMP
  - mbedtls: Removed unused variables
  - cmake: Added missing mbedTLS support
  - URL parser: Allow URLs to use one, two or three slashes
  - curl: Fix -q [regression]
  - openssl: Use correct buffer sizes for error messages
  - curl: Fix SIGSEGV while parsing URL with too many globs
  - schannel: Add CURLOPT_CERTINFO support
  - vtls: Fix ssl session cache race condition
  - http: Fix HTTP/2 connection reuse [regression]
  - checksrc: Add LoadLibrary to the banned functions list
  - schannel: Disable ALPN on Windows < 8.1
  - configure: Occasional ignorance of --enable-symbol-hiding with GCC
  - http2: test17xx are the first real HTTP/2 tests
  - resolve: Add support for IPv6 DNS64/NAT64 Networks on OS X + iOS
  - curl_multi_socket_action.3: Rewording
  - CURLOPT_POSTFIELDS.3: Clarify what happens when set empty
  - cmake: Fix build with winldap
  - openssl: Fix cert check with non-DNS name fields present
  - curl.1: Mention the units for the progress meter
  - openssl: Use more 'const' to fix build warnings with 1.1.0 branch
  - cmake: Now using BUILD_TESTING=ON/OFF
  - vtls: Only call add/getsession if session id is enabled
  - headers: Forward declare CURL, CURLM and CURLSH as structs
  - configure: Improve detection of CA bundle path on FreeBSD
  - SFTP: Set a generic error when no SFTP one exists
  - curl_global_init.3: Expand on the SSL and WIN32 bits purpose
  - conn: Don't free easy handle data in handler->disconnect
  - cookie.c: Fix misleading indentation
  - library: Fix memory leaks found during static analysis
  - CURLMOPT_SOCKETFUNCTION.3: Fix typo
  - curl_global_init: Moved the "IPv6 works" check here
  - connect: Disable TFO on Linux when using SSL
  - vauth: Fixed memory leak due to function returning without free
  - winbuild: Fix embedded manifest option
- Fix HTTPS and FTPS tests (work around stunnel bug #1358810)
- Require nss-pem because it is no longer included in the nss package
  (#1347336)

* Wed Jun 22 2016 Paul Howarth <paul@city-fan.org> - 7.49.1-3.1.cf
- Add HTTP/2 protocol support for EL-6 and EL-7 builds too

* Sun Jun 19 2016 Paul Howarth <paul@city-fan.org> - 7.49.1-3.0.cf
- Use multilib-rpm-config to install arch-dependent header files

* Fri Jun  3 2016 Paul Howarth <paul@city-fan.org> - 7.49.1-2.0.cf
- Fix SIGSEGV of the curl tool while parsing URL with too many globs (#1340757)

* Mon May 30 2016 Paul Howarth <paul@city-fan.org> - 7.49.1-1.0.cf
- Update to 7.49.1
  - Windows: prevent DLL hijacking, CVE-2016-4802
  - dist: Include manpage-scan.pl, nroff-scan.pl and CHECKSRC.md
  - schannel: Fix compile break with MSVC XP toolset
  - curlbuild.h.dist: Check __LP64__ as well to fix MIPS build
  - dist: Include curl_multi_socket_all.3
  - http2: Use HTTP/2 in the HTTP/1.1-alike response
  - openssl: ERR_remove_thread_state() is deprecated in latest 1.1.0
  - CURLOPT_CONNECT_TO.3: User must not free the list prematurely
  - libcurl.m4: Avoid obsolete warning
  - winbuild/Makefile.vc: Fix check on SSL, MBEDTLS, WINSSL exclusivity
  - curl_multibyte: Fix compiler error
  - openssl: Cleanup must free compression methods (memory leak)
  - mbedtls: Fix includes so snprintf() works
  - checksrc.pl: Added variants of strcat()/strncat() to banned function list
  - contributors.sh: Better grep pattern and show GitHub username
  - ssh: Fix build for libssh2 before 1.2.6
  - curl_share_setopt.3: Add min ver needed for ssl session lock

* Fri May 20 2016 Paul Howarth <paul@city-fan.org> - 7.49.0-1.1.cf
- Manually install (and package) zsh completion
- Bundle upstream files needed so we can run tests 1139 and 1140

* Wed May 18 2016 Paul Howarth <paul@city-fan.org> - 7.49.0-1.0.cf
- Update to 7.49.0
  - schannel: Add ALPN support
  - SSH: Support CURLINFO_FILETIME
  - SSH: New CURLOPT_QUOTE command "statvfs"
  - wolfssl: Add ALPN support
  - http2: Added --http2-prior-knowledge
  - http2: Added CURL_HTTP_VERSION_2_PRIOR_KNOWLEDGE
  - libcurl: Added CURLOPT_CONNECT_TO
  - curl: Added --connect-to
  - libcurl: Added CURLOPT_TCP_FASTOPEN
  - curl: Added --tcp-fastopen
  - curl: Remove support for --ftpport, -http-request and --socks
    (deprecated versions since around 10 years)
  - CVE-2016-3739: TLS certificate check bypass with mbedTLS/PolarSSL
  - checksrc.bat: Updated the help to be consistent with generate.bat
  - checksrc.bat: Added support for scanning the tests and examples
  - openssl: Fix ERR_remove_thread_state() for boringssl/libressl
  - openssl: boringssl provides the same numbering as openssl
  - multi: Fix "Operation timed out after" timer
  - url: Don't use bad offset in tld_check_name to show error
  - sshserver.pl: Use quotes for given options
  - Makefile.am: Skip the scripts dir
  - curl: Warn for --capath use if not supported by libcurl
  - http2: Fix connection reuse
  - GSS: Make Curl_gss_log_error more verbose
  - build-wolfssl: Allow a broader range of ciphers (Visual Studio)
  - wolfssl: Use ECC supported curves extension
  - openssl: Fix compilation warnings
  - Curl_add_buffer_send: Avoid possible NULL dereference
  - SOCKS5_gssapi_negotiate: Don't assume little-endian ints
  - strerror: Don't bit shift a signed integer
  - url: Corrected get protocol family for FTP and LDAP
  - curl/mprintf.h: Remove support for _MPRINTF_REPLACE
  - upload: Missing rewind call could make libcurl hang
  - IMAP: Check pointer before dereferencing it
  - build: Changed the Visual Studio projects warning level from 3 to 4
  - checksrc: Now stricter, wider checks, code cleaned up
  - checksrc: Added docs/CHECKSRC.md
  - curl_sasl: Fixed potential null pointer utilisation
  - krb5: Fixed missing client response when mutual authentication enabled
  - krb5: Only process challenge when present
  - krb5: Only generate a SPN when its not known
  - formdata: Use appropriate fopen() macros
  - curl.1: -w filename_effective was introduced in 7.26.0
  - http2: Make use of the nghttp2 error callback
  - http2: Fix connection reuse when PING comes after last DATA
  - curl.1: Change example for -F
  - HTTP2: Add a space character after the status code
  - curl.1: Use example.com more
  - mbedtls.c: Changed private prefix to mbed_
  - mbedtls: Implement and provide *_data_pending() to avoid hang
  - mbedtls: Fix MBEDTLS_DEBUG builds
  - ftp/imap/pop3/smtp: Allow the service name to be overridden
  - CURLOPT_SOCKS5_GSSAPI_SERVICE: Merged with CURLOPT_PROXY_SERVICE_NAME
  - build: Include scripts/ in the dist
  - http2: Add handling stream level error
  - http2: Improve header parsing
  - makefile.vc6: Use d suffix on debug object
  - configure: Remove check for libresolve
  - scripts/make: Use $(EXEEXT) for executables
  - checksrc: Got rid of the whitelist files
  - sendf: Added ability to call recv() before send() as workaround
  - NTLM: Check for NULL pointer before dereferencing
  - openssl: Builds with OpenSSL 1.1.0-pre5
  - configure: ac_cv_ -> curl_cv_ for all cached vars
  - winbuild: Add mbedtls support
  - curl: Make --ftp-create-dirs retry on failure
  - PolarSSL: Implement public key pinning
  - multi: Accidentally used resolved host name instead of proxy
  - CURLINFO_TLS_SESSION.3: clarify TLS library support before 7.48.0
  - CONNECT_ONLY: Don't close connection on GSS 401/407 reponses
  - opts: Fix some syntax errors in example code fragments
  - mbedtls: Fix session resume
  - test1139: Verifies libcurl option man page presence
  - CURLINFO_TLS_SSL_PTR.3: Clarify SSL pointer availability
  - curl: Make --disable work as long form of -q
  - curl: Use --telnet-option as documented
  - curl.1: Document --ftp-ssl-reqd, --krb4 and --ntlm-wb
  - curl: -h output lacked --proxy-header and --ntlm-wb
  - curl -J: Make it work even without http:// scheme on URL
  - lib: Include curl_printf.h as one of the last headers
  - tests: Handle path properly on Msys/Cygwin
  - curl.1: --mail-rcpt can be used multiple times
  - CURLOPT_ACCEPT_ENCODING.3: Clarified
  - docs: Fixed lots of broken man page references
  - tls: Make setting pinnedkey option fail if not supported
  - test1140: Run nroff-scan to verify man pages
  - http: Make sure a blank header overrides accept_decoding
  - connections: Do not reuse non-HTTP proxies on different ports
  - connect: Fix invalid "Network is unreachable" errors
  - TLS: Move the ALPN/NPN enable bits to the connection
  - TLS: SSL_peek is not a const operation
  - http2: Add space between colon and header value
  - darwinssl: Fix certificate verification disable on OS X 10.8
  - mprintf: Fix processing of width and prec args
  - ftp wildcard: segfault due to init only in multi_perform
- Update zsh completion patch
- Disable tests 1139 and 1140, which fail due to files missing from tarball
- Upstream not building/installing zsh completion script any longer

* Wed Mar 23 2016 Paul Howarth <paul@city-fan.org> - 7.48.0-1.0.cf
- Update to 7.48.0
  - configure: --with-ca-fallback: Use built-in TLS CA fallback
  - TFTP: Add --tftp-no-options to expose CURLOPT_TFTP_NO_OPTIONS
  - getinfo: CURLINFO_TLS_SSL_PTR supersedes CURLINFO_TLS_SESSION
  - Added CODE_STYLE.md
  - Proxy-Connection: Stop sending this header by default
  - os400: Sync ILE/RPG definitions with latest public header files
  - cookies: Allow spaces in cookie names, cut off trailing spaces
  - tool_urlglob: Allow reserved dos device names (Windows)
  - openssl: Remove most BoringSSL #ifdefs
  - tool_doswin: Support for literal path prefix \\?\
  - mbedtls: Fix ALPN usage segfault
  - mbedtls: Fix memory leak when destroying SSL connection data
  - nss: Do not count enabled cipher-suites
  - examples/cookie_interface.c: Add cleanup call
  - examples: Adhere to curl code style
  - curlx_tvdiff: Handle 32bit time_t overflows
  - dist: Ship buildconf.bat too
  - curl.1: --disable-{eprt,epsv} are ignored for IPv6 hosts
  - generate.bat: Fix comment bug by removing old comments
  - test1604: Add to Makefile.inc so it gets run
  - gtls: Fix for builds lacking encrypted key file support
  - SCP: Use libssh2_scp_recv2 to support > 2GB files on windows
  - CURLOPT_CONNECTTIMEOUT_MS.3: Fix example to use milliseconds option
  - cookie: Do not refuse cookies to localhost
  - openssl: Avoid direct PKEY access with OpenSSL 1.1.0
  - http: Don't break the header into chunks if HTTP/2
  - http2: Don't decompress gzip decoding automatically
  - curlx.c: i2s_ASN1_IA5STRING() clashes with an openssl function
  - curl.1: Add a missing dash
  - curl.1: HTTP headers for --cookie must be Set-Cookie style
  - CURLOPT_COOKIEFILE.3: HTTP headers must be Set-Cookie style
  - curl_sasl: Fix memory leak in digest parser
  - src/Makefile.m32: Add CURL_{LD,C}FLAGS_EXTRAS support
  - CURLOPT_DEBUGFUNCTION.3: Fix example
  - runtests: Fixed usage of %%PWD on MinGW64
  - tests/sshserver.pl: Use RSA instead of DSA for host auth
  - multi_remove_handle: Keep the timeout list until after disconnect
  - Curl_read: Check for activated HTTP/1 pipelining, not only requested
  - configure: Warn on invalid ca bundle or path
  - file: Try reading from files with no size
  - getinfo: Add support for mbedTLS TLS session info
  - formpost: Fix memory leaks in AddFormData error branches
  - makefile.m32: Allow to pass .dll/.exe-specific LDFLAGS
  - url: If Curl_done is premature then pipeline not in use
  - cookie: Remove redundant check
  - cookie: Don't expire session cookies in remove_expired
  - makefile.m32: Fix to allow -ssh2-winssl combination
  - checksrc.bat: Fixed cannot find perl if installed but not in path
  - build-openssl.bat: Fixed cannot find perl if installed but not in path
  - mbedtls: Fix user-specified SSL protocol version
  - makefile.m32: Add missing libs for static -winssl-ssh2 builds
  - test46: Change cookie expiry date
  - pipeline: Sanity check pipeline pointer before accessing it
  - openssl: Use the correct OpenSSL/BoringSSL/LibreSSL in messages
  - ftp_done: Clear tunnel_state when secondary socket closes
  - opt-docs: Fix heading macros
  - imap/pop3/smtp: Fixed connections upgraded with TLS are not reused
  - curl_multi_wait: Never return -1 in 'numfds'
  - url.c: Fix clang warning: no newline at end of file
  - krb5: Improved type handling to avoid clang compiler warnings
  - cookies: First n/v pair in Set-Cookie: is the cookie, then parameters
  - multi: Avoid blocking during CURLM_STATE_WAITPROXYCONNECT
  - multi hash: Ensure modulo performed on curl_socket_t
  - curl: glob_range: No need to check unsigned variable for negative
  - easy: Add check to malloc() when running event-based
  - CURLOPT_SSLENGINE.3: Only for OpenSSL built with engine support
  - version: Thread safety
  - openssl: verbose: Show matching SAN pattern
  - openssl: Adapt to OpenSSL 1.1.0 API breakage in ERR_remove_thread_state()
  - formdata.c: Fixed compilation warning
  - configure: Use cpp -P when needed
  - imap.c: Fixed compilation warning with /Wall enabled
  - config-w32.h: Fixed compilation warning when /Wall enabled
  - ftp/imap/pop3/smtp: Fixed compilation warning when /Wall enabled
  - build: Added missing Visual Studio filter files for VC10 onwards
  - easy: Remove poll failure check in easy_transfer
  - mbedtls: Fix compiler warning
  - build-wolfssl: Update VS properties for wolfSSL v3.9.0
  - Fixed various compilation warnings when verbose strings disabled
- Update patches as needed

* Thu Mar  3 2016 Paul Howarth <paul@city-fan.org> - 7.47.1-4.0.cf
- Do not refuse cookies for localhost (#1308791)

* Wed Feb 17 2016 Paul Howarth <paul@city-fan.org> - 7.47.1-3.0.cf
- Make SCP and SFTP test-cases work with recent OpenSSH versions that don't
  support DSA keys

* Thu Feb 11 2016 Paul Howarth <paul@city-fan.org> - 7.47.1-2.0.cf
- Enable support for Public Suffix List where possible (#1305701)

* Mon Feb  8 2016 Paul Howarth <paul@city-fan.org> - 7.47.1-1.0.cf
- Update to 7.47.1
  - getredirect.c: Fix variable name
  - tool_doswin: Silence unused function warning
  - cmake: Fixed when OpenSSL enabled on Windows and schannel detected
  - curl.1: Explain remote-name behavior if file already exists
  - tool_operate: Don't sanitize --output path (Windows)
  - URLs: Change all http:// URLs to https:// in documentation & comments
  - sasl_sspi: Fix memory leak in domain populate
  - COPYING: Clarify that Daniel is not the sole author
  - examples/htmltitle: Use _stricmp on Windows
  - examples/asiohiper: Avoid function name collision on Windows
  - idn_win32: Better error checking
  - openssl: Fix signed/unsigned mismatch warning in X509V3_ext
  - curl save files: Check for backslashes on cygwin
- Update patches as needed

* Thu Feb  4 2016 Paul Howarth <paul@city-fan.org> - 7.47.0-2.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Wed Jan 27 2016 Paul Howarth <paul@city-fan.org> - 7.47.0-1.0.cf
- Update to 7.47.0
  - version: Add flag CURL_VERSION_PSL for libpsl
  - http: Added CURL_HTTP_VERSION_2TLS to do HTTP/2 for HTTPS only
  - curl: Use 2TLS by default
  - curl --expect100-timeout: added
  - Add .dir-locals and set c-basic-offset to 2 (for emacs)
  - curl: Avoid local drive traversal when saving file on Windows
    (CVE-2016-0754)
  - NTLM: Do not resuse proxy connections without diff proxy credentials
    (CVE-2016-0755)
  - tests: Disable the OAUTHBEARER tests when using a non-default port number
  - curl: Remove keepalive #ifdef checks done on libcurl's behalf
  - formdata: Check if length is too large for memory
  - lwip: Fix compatibility issues with later versions
  - openssl: BoringSSL doesn't have CONF_modules_free
  - config-win32: Fix warning HAVE_WINSOCK2_H undefined
  - build: Fix compilation error with CURL_DISABLE_VERBOSE_STRINGS
  - http2: Fix hanging paused stream
  - scripts/Makefile: Fix GNUism and survive no perl
  - openssl: Adapt to 1.1.0+ name changes
  - openssl: Adapt to openssl ≥ 1.1.0 X509 opaque structs
  - HTTP2.md: Spell fix and remove TODO now implemented
  - setstropt: const-correctness
  - cyassl: Fix compiler warning on type conversion
  - gskit: Fix host subject altname verification
  - http2: Support trailer fields
  - wolfssl: Handle builds without SSLv3 support
  - cyassl: Deal with lack of *get_peer_certificate
  - sockfilt: Do not wait on unreliable file or pipe handle
  - make: Build zsh script even in an out-of-tree build
  - test 1326: Fix getting stuck on Windows
  - test 87: Fix file check on Windows
  - configure: Allow static builds on mingw
  - configure: Detect IPv6 support on Windows
  - ConnectionExists: With *PIPEWAIT, wait for connections
  - Makefile.inc: s/curl_SOURCES/CURL_FILES
  - test 16: Fixed for Windows
  - test 252-255: Use datacheck mode text for ASCII-mode LISTings
  - tftpd server: Add Windows support by writing files in binary mode
  - ftplistparser: Fix handling of file LISTings using Windows EOL
  - tests first.c: Fix calculation of sleep timeout on Windows
  - tests (several): Use datacheck mode text for ASCII-mode LISTings
  - CURLOPT_RANGE.3: For HTTP servers, range support is optional
  - test 1515: Add MSYS support by passing a relative path
  - curl_global_init.3: Add Windows-specific info for init via DLL
  - http2: Fix client write for trailers on stream close
  - mbedtls: Fix ALPN support
  - connection reuse: IDN host names fixed
  - http2: Fix PUSH_PROMISE headers being treated as trailers
  - http2: Handle the received SETTINGS frame
  - http2: Ensure that http2_handle_stream_close is called
  - mbedtls: Implement CURLOPT_PINNEDPUBLICKEY
  - runtests: Add mbedTLS to the SSL backends
  - IDN host names: Remove the port number before converting to ACE
  - zsh.pl: Fail if no curl is found
  - scripts: Fix zsh completion generation
  - scripts: Don't generate and install zsh completion when cross-compiling
  - lib: Prefix URLs with lower-case protocol names/schemes
  - ConnectionExists: Only do pipelining/multiplexing when asked
  - configure: Assume IPv6 works when cross-compiled
  - openssl: For 1.1.0+ they now provide a SSLeay() macro of their own
  - openssl: Improved error detection/reporting
  - ssh: CURLOPT_SSH_PUBLIC_KEYFILE now treats "" as NULL again
  - mbedtls: Fix pinned key return value on fail
  - maketgz: Generate date stamp with LC_TIME=C
- Re-enable previously-disabled tests
- Fix FTBFS when building curl dynamically with no libcurl.so.4 in system

* Fri Dec  4 2015 Paul Howarth <paul@city-fan.org> - 7.46.0-2.0.cf
- Rebuild for #1288529

* Wed Dec  2 2015 Paul Howarth <paul@city-fan.org> - 7.46.0-1.0.cf
- Update to 7.46.0
  - configure: build silently by default
  - cookies: Add support for Public Suffix List with libpsl
  - vtls: Added support for mbedTLS
  - Added CURLOPT_STREAM_DEPENDS
  - Added CURLOPT_STREAM_DEPENDS_E
  - Added CURLOPT_STREAM_WEIGHT
  - Added CURLFORM_CONTENTLEN
  - oauth2: Added support for OAUTHBEARER SASL mechanism to IMAP, POP3 and SNMP
  - des: Fix header conditional for Curl_des_set_odd_parity
  - ntlm: Get rid of unconditional use of long long
  - CURLOPT_CERTINFO.3: Fix reference to CURLINFO_CERTINFO
  - docs: CURLINFO_LASTSOCKET => CURLINFO_ACTIVESOCKET
  - http2: Fix http2_recv to return -1 if recv returned -1
  - curl_global_init_mem: Set function pointers before doing init
  - ntlm: Error out without 64bit support as the code needs it
  - openssl: Fix set up of pkcs12 certificate verification chain
  - acinclude: Remove PKGCONFIG override
  - test1531: case the size to fix the test on non-largefile builds
  - fread_func: Move callback pointer from set to state struct
  - test1601: Fix compilation with --enable-debug and --disable-crypto-auth
  - http2: Don't pass uninitialized name+len pairs to nghttp2_submit_request
  - curlbuild.h: Fix non-configure compiling to mips and sh4 targets
  - tool: Generate easysrc with last cache linked-list
  - cmake: Fix for add_subdirectory(curl) use-case
  - vtls: Fix compiler warning for TLS backends without sha256
  - build: Fix for MSDOS/djgpp
  - checksrc: Add crude // detection
  - http2: on_frame_recv: Trust the conn/data input
  - ftp: Allow CURLOPT_IGNORE_CONTENT_LENGTH to ignore size
  - polarssl/mbedtls: Fix name space pollution
  - build: Fix mingw ssl gdi32 order
  - build: Fix support for PKG_CONFIG
  - MacOSX-Framework: sdk regex fix for sdk 10.10 and later
  - socks: Fix incorrect port numbers in failed connect messages
  - curl.1: -E: s/private certificate/client certificate/
  - curl.h: s/HTTPPOST_/CURL_HTTPOST_/
  - curl_formadd: Support >2GB files on windows
  - http redirects: %%-encode bytes outside of ascii range
  - rawstr: Speed up Curl_raw_toupper by 40%%
  - curl_ntlm_core: Fix 2 curl_off_t constant overflows
  - getinfo: CURLINFO_ACTIVESOCKET: Fix bad socket value
  - tftp tests: Verify sent options too
  - imap: Don't call imap_atom() when no mailbox specified in LIST command
  - imap: Fixed double quote in LIST command when mailbox contains spaces
  - imap: Don't check for continuation when executing a CUSTOMREQUEST
  - acinclude: Remove check for 16-bit curl_off_t
  - BoringSSL: Work with stricter BIO_get_mem_data()
  - cmake: Add missing feature macros in config header
  - sasl_sspi: Fixed unicode build for digest authentication
  - sasl_sspi: Fix identity memory leak in digest authentication
  - unit1602: Fixed failure in torture test
  - unit1603: Added unit tests for hash functions
  - vtls/openssl: Remove unused traces of yassl ifdefs
  - openssl: Remove #ifdefs for < 0.9.7 support
  - typecheck-gcc.h: Add some missing options
  - curl: Mark two more options strings for --libcurl output
  - openssl: Free modules on cleanup
  - CURLMOPT_PUSHFUNCTION.3: *_byname() returns only the first header
  - getconnectinfo: Don't call recv(2) if socket == -1
  - http2: http_done: Don't free already-freed push headers
  - zsh completion: Preserve single quotes in output
  - os400: Provide options for libssh2 use in compile scripts
  - build: Fix theoretical infinite loops
  - pop3: Differentiate between success and continuation responses
  - examples: Fixed compilation warnings
  - schannel: Use GetVersionEx() when VerifyVersionInfo() isn't available
  - CURLOPT_HEADERFUNCTION.3: fix typo
  - curl: Expanded the -XHEAD warning text
  - done: Make sure the final progress update is made
  - build: Install zsh completion
  - RTSP: Do not add if-modified-since without timecondition
  - curl: Fixed display of URL index in password prompt for --next
  - nonblock: Fix setting non-blocking mode for Amiga
  - http2 push: Add missing inits of new stream
  - http2: Convert some verbose output into debug-only output
  - Curl_read_plain: clean up ifdefs that break statements
- Explicitly turn off silent building so we can see the compiler flags used
- Disable OAUTHBEARER tests since they don't work with custom test ports

* Wed Oct  7 2015 Paul Howarth <paul@city-fan.org> - 7.45.0-1.0.cf
- Update to 7.45.0
  - Added CURLOPT_DEFAULT_PROTOCOL
  - Added new tool option --proto-default
  - getinfo: Added CURLINFO_ACTIVESOCKET
  - Turned CURLINFO_* option docs as stand-alone man pages
  - curl: Point out unnecessary uses of -X in verbose mode
  - curl_global_init_mem.3: Stronger thread safety warning
  - buildconf.bat: Fixed issues when ran in directories with special chars
  - cmake: Fix CurlTests check for gethostbyname_r with 5 arguments
  - generate.bat: Fixed issues when ran in directories with special chars
  - generate.bat: Only call buildconf.bat if it exists
  - generate.bat: Added support for generating only the prerequisite files
  - curl.1: Document weaknesses in SSLv2 and SSLv3
  - CURLOPT_HTTP_VERSION.3: Connection re-use goes before version
  - docs: Update the redirect protocols disabled by default
  - inet_pton.c: Fix MSVC run-time check failure
  - CURLMOPT_PUSHFUNCTION.3: Fix argument types
  - rtsp: Support basic/digest authentication
  - rtsp: Stop reading empty DESCRIBE responses
  - travis: Upgrading to container based build
  - travis.yml: Add OS X testbot
  - FTP: Make state machine not get stuck in state
  - openssl: Handle lack of server cert when strict checking disabled
  - configure: Change functions to detect openssl (clones)
  - configure: Detect latest boringssl
  - runtests: Allow for spaces in server-verify curl custom path
  - http2: on_frame_recv: Get a proper 'conn' for the debug logging
  - ntlm: Mark deliberate switch case fall-through
  - http2: Remove dead code
  - curl_easy_{escape,unescape}.3: "char *" vs. "const char *"
  - curl: Point out the conflicting HTTP methods if used
  - cmake: Added Windows SSL support
  - curl_easy_{escape,setopt}.3: Fix example
  - curl_easy_escape.3: Escape '\n'
  - libcurl.m4: Put braces around empty if body
  - buildconf.bat: Fixed double blank line in 'curl manual' warning output
  - sasl: Only define Curl_sasl_digest_get_pair() when CRYPTO_AUTH enabled
  - inet_pton.c: Fix MSVC run-time check failure
  - CURLOPT_FOLLOWLOCATION.3: Mention methods for redirects
  - http2: Don't pass on Connection: headers
  - nss: Do not directly access SSL_ImplementedCiphers
  - docs: Numerous cleanups and spelling fixes
  - FTP: do_more: Add check for wait_data_conn in upload case
  - parse_proxy: Reject illegal port numbers
  - cmake: IPv6 : Disable Unix header check on Windows platform
  - winbuild: Run buildconf.bat if necessary
  - buildconf.bat: Fix syntax error
  - curl_sspi: Fix possibly undefined CRYPT_E_REVOKED
  - nss: Prevent NSS from incorrectly re-using a session
  - libcurl-errors.3: Add two missing error codes
  - openssl: Fix build with < 0.9.8
  - openssl: Refactor certificate parsing to use OpenSSL memory BIO
  - openldap: Only part of LDAP query results received
  - ssl: Add server cert's "sha256//" hash to verbose
  - NTLM: Reset auth-done when using a fresh connection
  - curl: Generate easysrc only on --libcurl
  - tests: Disable 1801 until fixed
  - CURLINFO_TLS_SESSION: Always return backend info
  - gnutls: Support CURLOPT_KEYPASSWD
  - gnutls: Report actual GnuTLS error message for certificate errors
  - tests: Disable 1510 due to CI-problems on github
  - cmake: Put "winsock2.h" before "windows.h" during configure checks
  - cmake: Ensure discovered include dirs are considered
  - configure: Add missing ')' for CURL_CHECK_OPTION_RT
  - build: Fix failures with -Wcast-align and -Werror
  - FTP: Fix uploading ASCII with unknown size
  - readwrite_data: Set a max number of loops
  - http2: Avoid superfluous Curl_expire() calls
  - http2: Set TCP_NODELAY unconditionally
  - docs: Fix unescaped '\n' in man pages
  - openssl: Fix algorithm init to make (gost) engines work
  - win32: Make recent Borland compilers use long long
  - runtests: Fix pid check in checkdied
  - gopher: Don't send NUL byte
  - tool_setopt: Fix c_escape truncated octal
  - hiperfifo: Fix the pointer passed to WRITEDATA
  - getinfo: Fix return code for unknown CURLINFO options

* Fri Sep 18 2015 Paul Howarth <paul@city-fan.org> - 7.44.0-2.0.cf
- Prevent NSS from incorrectly re-using a session (#1104597)

* Wed Aug 12 2015 Paul Howarth <paul@city-fan.org> - 7.44.0-1.0.cf
- Update to 7.44.0
  - http2: Added CURLMOPT_PUSHFUNCTION and CURLMOPT_PUSHDATA
  - examples: Added http2-serverpush.c
  - http2: Added curl_pushheader_byname() and curl_pushheader_bynum()
  - docs: Added CODE_OF_CONDUCT.md
  - curl: Add --ssl-no-revoke to disable certificate revocation checks
  - libcurl: New value CURLSSLOPT_NO_REVOKE for CURLOPT_SSL_OPTIONS
  - makefile: Added support for VC14
  - build: Added Visual Studio 2015 (VC14) project files
  - build: Added wolfSSL configurations to VC10+ project files
  - FTP: Fix HTTP CONNECT logic regression
  - openssl: Fix build with openssl < ~ 0.9.8f
  - openssl: Fix build with BoringSSL
  - curl_easy_setopt.3: Option order doesn't matter
  - openssl: Fix use of uninitialized buffer
  - RTSP: Removed dead code
  - Makefile.m32: Add support for CURL_LDFLAG_EXTRAS
  - curl: Always provide negotiate/kerberos options
  - cookie: Fix bug in export if any-domain cookie is present
  - curl_easy_setopt.3: Mention CURLOPT_PIPEWAIT
  - INSTALL: Advise use of non-native SSL for Windows <= XP
  - tool_help: Fix --tlsv1 help text to use >= for TLSv1
  - HTTP: POSTFIELDSIZE set after added to multi handle
  - SSL-PROBLEMS: Mention WinSSL problems in WinXP
  - setup-vms.h: Symbol case fixups
  - SSL: Pinned public key hash support
  - libtest: Call PR_Cleanup() on exit if NSPR is used
  - ntlm_wb: Fix theoretical memory leak
  - runtests: Allow for spaces in curl custom path
  - http2: Add stream != NULL checks for reliability
  - schannel: Replace deprecated GetVersion with VerifyVersionInfo
  - http2: Verify success of strchr() in http2_send()
  - configure: Add --disable-rt option
  - openssl: Work around MSVC warning
  - HTTP: Ignore "Content-Encoding: compress"
  - configure: Check if OpenSSL linking wants -ldl
  - build-openssl.bat: Show syntax if required args are missing
  - test1902: Attempt to make the test more reliable
  - libcurl-thread.3: Consolidate thread safety info
  - maketgz: Fixed some VC makefiles missing from the release tarball
  - libcurl-multi.3: Mention curl_multi_wait
  - ABI doc: Use secure URL
  - http: Move HTTP/2 cleanup code off http_disconnect()
  - libcurl-thread.3: Warn memory functions must be thread safe
  - curl_global_init_mem.3: Warn threaded resolver needs thread safe funcs
  - docs: formpost needs the full size at start of upload
  - curl_gssapi: Remove 'const' to fix compiler warnings
  - SSH: Three state machine fixups
  - libcurl.3: Fix a single typo
  - generate.bat: Only clean prerequisite files when in ALL mode
  - curl_slist_append.3: Add error checking to the example
  - buildconf.bat: Added support for file clean-up via -clean
  - generate.bat: Use buildconf.bat for prerequisite file clean-up
  - NTLM: Handle auth for only a single request
  - curl_multi_remove_handle.3: Fix formatting
  - checksrc.bat: Fixed error when [directory] isn't a curl source directory
  - checksrc.bat: Fixed error when missing *.c and *.h files
  - CURLOPT_RESOLVE.3: Note removal support was added in 7.42
  - test46: Update cookie expire time
  - SFTP: Fix range request off-by-one in size check
  - CMake: Fix GSSAPI builds
  - build: Refer to fixed libidn versions
  - http2: Discard frames with no SessionHandle
  - curl_easy_recv.3: Fix formatting
  - libcurl-tutorial.3: Fix formatting
  - curl_formget.3: Correct return code

* Thu Jul 30 2015 Paul Howarth <paul@city-fan.org> - 7.43.0-3.0.cf
- Prevent dnf from crashing when using both FTP and HTTP (#1248389)
- Add HTTP/2 protocol support for Fedora 23 too

* Sat Jul 18 2015 Paul Howarth <paul@city-fan.org> - 7.43.0-2.0.cf
- Build support for the HTTP/2 protocol (Fedora 24 onwards)

* Wed Jun 17 2015 Paul Howarth <paul@city-fan.org> - 7.43.0-1.0.cf
- Update to 7.43.0
  - CVE-2015-3236: Lingering HTTP credentials in connection re-use
  - CVE-2015-3237: SMB send off unrelated memory contents
  - Added CURLOPT_PROXY_SERVICE_NAME
  - Added CURLOPT_SERVICE_NAME
  - New curl option: --proxy-service-name
  - New curl option: --service-name
  - New curl option: --data-raw
  - Added CURLOPT_PIPEWAIT
  - Added support for multiplexing transfers using HTTP/2, enable this
    with the new CURLPIPE_MULTIPLEX bit for CURLMOPT_PIPELINING
  - HTTP/2: Requires nghttp2 1.0.0 or later
  - scripts: Add zsh.pl for generating zsh completion
  - curl.h: Add CURL_HTTP_VERSION_2
  - nss: Fix compilation failure with old versions of NSS
  - curl_easy_getinfo.3: Document 'internals' in CURLINFO_TLS_SESSION
  - schannel.c: Fix possible SEC_E_BUFFER_TOO_SMALL error
  - Curl_ossl_init: Load built-in modules
  - configure: Follow-up fix for krb5-config
  - sasl_sspi: Populate domain from the realm in the challenge
  - netrc: Support 'default' token
  - README: Convert to UTF-8
  - cyassl: Implement public key pinning
  - nss: Implement public key pinning for NSS backend
  - mingw build: Add arch -m32/-m64 to LDFLAGS
  - schannel: Fix out of bounds array
  - configure: Remove autogenerated files by autoconf
  - configure: Remove --automake from libtoolize call
  - acinclude.m4: Fix shell test for default CA cert bundle/path
  - schannel: Fix regression in schannel_recv
  - openssl: Skip trace outputs for ssl_ver == 0
  - gnutls: Properly retrieve certificate status
  - netrc: Read in text mode when cygwin
  - winbuild: Document the option used to statically link the CRT
  - FTP: Make EPSV use the control IP address rather than the original host
  - FTP: fIx dangling conn->ip_addr dereference on verbose EPSV
  - conncache: Keep bundles on host+port bases, not only host names
  - runtests.pl: Use 'h2c' now, no -14 anymore
  - curlver: Introducing new version number (checking) macros
  - openssl: boringssl build breakage, use SSL_CTX_set_msg_callback
  - CURLOPT_POSTFIELDS.3: Correct variable names
  - curl_easy_unescape.3: Update RFC reference
  - gnutls: Don't fail on non-fatal alerts during handshake
  - testcurl.pl: Allow source to be in an arbitrary directory
  - CURLOPT_HTTPPROXYTUNNEL.3: Only works with a HTTP proxy
  - SSPI-error: Change SEC_E_ILLEGAL_MESSAGE description
  - parse_proxy: Switch off tunneling if non-HTTP proxy
  - share_init: Fix OOM crash
  - perl: Remove subdir, not touched in 9 years
  - CURLOPT_COOKIELIST.3: Add example
  - CURLOPT_COOKIE.3: Explain that the cookies won't be modified
  - CURLOPT_COOKIELIST.3: Explain Set-Cookie without a domain
  - FAQ: How do I port libcurl to my OS?
  - openssl: Use TLS_client_method for OpenSSL 1.1.0+
  - HTTP-NTLM: Fail auth on connection close instead of looping
  - curl_setup: Add macros for FOPEN_READTEXT, FOPEN_WRITETEXT
  - curl_getdate.3: Update RFC reference
  - curl_multi_info_read.3: Added example
  - curl_multi_perform.3: Added example
  - curl_multi_timeout.3: Added example
  - cookie: Stop exporting any-domain cookies
  - openssl: Remove dummy callback use from SSL_CTX_set_verify()
  - openssl: Remove SSL_get_session()-using code
  - openssl: Removed USERDATA_IN_PWD_CALLBACK kludge
  - openssl: Removed error string #ifdef
  - openssl: Fix verification of server-sent legacy intermediates
  - docs: man page indentation and syntax fixes
  - docs: Spelling fixes
  - fopen.c: Fix a few compiler warnings
  - CURLOPT_OPENSOCKETFUNCTION: Return error at once
  - schannel: Add support for optional client certificates
  - build: Properly detect OpenSSL 1.0.2 when using configure
  - urldata: Store POST size in state.infilesize too
  - security: choose_mech: Remove dead code
  - rtsp_do: Remove dead code
  - docs: Many HTTP URIs changed to HTTPS
  - schannel: schannel_recv overhaul
- Fix build for old openssl versions without SSL3_MT_NEWSESSION_TICKET

* Sat Jun  6 2015 Paul Howarth <paul@city-fan.org> - 7.42.1-2.0.cf
- curl-config --libs now works on x86_64 without libcurl-devel.x86_64
  (#1228363)

* Wed Apr 29 2015 Paul Howarth <paul@city-fan.org> - 7.42.1-1.0.cf
- Update to 7.42.1
  - CURLOPT_HEADEROPT: default to separate (CVE-2015-3153)
  - dist: include {src,lib}/checksrc.whitelist
  - connectionexists: fix build without NTLM
  - docs: distribute the CURLOPT_PINNEDPUBLICKEY(3) man page, too
  - curl -z: do not write empty file on unmet condition
  - openssl: fix serial number output
  - curl_easy_getinfo.3: document 'internals' in CURLINFO_TLS_SESSION
  - sws: init http2 state properly
  - curl.1: fix typo

* Wed Apr 22 2015 Paul Howarth <paul@city-fan.org> - 7.42.0-1.1.cf
- Implement public key pinning for NSS backend (#1195771)
- Do not run flaky test-cases in %%check

* Wed Apr 22 2015 Paul Howarth <paul@city-fan.org> - 7.42.0-1.0.cf
- Update to 7.42.0
  - openssl: Show the cipher selection to use in verbose text
  - gtls: Implement CURLOPT_CERTINFO
  - Add CURLOPT_SSL_FALSESTART option (darwinssl and NSS)
  - curl: Add --false-start option
  - Add CURLOPT_PATH_AS_IS
  - curl: Add --path-as-is option
  - curl: Create output file on successful download of an empty file
  - ConnectionExists: For NTLM re-use, require credentials to match
    (CVE-2015-3143)
  - Cookie: Cookie parser out of boundary memory access (CVE-2015-3145)
  - fix_hostname: Zero length host name caused -1 index offset (CVE-2015-3144)
  - http_done: Close Negotiate connections when done (CVE-2015-3148)
  - sws: Timeout idle CONNECT connections
  - nss: Improve error handling in Curl_nss_random()
  - nss: Do not skip Curl_nss_seed() if data is NULL
  - curl-config.in: Eliminate double quotes around CURL_CA_BUNDLE
  - http2: Move lots of verbose output to be debug-only
  - dist: Add extern-scan.pl to the tarball
  - http2: Return recv error on unexpected EOF
  - build: Use default RandomizedBaseAddress directive in VC9+ project files
  - build: Removed DataExecutionPrevention directive from VC9+ project files
  - tool: Updated the warnf() function to use the GlobalConfig structure
  - http2: Return error if stream was closed with other than NO_ERROR
  - mprintf.h: Remove #ifdef CURLDEBUG
  - libtest: Fixed linker errors on msvc
  - tool: Use ENABLE_CURLX_PRINTF instead of _MPRINTF_REPLACE
  - curl.1: Fix "The the" typo
  - cmake: Handle build definitions CURLDEBUG/DEBUGBUILD
  - openssl: Remove all uses of USE_SSLEAY
  - multi: Fix memory-leak on timeout (regression)
  - curl_easy_setopt.3: Added CURLOPT_SSL_VERIFYSTATUS
  - metalink: Add some error checks
  - TLS: Make it possible to enable ALPN/NPN without HTTP/2
  - http2: Use CURL_HTTP_VERSION_* symbols instead of NPN_*
  - conncontrol: Only log changes to the connection bit
  - multi: Fix *getsock() with CONNECT
  - symbols.pl: Handle '-' in the deprecated field
  - MacOSX-Framework: Use @rpath instead of @executable_path
  - GnuTLS: Add support for CURLOPT_CAPATH
  - GnuTLS: Print negotiated TLS version and full cipher suite name
  - GnuTLS: Don't print double newline after certificate dates
  - memanalyze.pl: Handle free(NULL)
  - proxy: Re-use proxy connections (regression)
  - mk-ca-bundle: Don't report SHA1 numbers with "-q"
  - http: Always send Host: header as first header
  - openssl: Sort ciphers to use based on strength
  - openssl: Use colons properly in the ciphers list
  - http2: Detect premature close without data transferred
  - hostip: Fix signal race in Curl_resolv_timeout
  - closesocket: Call multi socket cb on close even with custom close
  - mksymbolsmanpage.pl: Use std header and generate better nroff header
  - connect: Fix happy eyeballs logic for IPv4-only builds
  - curl_easy_perform.3: Remove superfluous close brace from example
  - HTTP: Don't use Expect: headers when on HTTP/2
  - Curl_sh_entry: Remove unused 'timestamp'
  - docs/libcurl: Makefile portability fix
  - mkhelp: Remove trailing carriage return from every line of input
  - nss: Explicitly tell NSS to disable NPN/ALPN when libcurl disables it
  - curl_easy_setopt.3: Added a few missing options
  - metalink: Fix resource leak in OOM
  - axtls: Version 1.5.2 now requires that config.h be manually included
  - HTTP: Don't switch to HTTP/2 from 1.1 until we get the 101
  - cyassl: Detect the library as renamed wolfssl
  - CURLOPT_HTTPHEADER.3: Add a "SECURITY CONCERNS" section
  - CURLOPT_URL.3: Added "SECURITY CONCERNS"
  - openssl: Try to avoid accessing OCSP structs when possible
  - test938: Added missing closing tags
  - testcurl: Allow '=' in values given on command line
  - tests/certs: Added make target to rebuild certificates
  - tests/certs: Rebuild certificates with modified key usage bits
  - gtls: Avoid uninitialized variable
  - gtls: Dereferencing NULL pointer
  - gtls: Add check of return code
  - test1513: Eliminated race condition in test run
  - dict: Rename byte to avoid compiler shadowed declaration warning
  - curl_easy_recv/send: Make them work with the multi interface
  - vtls: Fix compile with --disable-crypto-auth but with SSL
  - openssl: Adapt to ASN1/X509 things gone opaque in 1.1
  - openssl: verifystatus: Only use the OCSP work-around <= 1.0.2a
  - curl_memory: Make curl_memory.h the second-last header file loaded
  - testcurl.pl: Add the --notes option to supply more info about a build
  - cyassl: If wolfSSL then identify as such in version string
  - cyassl: Check for invalid length parameter in Curl_cyassl_random
  - cyassl: Default to highest possible TLS version
  - Curl_ssl_md5sum: Return CURLcode (fixes OOM)
  - polarssl: Remove dead code
  - polarssl: Called mbedTLS in 1.3.10 and later
  - globbing: Fix step parsing for character globbing ranges
  - globbing: Fix url number calculation when using range with step
  - multi: On a request completion, check all CONNECT_PEND transfers
  - build: Link curl to openssl libraries when openssl support is enabled
  - url: Don't accept CURLOPT_SSLVERSION unless USE_SSL is defined
  - vtls: Don't accept unknown CURLOPT_SSLVERSION values
  - build: Fix libcurl.sln erroneous mixed configurations
  - cyassl: Remove undefined reference to CyaSSL_no_filesystem_verify
  - cyassl: Add SSL context callback support for CyaSSL
  - tool: Only set SSL options if SSL is enabled
  - multi: Remove_handle: move pending connections
  - configure: Use KRB5CONFIG for krb5-config
  - axtls: Add timeout within Curl_axtls_connect
  - CURLOPT_HTTP200ALIASES.3: Mainly SHOUTcast servers use "ICY 200"
  - cyassl: Fix library initialization return value
  - cookie: Handle spaces after the name in Set-Cookie
  - http2: Fix missing nghttp2_session_send call in Curl_http2_switched
  - cyassl: Fix certificate load check
  - build-openssl.bat: Fix mixed line endings
  - checksrc.bat: Check lib\vtls source
  - DNS: Fix refreshing of obsolete dns cache entries
  - CURLOPT_RESOLVE: Actually implement removals
  - checksrc.bat: Quotes to support an SRC_DIR with spaces
  - cyassl: Remove 'Connecting to' message from cyassl_connect_step2
  - cyassl: Use CYASSL_MAX_ERROR_SZ for error buffer size
  - lib/transfer.c: Remove factor of 8 from sleep time calculation
  - lib/makefile.m32: Add missing libs to build libcurl.dll
  - build: Generate source prerequisites for Visual Studio in generate.bat
  - cyassl: Include the CyaSSL build config
  - firefox-db2pem: Fix wildcard to find Firefox default profile
  - BUGS: Refer to the github issue tracker now as primary
  - vtls_openssl: Improve several certificate error messages
  - cyassl: Add support for TLS extension SNI
  - parsecfg: Do not continue past a zero termination
  - configure --with-nss=PATH: Query pkg-config if available
  - configure --with-nss: Drop redundant if statement
  - cyassl: Fix include order
  - HTTP: Fix PUT regression with Negotiate
  - curl_version_info.3: Fixed the 'protocols' variable type
- Add patch to disabled unsupported TLS False Start support in NSS builds
  with NSS < 3.15.4

* Wed Feb 25 2015 Paul Howarth <paul@city-fan.org> - 7.41.0-1.0.cf
- Update to 7.41.0
  - NetWare build: added TLS-SRP enabled build
  - winbuild: Added option to build with c-ares
  - Added --cert-status
  - Added CURLOPT_SSL_VERIFYSTATUS
  - sasl: Implement EXTERNAL authentication mechanism
  - sasl_gssapi: Fixed build on NetBSD with built-in GSS-API
  - FTP: Fix IPv6 host using link-local address
  - FTP: If EPSV fails on IPV6 connections, bail out
  - gssapi: Remove need for duplicated GSS_C_NT_HOSTBASED_SERVICE definitions
  - NSS: Fix compiler error when built http2-enabled
  - mingw build: allow to pass custom CFLAGS
  - Add -m64 CFLAGS when targeting mingw64, add -m32/-m64 to LDFLAGS
  - curl_schannel.c: Mark session as removed from cache if not freed
  - Curl_pretransfer: Reset expected transfer sizes
  - curl.h: Remove extra space
  - curl_endian: Fixed build when 64-bit integers are not supported
  - checksrc.bat: Better detection of Perl installation
  - build-openssl.bat: Added check for Perl installation
  - http_negotiate: Return CURLcode in Curl_input_negotiate() instead of int
  - http_negotiate: Added empty decoded challenge message info text
  - vtls: Removed unimplemented overrides of curlssl_close_all()
  - sasl_gssapi: Fixed memory leak with local SPN variable
  - http_negotiate: Use dynamic buffer for SPN generation
  - ldap: Renamed the CURL_LDAP_WIN definition to USE_WIN32_LDAP
  - openssl: Do public key pinning check independently
  - timeval: Typecast for better type (on Amiga)
  - ipv6: Enclose AF_INET6 uses with proper #ifdefs for ipv6
  - SASL: Common URL option and auth capabilities decoders for all protocols
  - BoringSSL: Fix build
  - BoringSSL: Detected by configure, switches off NTLM
  - openvms: Handle openssl/0.8.9zb version parsing
  - configure: Detect libresssl
  - configure: Remove detection of the old yassl emulation API
  - curl_setup: Disable SMB/CIFS support when HTTP only
  - imap: Remove automatic password setting: it breaks external sasl authentication
  - sasl: Remove XOAUTH2 from default enabled authentication mechanism
  - runtests: Identify BoringSSL and libressl
  - Security: Avoid compiler warning
  - ldap: Build with BoringSSL
  - des: Added Curl_des_set_odd_parity()
  - CURLOPT_SEEKFUNCTION.3: also when server closes a connection
  - CURLOPT_HTTP_VERSION.3: CURL_HTTP_VERSION_2_0 added in 7.33.0
  - build: Removed unused Visual Studio bscmake settings
  - build: Enabled DEBUGBUILD in Visual Studio debug builds
  - build: Renamed top level Visual Studio solution files
  - build: Removed Visual Studio SuppressStartupBanner directive for VC8+
  - libcurl-symbols: First basic shot for autogenerated docs
  - Makefile.am: fix 'make distcheck'
  . getpass_r: Read from stdin, not stdout!
  - getpass: Protect include with proper #ifdef
  - opts: CURLOPT_CAINFO availability depends on SSL engine
  - More cleanup of 'CURLcode result' return code
  - MD4: Replace implementation
  - MD5: Replace implementation
  - openssl: SSL_SESSION->ssl_version no longer exist
  - md5: use axTLS's own MD5 functions when available
  - schannel: Removed curl_ prefix from source files
  - curl.1: Add warning when using -H and redirects
  - curl.1: Clarify that -X is used for all requests
  - gskit: Fix exclusive SSLv3 option
  - polarssl: Fix exclusive SSL protocol version options
  - http2: Fix bug that associated stream canceled on PUSH_PROMISE
  - ftp: Accept all 2xx responses to the PORT command
  - configure: Allow both --with-ca-bundle and --with-ca-path
  - cmake: Install the dll file to the correct directory
  - nss: Fix NPN/ALPN protocol negotiation
  - polarssl: Fix ALPN protocol negotiation
  - cmake: Fix generation of tool_hugehelp.c on windows
  - cmake: Fix winsock2 detection on windows
  - gnutls: Fix build with HTTP2
  - connect: Fix a spurious connect failure on dual-stacked hosts
  - test: Test 530 is now less timing dependent
  - telnet: Invalid use of custom read function if not set
- Include extern-scan.pl to make test1135 succeed (upstream commit 1514b718)

* Mon Feb 23 2015 Paul Howarth <paul@city-fan.org> - 7.40.0-3.0.cf
- Fix a spurious connect failure on dual-stacked hosts (#1187531)

* Sun Feb 22 2015 Paul Howarth <paul@city-fan.org> - 7.40.0-2.0.cf
- Rebuilt for Fedora 23 Change
  https://fedoraproject.org/wiki/Changes/Harden_all_packages_with_position-independent_code

* Thu Jan  8 2015 Paul Howarth <paul@city-fan.org> - 7.40.0-1.0.cf
- Update to 7.40.0 (addresses CVE-2014-8150 and CVE-2014-8151)
  - http_digest: added support for Windows SSPI based authentication
  - version info: added Kerberos V5 to the supported features
  - Makefile: added VC targets for WinIDN
  - config-win32: introduce build targets for VS2012+
  - SSL: add PEM format support for public key pinning
  - smtp: added support for the conversion of Unix newlines during mail send
  - smb: added initial support for the SMB/CIFS protocol
  - added support for HTTP over unix domain sockets, via
    CURLOPT_UNIX_SOCKET_PATH and --unix-socket
  - sasl: added support for GSS-API based Kerberos V5 authentication
  - darwinssl: fix session ID keys to only reuse identical sessions
  - url-parsing: reject CRLFs within URLs
  - OS400: adjust specific support to last release
  - THANKS: remove duplicate names
  - url.c: fixed compilation warning
  - ssh: fixed build on platforms where R_OK is not defined
  - tool_strdup.c: include the tool strdup.h
  - build: fixed Visual Studio project file generation of strdup.[c|h]
  - curl_easy_setopt.3: add CURLOPT_PINNEDPUBLICKEY
  - curl.1: show zone index use in a URL
  - mk-ca-bundle.vbs: switch to new certdata.txt url
  - Makefile.dist: added some missing SSPI configurations
  - build: fixed no NTLM support for email when CURL_DISABLE_HTTP is defined
  - SSH: use the port number as well for known_known checks
  - libssh2: detect features based on version, not configure checks
  - http2: deal with HTTP/2 data inside Upgrade response header buffer
  - multi: removed Curl_multi_set_easy_connection
  - symbol-scan.pl: do not require autotools
  - cmake: add ENABLE_THREADED_RESOLVER, rename ARES
  - cmake: build libhostname for test suite
  - cmake: fix HAVE_GETHOSTNAME definition
  - tests: fix libhostname visibility
  - tests: fix memleak in server/resolve.c
  - vtls.h: fixed compiler warning when compiled without SSL
  - CMake: restore order-dependent header checks
  - CMake: restore order-dependent library checks
  - tool: removed krb4 from the supported features
  - http2: don't send Upgrade headers when we already do HTTP/2
  - examples: don't call select() to sleep on windows
  - win32: updated some legacy APIs to use the newer extended versions
  - easy.c: fixed compilation warning when no verbose string support
  - connect.c: fixed compilation warning when no verbose string support
  - build: in Makefile.m32 pass -F flag to windres
  - build: in Makefile.m32 add -m32 flag for 32bit
  - multi: when leaving for timeout, close accordingly
  - CMake: simplify if() conditions on check result variables
  - build: in Makefile.m32 try to detect 64bit target
  - multi: inform about closed sockets before they are closed
  - multi-uv.c: close the file handle after download
  - examples: wait recommended 100ms when no file descriptors are ready
  - ntlm: split the SSPI based messaging code from the native messaging code
  - cmake: fix NTLM detection when CURL_DISABLE_HTTP defined
  - cmake: add Kerberos to the supported feature
  - CURLOPT_POSTFIELDS.3: mention the COPYPOSTFIELDS option
  - http: disable pipelining for HTTP/2 and upgraded connections
  - ntlm: fixed static'ness of local decode function
  - sasl: reduced the need for two sets of NTLM messaging functions
  - multi.c: fixed compilation warnings when no verbose string support
  - select.c: fix compilation for VxWorks
  - multi-single.c: switch to use curl_multi_wait
  - curl_multi_wait.3: clarify numfds being used if not NULL
  - http.c: fixed compilation warnings from features being disabled
  - NSS: enable the CAPATH option
  - docs: fix FAILONERROR typos
  - HTTP: don't abort connections with pending Negotiate authentication
  - HTTP: free (proxy)userpwd for NTLM/Negotiate after sending a request
  - http_perhapsrewind: don't abort CONNECT requests
  - build: updated dependencies in makefiles
  - multi.c: fixed compilation warning
  - ftp.c: fixed compilation warnings when proxy support disabled
  - get_url_file_name: fixed crash on OOM on debug build
  - cookie.c: refactored cleanup code to simplify
  - OS400: enable NTLM authentication
  - ntlm: use Windows Crypt API
  - http2: avoid logging neg "failure" if h2 was not requested
  - schannel_recv: return the correct code
  - VC build: added sspi define for winssl-zlib builds
  - Curl_client_write(): chop long data, convert data only once
  - openldap: do not ignore Curl_client_write() return code
  - ldap: check Curl_client_write() return codes
  - parsedate.c: fixed compilation warning
  - url.c: fixed compilation warning when USE_NTLM is not defined
  - ntlm_wb_response: fix "statement not reached"
  - telnet: fix "cast increases required alignment of target type"
  - smtp: fixed dot stuffing when EOL characters at end of input buffers
  - ntlm: allow NTLM2Session messages when USE_NTRESPONSES manually defined
  - ntlm: disable NTLM v2 when 64-bit integers are not supported
  - ntlm: use short integer when decoding 16-bit values
  - ftp.c: fixed compilation warning when no verbose string support
  - synctime.c: fixed timeserver URLs
  - mk-ca-bundle.pl: restored forced run again
  - ntlm: fixed return code for bad type-2 Target Info
  - curl_schannel.c: data may be available before connection shutdown
  - curl_schannel: improvements to memory re-allocation strategy
  - darwinssl: aprintf() to allocate the session key
  - tool_util.c: use GetTickCount64 if it is available
  - lib: fixed multiple code analysis warnings if SAL are available
  - tool_binmode.c: explicitly ignore the return code of setmode
  - tool_urlglob.c: silence warning C6293: Ill-defined for-loop
  - opts: warn CURLOPT_TIMEOUT overrides when set after CURLOPT_TIMEOUT_MS
  - SFTP: work-around servers that return zero size on STAT
  - connect: singleipconnect(): properly try other address families after failure
  - IPV6: address scope != scope id
  - parseurlandfillconn(): fix improper non-numeric scope_id stripping
  - secureserver.pl: make OpenSSL CApath and cert absolute path values
  - secureserver.pl: update Windows detection and fix path conversion
  - secureserver.pl: clean up formatting of config and fix verbose output
  - tests: added Windows support using Cygwin-based OpenSSH
  - sockfilt.c: use non-Ex functions that are available before WinXP
  - VMS: updates for 0740-0D1220
  - openssl: warn for SRP set if SSLv3 is used, not for TLS version
  - openssl: make it compile against openssl 1.1.0-DEV master branch
  - openssl: fix SSL/TLS versions in verbose output
  - curl: show size of inhibited data when using -v
  - build: removed WIN32 definition from the Visual Studio projects
  - build: removed WIN64 definition from the libcurl Visual Studio projects
  - vtls: use bool for Curl_ssl_getsessionid() return type
  - sockfilt.c: replace 100ms sleep with thread throttle
  - sockfilt.c: reduce the number of individual memory allocations
  - vtls: don't set cert info count until memory allocation is successful
  - nss: don't ignore Curl_ssl_init_certinfo() OOM failure
  - nss: don't ignore Curl_extract_certinfo() OOM failure
  - vtls: fixed compilation warning and an ignored return code
  - sockfilt.c: fixed compilation warnings
  - darwinssl: fixed compilation warning
  - vtls: use '(void) arg' for unused parameters
  - sepheaders.c: fixed resource leak on failure
  - lib1900.c: fixed cppcheck error
  - ldap: fixed Unicode connection details in Win32 initialsation / bind calls
  - ldap: fixed Unicode DN, attributes and filter in Win32 search calls
- re-enable test 2034 (https with certificate pinning) as it seems to be
  working again on EL
- update patches as needed
- replace metalink patch with an openssl-specific version, since nss is fixed
  upstream
- BR: python for http-pipe testing

* Wed Nov  5 2014 Paul Howarth <paul@city-fan.org> - 7.39.0-1.0.cf
- update to 7.39.0 (addresses CVE-2014-3707)
  - SSLv3 is disabled by default
  - CURLOPT_COOKIELIST: added "RELOAD" command
  - build: added WinIDN build configuration options to Visual Studio projects
  - ssh: improve key file search
  - SSL: public key pinning - use CURLOPT_PINNEDPUBLICKEY and --pinnedpubkey
  - vtls: remove QsoSSL support, use gskit!
  - mk-ca-bundle: added SHA-384 signature algorithm
  - docs: added many examples for libcurl opts and other doc improvements
  - build: added VC ssh2 target to main Makefile
  - MinGW: added support to build with nghttp2
  - NetWare: added support to build with nghttp2
  - build: added Watcom support to build with WinSSL
  - build: added optional specific version generation of VC project files
  - curl_easy_duphandle: CURLOPT_COPYPOSTFIELDS read out of bounds
  - openssl: build fix for versions < 0.9.8e
  - newlines: fix mixed newlines to LF-only
  - ntlm: fixed HTTP proxy authentication when using Windows SSPI
  - sasl_sspi: fixed Unicode build
  - file: reject paths using embedded %%00
  - threaded-resolver: revert Curl_expire_latest() switch
  - configure: allow --with-ca-path with PolarSSL too
  - HTTP/2: fix busy loop when EOF is encountered
  - CURLOPT_CAPATH: return failure if set without backend support
  - nss: do not fail if a CRL is already cached
  - smtp: fixed intermittent "SSL3_WRITE_PENDING: bad write retry" error
  - fixed 20+ nits/memory leaks identified by Coverity scans
  - curl_schannel.c: fixed possible memory or handle leak
  - multi-uv.c: call curl_multi_info_read() better
  - Cmake: check for OpenSSL before OpenLDAP
  - Cmake: fix library list provided to cURL tests
  - Cmake: avoid cycle directory dependencies
  - Cmake: build with GSS-API libraries (MIT or Heimdal)
  - vtls: provide backend defines for internal source code
  - nss: fix a connection failure when FTPS handle is reused
  - tests/http_pipe.py: Python 3 support
  - cmake: build tool_hugehelp (ENABLE_MANUAL)
  - cmake: enable IPv6 by default if available
  - tests: move TESTCASES to Makefile.inc, add show for cmake
  - ntlm: avoid unnecessary buffer allocation for SSPI based type-2 token
  - ntlm: fixed empty/bad base-64 decoded buffer return codes
  - ntlm: fixed empty type-2 decoded message info text
  - cmake: add CMake/Macros.cmake to the release tarball
  - cmake: add SUPPORT_FEATURES and SUPPORT_PROTOCOLS
  - cmake: use LIBCURL_VERSION from curlver.h
  - cmake: generate pkg-config and curl-config
  - fixed several superfluous variable assignements identified by cppcheck
  - cleanup of 'CURLcode result' return code
  - pipelining: only output "is not blacklisted" in debug builds
  - SSL: remove SSLv3 from SSL default due to POODLE attack
  - gskit.c: remove SSLv3 from SSL default
  - darwinssl: detect possible future removal of SSLv3 from the framework
  - ntlm: only define ntlm data structure when USE_NTLM is defined
  - ntlm: return CURLcode from Curl_ntlm_core_mk_lm_hash()
  - ntlm: return all errors from Curl_ntlm_core_mk_nt_hash()
  - sspi: only call CompleteAuthToken() when complete is needed
  - http_negotiate: fixed missing check for USE_SPNEGO
  - HTTP: return larger than 3 digit response codes too
  - openssl: check for NPN / ALPN via OpenSSL version number
  - openssl: enable NPN separately from ALPN
  - sasl_sspi: allow DIGEST-MD5 to use current windows credentials
  - sspi: return CURLE_LOGIN_DENIED on AcquireCredentialsHandle() failure
  - resume: consider a resume from [content-length] to be OK
  - sasl: fixed Kerberos V5 inclusion when CURL_DISABLE_CRYPTO_AUTH is used
  - build-openssl.bat: fix x64 release build
  - cmake: drop _BSD_SOURCE macro usage
  - cmake: fix gethostby{addr,name}_r in CurlTests
  - cmake: clean OtherTests, fixing -Werror
  - cmake: fix struct sockaddr_storage check
  - Curl_single_getsock: fix hold/pause sock handling
  - SSL: PolarSSL default min SSL version TLS 1.0
  - cmake: fix ZLIB_INCLUDE_DIRS use
  - buildconf: stop checking for libtool
- disable test 2034 (https with certificate pinning) on EL-5/6 until such time
  as we can figure out why it breaks
  (http://curl.haxx.se/mail/lib-2014-11/0040.html)

* Tue Oct 21 2014 Paul Howarth <paul@city-fan.org> - 7.38.0-2.0.cf
- fix a connection failure when FTPS handle is reused

* Wed Sep 10 2014 Paul Howarth <paul@city-fan.org> - 7.38.0-1.0.cf
- update to 7.38.0
  - CVE-2014-3613: cookie leak with IP address as domain
  - CVE-2014-3620: cookie leak for TLDs
  - CURLE_HTTP2 is a new error code
  - CURLAUTH_NEGOTIATE is a new auth define
  - CURL_VERSION_GSSAPI is a new capability bit
  - no longer use fbopenssl for anything
  - schannel: use CryptGenRandom for random numbers
  - axtls: define curlssl_random using axTLS's PRNG
  - cyassl: use RNG_GenerateBlock to generate a good random number
  - findprotocol: show unsupported protocol within quotes
  - version: detect and show LibreSSL
  - version: detect and show BoringSSL
  - imap/pop3/smtp: Kerberos (SASL GSSAPI) authentication via Windows SSPI
  - http2: requires nghttp2 0.6.0 or later
  - fix a build failure on Debian when NSS support is enabled
  - HTTP/2: fixed compiler warnings when built disabled
  - cyassl: return the correct error code on no CA cert
  - http: deprecate GSS-Negotiate macros due to bad naming
  - http: fixed Negotiate: authentication
  - multi: improve proxy CONNECT performance (regression)
  - ntlm_wb: avoid invoking ntlm_auth helper with empty username
  - ntlm_wb: fix hard-coded limit on NTLM auth packet size
  - url.c: use the preferred symbol name: *READDATA
  - smtp: fixed a segfault during test 1320 torture test
  - cyassl: made it compile with version 2.0.6 again
  - nss: do not check the version of NSS at run time
  - c-ares: fix build without IPv6 support
  - HTTP/2: use base64url encoding
  - SSPI Negotiate: fix 3 memory leaks
  - libtest: fixed duplicated line in Makefile
  - conncache: fix compiler warning
  - openssl: make ossl_send return CURLE_OK better
  - HTTP/2: support expect: 100-continue
  - HTTP/2: fix infinite loop in readwrite_data()
  - parsedate: fix the return code for an overflow edge condition
  - darwinssl: don't use strtok()
  - http_negotiate_sspi: fixed specific username and password not working
  - openssl: replace call to OPENSSL_config
  - http2: show the received header for better debugging
  - HTTP/2: move :authority before non-pseudo header fields
  - HTTP/2: reset promised stream, not its associated stream
  - HTTP/2: added some more logging for debugging stream problems
  - ntlm: added support for SSPI package info query
  - ntlm: fixed hard coded buffer for SSPI based auth packet generation
  - sasl_sspi: fixed memory leak with not releasing Package Info struct
  - sasl_sspi: fixed SPN not being converted to wchar under Unicode builds
  - sasl: use a dynamic buffer for DIGEST-MD5 SPN generation
  - http_negotiate_sspi: use a dynamic buffer for SPN generation
  - sasl_sspi: fixed missing free of challenge buffer on SPN failure
  - sasl_sspi: fixed hard coded buffer for response generation
  - Curl_poll + Curl_wait_ms: fix timeout return value
  - docs/SSLCERTS: update the section about NSS database
  - create_conn: prune dead connections
  - openssl: fix version report for the 0.9.8 branch
  - mk-ca-bundle.pl: switched to using hg.mozilla.org
  - http: fix the Content-Range: parser
  - Curl_disconnect: don't free the URL
  - win32: fixed WinSock 2 #if
  - NTLM: ignore CURLOPT_FORBID_REUSE during NTLM HTTP auth
  - curl.1: clarify --limit-rate's effect on both directions
  - disconnect: don't touch easy-related state on disconnects
  - Cmake: big cleanup and numerous fixes
  - HTTP/2: supports draft-14 - moved :headers before the non-psuedo headers
  - configure.ac: add support for recent GSS-API implementations for HP-UX
  - CONNECT: close proxy connections that fail
  - CURLOPT_NOBODY.3: clarify this option is for downloads
  - darwinssl: fix CA certificate checking using PEM format
  - resolve: cache lookup for async resolvers
  - low-speed-limit: avoid timeout flood
  - polarssl: implement CURLOPT_SSLVERSION
  - multi: convert CURLM_STATE_CONNECT_PEND handling to a list
  - curl_multi_cleanup: remove superfluous NULL assigns
  - polarssl: support CURLOPT_CAPATH / --capath
  - progress: size_dl/size_ul are always >= 0, and clear "KNOWN" properly
- add workaround for build with openssl < 0.9.8e

* Sun Aug 17 2014 Paul Howarth <paul@city-fan.org> - 7.37.1-3.0.cf
- rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Wed Aug 13 2014 Paul Howarth <paul@city-fan.org> - 7.37.1-2.0.cf
- tighten dependencies

* Thu Jul 17 2014 Paul Howarth <paul@city-fan.org> - 7.37.1-1.1.cf
- use POSIX threads and NSS for EL-7 build

* Wed Jul 16 2014 Paul Howarth <paul@city-fan.org> - 7.37.1-1.0.cf
- update to 7.37.1
  - bits.close: introduce connection close tracking
  - darwinssl: add support for --cacert
  - polarssl: add ALPN support
  - docs: added new option man pages
  - build: fixed incorrect reference to curl_setup.h in Visual Studio files
  - build: use $(TargetDir) and $(TargetName) macros for .pdb and .lib output
  - curl.1: clarify that -u can't specify a user with colon
  - openssl: fix uninitialized variable use in NPN callback
  - curl_easy_reset: reset the URL
  - curl_version_info.3: returns a pointer to a static struct
  - url-parser: only use if_nametoindex if detected by configure
  - select: with winsock, avoid passing unsupported arguments to select()
  - gnutls: don't use deprecated type names any more
  - gnutls: allow building with nghttp2 but without ALPN support
  - tests: fix portability issue with the tftpd server
  - curl_sasl_sspi: fixed corrupt hostname in DIGEST-MD5 SPN
  - curl_sasl: extended native DIGEST-MD5 cnonce to be a 32-byte hex string
  - random: use Curl_rand() for proper random data
  - Curl_ossl_init: call OPENSSL_config for initing engines
  - config-win32.h: updated for VC12
  - winbuild: don't USE_WINSSL when WITH_SSL is being used
  - getinfo: HTTP CONNECT code not reset between transfers
  - Curl_rand: use a fake entropy for debug builds when CURL_ENTROPY set
  - http2: avoid segfault when using the plain-text http2
  - conncache: move the connection counter to the cache struct
  - http2: better return code error checking
  - curlbuild: fix GCC build on SPARC systems without configure script
  - tool_metalink: support polarssl as digest provider
  - curl.h: reverse the enum/define setup for old symbols
  - curl.h: moved two really old deprecated symbols
  - curl.h: renamed CURLOPT_DEPRECATEDx to CURLOPT_OBSOLETEx
  - buildconf: do not search tools in current directory
  - OS400: make it compilable again; make RPG binding up to date
  - nss: do not abort on connection failure (failing tests 305 and 404)
  - nss: make the fallback to SSLv3 work again
  - tool: prevent valgrind from reporting possibly lost memory (nss only)
  - progress callback: skip last callback update on errors
  - nss: fix a memory leak when CURLOPT_CRLFILE is used
  - compiler warnings: potentially uninitialized variables
  - url.c: fixed memory leak on OOM
  - gnutls: ignore invalid certificate dates with VERIFYPEER disabled
  - gnutls: fix SRP support with versions of GnuTLS from 2.99.0
  - gnutls: fixed a couple of uninitialized variable references
  - gnutls: fixed compilation against versions < 2.12.0
  - build: fixed overridden compiler PDB settings in VC7 to VC12
  - ntlm_wb: fixed buffer size not being large enough for NTLMv2 sessions
  - netrc: don't abort if home dir cannot be found
  - netrc: fixed thread safety problem by using getpwuid_r if available
  - cookie: avoid mutex deadlock
  - configure: respect host tool prefix for krb5-config
  - gnutls: handle IP address in cert name check
- fix endless loop with GSSAPI proxy auth (#1118751)

* Mon Jul 14 2014 Paul Howarth <paul@city-fan.org> - 7.37.0-4.0.cf
- use %%license in %%files list where possible

* Fri Jul  4 2014 Paul Howarth <paul@city-fan.org> - 7.37.0-3.0.cf
- various SSL-related fixes (mainly crash on connection failure)

* Sat Jun  7 2014 Paul Howarth <paul@city-fan.org> - 7.37.0-2.0.cf
- rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed May 21 2014 Paul Howarth <paul@city-fan.org> - 7.37.0-1.0.cf
- update to 7.37.0
  this release includes the following changes:
  - URL parser: IPv6 zone identifiers are now supported
  - CURLOPT_PROXYHEADER: set headers for proxy-only
  - CURLOPT_HEADEROPT: added
  - curl: add --proxy-header
  - sasl: added support for DIGEST-MD5 via Windows SSPI
  - sasl: added DIGEST-MD5 qop-option validation in native challange handling
  - imap: expanded mailbox SEARCH support to use URL query strings
  - imap: extended FETCH support to include PARTIAL URL specifier
  - nss: implement non-blocking SSL handshake
  - build: reworked Visual Studio project files
  - poll: enable poll on darwin13
  - mk-ca-bundle: added -p
  - libtests: add a wait_ms() function
  this release includes the following bugfixes:
  - mkhelp: generate code for --disable-manual as well
  - hostcheck: added a system include to define struct in_addr
  - winbuild: added warnless.c to fix build
  - Makefile.vc6: added warnless.c to fix build
  - smtp: fixed login denied when server doesn't support AUTH capability
  - smtp: fixed login denied with a RFC-821 based server
  - curl: stop interpreting IPv6 literals as glob patterns
  - http2: remove _DRAFT09 from the NPN_HTTP2 enum
  - http2: let openssl mention the exact protocol negotiated
  - http2+openssl: fix compiler warnings in ALPN using code
  - ftp: in passive data connect wait for happy eyeballs sockets
  - HTTP: don't send Content-Length: 0 _and_ Expect: 100-continue
  - http2: compile with current nghttp2, which supports h2-11
  - http_negotiate_sspi: fixed compilation when USE_HTTP_NEGOTIATE not defined
  - strerror: fix comment about vxworks' strerror_r buffer size
  - url: only use if_nametoindex() if IFNAMSIZ is available
  - imap: fixed untagged response detection when no data after command
  - various: fix possible dereference of null pointer
  - various: fix use of uninitialized variable
  - various: fix use of non-null terminated strings
  - telnet.c: check sscanf results before passing them to snprintf
  - parsedate.c: check sscanf result before passing it to strlen
  - sockfilt.c: free memory in case of memory allocation errors
  - sockfilt.c: ignore non-key-events and continue waiting for input
  - sockfilt.c: properly handle disk files, pipes and character input
  - sockfilt.c: fixed getting stuck waiting for MinGW stdin pipe
  - sockfilt.c: clean up threaded approach and add documentation
  - configure: use the nghttp2 path correctly with pkg-config
  - curl_global_init_mem: bump initialized even if already initialized
  - gtls: fix NULL pointer dereference
  - cyassl: use error-ssl.h when available
  - handler: make 'protocol' always specified as a single bit
  - INFILESIZE: fields in UserDefined must not be changed run-time
  - openssl: biomem->data is not zero terminated
  - config-win32.h: fixed HAVE_LONGLONG for Visual Studio .NET 2003 and up
  - curl_ntlm_core: fixed use of long long for VC6 and VC7
  - SNI: strip off a single trailing dot from host name
  - curl: bail on cookie use when built with disabled cookies
  - curl_easy_setopt.3: added the proto for CURLOPT_SSH_KNOWNHOSTS
  - curl_multi_cleanup: ignore SIGPIPE better
  - schannel: don't use the connect-timeout during send
  - mprintf: allow %%.s with data not being zero terminated
  - tool_help: fixed missing --login-options option
  - configure: don't set LD_LIBRARY_PATH when cross-compiling
  - http: auth failure on duplicated 'WWW-Authenticate: Negotiate' header
  - cacertinmem: fix memory leak
  - lib1506: make sure the transfers are not within the same ms
  - Makefile.b32: fixed for vtls changes
  - sasl: fixed missing qop in the client's challenge-response message
  - openssl: unbreak PKCS12 support
  - darwinssl: fix potential crash with a P12 file
  - timers: fix timer regression involving redirects / reconnects
  - CURLINFO_SSL_VERIFYRESULT: made more reliable
  - HTTP: fixed connection re-use
  - configure: add SPNEGO to supported features
  - configure: add GSS-API to supported features
  - ALPN: fix typo in http/1.1 identifier
  - http2: make connection re-use work

* Sat May 10 2014 Paul Howarth <paul@city-fan.org> - 7.36.0-4.0.cf
- fix auth failure on duplicated 'WWW-Authenticate: Negotiate' header
  (#1093348)

* Fri Apr 25 2014 Paul Howarth <paul@city-fan.org> - 7.36.0-3.0.cf
- nss: implement non-blocking SSL handshake

* Thu Mar 27 2014 Paul Howarth <paul@city-fan.org> - 7.36.0-2.0.cf
- extend URL parser to support IPv6 zone identifiers (#680996)

* Thu Mar 27 2014 Paul Howarth <paul@city-fan.org> - 7.36.0-1.1.cf
- adapt tests 815 and 816 such that they work with the fix for CVE-2014-0138

* Wed Mar 26 2014 Paul Howarth <paul@city-fan.org> 7.36.0-1.0.cf
- update to 7.36.0
  this release includes the following security advisories:
  - wrong re-use of connections (CVE-2014-0138)
  - IP address wildcard certificate validation (CVE-2014-0139)
  - not verifying certs for TLS to IP address / Darwinssl (CVE-2014-1263)
  - not verifying certs for TLS to IP address / Winssl (CVE-2014-2522)
  this release includes the following changes:
  - ntlm: added support for NTLMv2
  - tool: added support for URL specific options
  - openssl: add ALPN support
  - gtls: add ALPN support
  - nss: add ALPN and NPN support
  - added CURLOPT_EXPECT_100_TIMEOUT_MS
  - tool: add --no-alpn and --no-npn
  - added CURLOPT_SSL_ENABLE_NPN and CURLOPT_SSL_ENABLE_ALPN
  - winssl: enable TLSv1.1 and TLSv1.2 by default
  - winssl: TLSv1.2 disables certificate signatures using MD5 hash
  - winssl: enable hostname verification of IP address using SAN or CN
  - darwinssl: don't omit CN verification when an IP address is used
  - http2: build with current nghttp2 version
  - polarssl: dropped support for PolarSSL < 1.3.0
  - openssl: info message with SSL version used
  this release includes the following bugfixes:
  - nss: allow to use ECC ciphers if NSS implements them
  - netrc: fixed a memory leak in an OOM condition
  - ftp: fixed a memory leak on wildcard error path
  - pipeline: fixed a NULL pointer dereference on OOM
  - nss: prefer highest available TLS version
  - 100-continue: fix timeout condition
  - ssh: fixed a NULL pointer dereference on OOM condition
  - formpost: use semicolon in multipart/mixed
  - --help: add missing --tlsv1.x options
  - formdata: fixed memory leak on OOM condition
  - ConnectionExists: reusing possible HTTP+NTLM connections better
  - mingw32: fix compilation
  - chunked decoder: track overflows correctly
  - curl_easy_setopt.3: add CURL_HTTP_VERSION_2_0
  - dict: fix memory leak in OOM exit path
  - valgrind: added suppression on optimized code
  - curl: output protocol headers using binary mode
  - tool: added URL index to password prompt for multiple operations
  - ConnectionExists: re-use non-NTLM connections better
  - axtls: call ssl_read repeatedly
  - multi: make MAXCONNECTS default 4 x number of easy handles function
  - configure: fix the --disable-crypto-auth option
  - multi: ignore SIGPIPE internally
  - curl.1: update the description of --tlsv1
  - SFTP: skip reading the dir when NOBODY=1
  - easy: fixed a memory leak on OOM condition
  - tool: fixed incorrect return code when setting HTTP request fails
  - configure: tiny fix to honor POSIX
  - tool: do not output libcurl source for the information only parameters
  - Rework Open Watcom make files to use standard Wmake features
  - x509asn: moved out Curl_verifyhost from NSS builds
  - configure: call it GSS-API
  - hostcheck: Curl_cert_hostcheck is not used by NSS builds
  - multi_runsingle: move timestamp into INIT
  - remote_port: allow connect to port 0
  - parse_remote_port: error out on illegal port numbers better
  - ssh: pass errors from libssh2_sftp_read up the stack
  - docs: remove documentation on setting up krb4 support
  - polarssl: build fixes to work with PolarSSL 1.3.x
  - polarssl: fix possible handshake timeout issue in multi
  - nss: allow to enable/disable cipher-suites better
  - ssh: prevent a logic error that could result in an infinite loop
  - http2: free resources on disconnect
  - polarssl: avoid extra newlines in debug messages
  - rtsp: parse "Session:" header properly
  - trynextip: don't store 'ai' on failed connects
  - Curl_cert_hostcheck: strip trailing dots in host name and wildcard
- update patches as needed
- drop support for old distributions prior to FC-5
  - drop %%defattr, redundant since rpm 4.4
  - unconditionally build with metalink support
  - certs always live under /etc/pki
- skip IMAP tests 815 and 816 for now, which are failing in this release

* Mon Mar 17 2014 Paul Howarth <paul@city-fan.org> - 7.35.0-5.0.cf
- add perl build requirements for the test suite

* Wed Mar  5 2014 Paul Howarth <paul@city-fan.org> - 7.35.0-3.0.cf
- avoid spurious failure of test1086 on s390(x) koji builders (#1072273)

* Tue Feb 25 2014 Paul Howarth <paul@city-fan.org> - 7.35.0-2.0.cf
- refresh expired cookie in test172 from upstream test-suite (#1068967)

* Wed Jan 29 2014 Paul Howarth <paul@city-fan.org> - 7.35.0-1.0.cf
- update to 7.35.0:
  - imap/pop3/smtp: added support for SASL authentication downgrades
  - imap/pop3/smtp: extended the login options to support multiple auth mechs
  - TheArtOfHttpScripting: major update, converted layout and more
  - mprintf: added support for I, I32 and I64 size specifiers
  - makefile: added support for VC7, VC11 and VC12
  - SECURITY ADVISORY: re-use of wrong HTTP NTLM connection (CVE-2014-0015)
  - curl_easy_setopt: fixed OAuth 2.0 Bearer option name
  - pop3: fixed APOP being determined by CAPA response rather than by timestamp
  - Curl_pp_readresp: zero terminate line
  - FILE: don't wait due to CURLOPT_MAX_RECV_SPEED_LARGE
  - docs: mention CURLOPT_MAX_RECV/SEND_SPEED_LARGE don't work for FILE://
  - pop3: fixed auth preference not being honored when CAPA not supported
  - imap: fixed auth preference not being honored when CAPABILITY not supported
  - threaded resolver: use pthread_t * for curl_thread_t
  - FILE: we don't support paused transfers using this protocol
  - connect: try all addresses in first connection attempt
  - curl_easy_setopt.3: added SMTP information to CURLOPT_INFILESIZE_LARGE
  - OpenSSL: fix forcing SSLv3 connections
  - openssl: allow explicit sslv2 selection
  - FTP parselist: fix "total" parser
  - conncache: fix possible dereference of null pointer
  - multi.c: fix possible dereference of null pointer
  - mk-ca-bundle: introduces -d and warns about using this script
  - ConnectionExists: fix NTLM check for new connection
  - trynextip: fix build for non-IPV6 capable systems
  - Curl_updateconninfo: don't do anything for UDP "connections"
  - darwinssl: un-break Leopard build after PKCS#12 change
  - threaded-resolver: never use NULL hints with getaddrinf
  - multi_socket: remind app if timeout didn't run
  - OpenSSL: deselect weak ciphers by default
  - error message: sensible message on timeout when transfer size unknown
  - curl_easy_setopt.3: mention how to unset CURLOPT_INFILESIZE*
  - win32: fixed use of deprecated function 'GetVersionInfoEx' for VC12
  - configure: fix gssapi linking on HP-UX
  - chunked-parser: abort on overflows, allow 64 bit chunks
  - chunked parsing: relax the CR strictness
  - cookie: max-age fixes
  - progress bar: always update when at 100%%
  - progress bar: increase update frequency to 10Hz
  - tool: fixed incorrect return code if command line parser runs out of memory
  - tool: fixed incorrect return code if password prompting runs out of memory
  - HTTP POST: omit Content-Length if data size is unknown
  - GnuTLS: disable insecure ciphers
  - GnuTLS: honor --slv2 and the --tlsv1[.N] switches
  - multi: fixed a memory leak on OOM condition
  - netrc: fixed a memory and file descriptor leak on OOM
  - getpass: fix password parsing from console
  - TFTP: fix crash on time-out
  - hostip: don't remove DNS entries that are in use
  - tests: lots of tests fixed to pass the OOM torture tests

* Tue Jan 21 2014 Paul Howarth <paul@city-fan.org> - 7.34.0-1.1.cf
- add a couple of fixes from upstream for forced SSLv2 and SSLv3 support

* Tue Dec 17 2013 Paul Howarth <paul@city-fan.org> - 7.34.0-1.0.cf
- update to 7.34.0:
  - gtls: respect *VERIFYHOST independently of *VERIFYPEER (CVE-2013-6422)
  - SSL: protocol version can be specified more precisely
  - imap/pop3/smtp: added graceful cancellation of SASL authentication
  - add "Happy Eyeballs" for IPv4/IPv6 dual connect attempts
  - base64: added validation of base64 input strings when decoding
  - curl_easy_setopt: added the ability to set the login options separately
  - smtp: added support for additional SMTP commands
  - curl_easy_getinfo: added CURLINFO_TLS_SESSION for accessing TLS internals
  - nss: allow to use TLS > 1.0 if built against recent NSS
  - SECURITY: added this document to describe our security processes
  - parseconfig: warn if unquoted white spaces are detected
  - darwinssl: un-break iOS build after PKCS#12 feature added
  - tool: use XFERFUNCTION to save some casts
  - usercertinmem: fix memory leaks
  - ssh: handle successful SSH_USERAUTH_NONE
  - NSS: acknowledge the --no-sessionid/CURLOPT_SSL_SESSIONID_CACHE option
  - test906: fixed failing test on some platforms
  - sasl: initialize NSS before using NTLM crypto
  - sasl: fixed memory leak in OAUTH2 message creation
  - imap/pop3/smtp: fixed QUIT / LOGOUT being sent when SSL connect fails
  - cmake: unbreak for non-Windows platforms
  - ssh: initialize per-handle data in ssh_connect()
  - glob: fix broken URLs
  - configure: check for long long when building with cyassl
  - CURLOPT_RESOLVE: mention they don't time-out
  - docs/examples/httpput.c: fix build for MSVC
  - FTP: make the data connection work when going through proxy
  - NSS: support for CERTINFO feature
  - curl_multi_wait: accept 0 from multi_timeout() as valid timeout
  - glob_range: pass the closing bracket for a-z ranges
  - tool_help: updated --list-only description to include POP3
  - Curl_ssl_push_certinfo_len: don't %%.*s non-zero-terminated string
  - cmake: fix Windows build with IPv6 support
  - ares: fixed compilation under Visual Studio 2012
  - curl_easy_setopt.3: clarify CURLOPT_SSL_VERIFYHOST documentation
  - curl.1: mention that -O does no URL decoding
  - darwinssl: PKCS#12 import feature now requires Lion or later
  - darwinssl: check for SSLSetSessionOption() presence when toggling BEAST
  - configure: fix test with -Werror=implicit-function-declaration
  - sigpipe: factor out sigpipe_reset from easy.c
  - curl_multi_cleanup: ignore SIGPIPE
  - globbing: curl glob counter mismatch with {} list use
  - parseconfig: dash options can't specified with colon or equals
  - digest: fix CURLAUTH_DIGEST_IE
  - curl.h: <sys/select.h> for OpenBSD
  - darwinssl: Fix #if 10.6.0 for SecKeychainSearch
  - TFTP: fix return codes for connect timeout
  - login options: remove the ;[options] support from CURLOPT_USERPWD
  - imap: fixed incorrect fallback to clear text authentication
  - parsedate: avoid integer overflow
  - curl.1: document -J doesn't %%-decode
  - multi: add timer inaccuracy margin to timeout/connecttimeout
- switch to openssl backend for Fedora 10 to 15 as NSS 3.14 is now required
  (http://curl.haxx.se/mail/lib-2013-12/0000.html)

* Mon Dec  2 2013 Paul Howarth <paul@city-fan.org> - 7.33.0-2.0.cf
- allow to use TLS > 1.0 if built against recent NSS

* Wed Oct 30 2013 Paul Howarth <paul@city-fan.org> - 7.33.0-1.3.cf
- run tests with -n to explicitly disable valgrind, which can be problematic
  on old distributions

* Tue Oct 22 2013 Paul Howarth <paul@city-fan.org> - 7.33.0-1.2.cf
- fix missing initialization in SSH code causing test 619 to fail

* Fri Oct 18 2013 Paul Howarth <paul@city-fan.org> - 7.33.0-1.1.cf
- fix missing initialization in NTLM code causing test 906 to fail

* Tue Oct 15 2013 Paul Howarth <paul@city-fan.org> - 7.33.0-1.0.cf
- update to 7.33.0:
  - test code for testing the event based API
  - CURLM_ADDED_ALREADY: new error code
  - test TFTP server: support "writedelay" within <servercmd>
  - krb4 support has been removed
  - imap/pop3/smtp: added basic SASL XOAUTH2 support
  - darwinssl: add support for PKCS#12 files for client authentication
  - darwinssl: enable BEAST workaround on iOS 7 and later
  - pass password to OpenSSL engine by user interface
  - c-ares: add support for various DNS binding options
  - cookies: add expiration
  - curl: added --oauth2-bearer option
  - nss: make sure that NSS is initialized
  - curl: make --no-[option] work properly for several options
  - FTP: with socket_action send better socket updates in active mode
  - curl: fix the --sasl-ir in the --help output
  - tests 2032, 2033: don't hardcode port in expected output
  - urlglob: better detect unclosed braces, empty lists and overflows
  - urlglob: error out on range overflow
  - imap: fixed response check for SEARCH, EXPUNGE, LSUB, UID and NOOP commands
  - handle arbitrary-length username and password
  - TFTP: make the CURLOPT_LOW_SPEED* options work
  - curl.h: name space pollution by "enum type"
  - multi: move on from STATE_DONE faster
  - FTP: 60 secs delay if aborted in the CURLOPT_HEADERFUNCTION callback
  - multi_socket: improved 100-continue timeout handling
  - curl_multi_remove_handle: allow multiple removes
  - FTP: fix getsock during DO_MORE state
  - -x: rephrased the --proxy section somewhat
  - acinclude: fix --without-ca-path when cross-compiling
  - LDAP: fix bad free() when URL parsing failed
  - --data: mention CRLF treatment when reading from file
  - curl_easy_pause: suggest one way to unpause
  - imap: fixed calculation of transfer when partial FETCH received
  - pingpong: check SSL library buffers for already read data
  - imap/pop3/smtp: speed up SSL connection initialization
  - libcurl.3: for multi interface connections are held in the multi handle
  - curl_easy_setopt.3: mention RTMP URL quirks
  - curl.1: detail how short/long options work
  - curl.1: added information about optional login options to --user option
  - curl: added clarification to the --mail options in the --help output
  - curl_easy_setopt.3: clarify that TIMEOUT and TIMEOUT_MS set the same value
  - openssl: use correct port number in error message
  - darwinssl: block TLS_RSA_WITH_NULL_SHA256 cipher
  - OpenSSL: acknowledge CURLOPT_SSL_VERIFYHOST without VERIFYPEER
  - xattr: add support for FreeBSD xattr API
  - win32: fix Visual Studio 2010 build with WINVER >= 0x600
  - configure: use icc options without space
  - test1112: Increase the timeout from 7s to 16s
  - SCP: upload speed on a fast connection limited to 16384 B/s
  - curl_setup_once: fix errno access for lwip on Windows
  - HTTP: output http response 304 when modified time is too old
- adjust multilib, debug and threaded DNS patches
- add new patch for failing test 906

* Fri Oct 11 2013 Paul Howarth <paul@city-fan.org> - 7.32.0-3.0.cf
- do not limit the speed of SCP upload on a fast connection
  (http://thread.gmane.org/gmane.comp.web.curl.library/40551/focus=40561)

* Mon Sep  9 2013 Paul Howarth <paul@city-fan.org> - 7.32.0-2.0.cf
- avoid delay if FTP is aborted in CURLOPT_HEADERFUNCTION callback (#1005686)

* Mon Aug 12 2013 Paul Howarth <paul@city-fan.org> - 7.32.0-1.1.cf
- make sure that NSS is initialized prior to calling PK11_GenerateRandom()

* Mon Aug 12 2013 Paul Howarth <paul@city-fan.org> - 7.32.0-1.0.cf
- update to 7.32.0:
  - curl: allow timeouts to accept decimal values
  - OS400: add slist and certinfo EBCDIC support
  - OS400: new SSL backend GSKit
  - CURLOPT_XFERINFOFUNCTION: introducing a new progress callback
  - LIBCURL-STRUCTS: new document
  - dotdot: introducing dot file path cleanup
  - docs: fix typo in curl_easy_getinfo manpage
  - test1230: avoid using hard-wired port number
  - test1396: invoke the correct test tool
  - SIGPIPE: ignored while inside the library
  - darwinssl: fix crash that started happening in Lion
  - OpenSSL: check for read errors, don't assume
  - c-ares: improve error message on failed resolve
  - printf: make sure %%x are treated unsigned
  - formpost: better random boundaries
  - url: restore the functionality of 'curl -u :'
  - curl.1: fix typo in --xattr description
  - digest: improve nonce generation
  - configure: automake 1.14 compatibility tweak
  - curl.1: document the --post303 option in the man page
  - curl.1: document the --sasl-ir option in the man page
  - setup-vms.h: sk_pop symbol tweak
  - tool_paramhlp: try harder to catch negatives
  - cmake: fix for MSVC2010 project generation
  - asyn-ares: don't blank ares servers if none configured
  - curl_multi_wait: set revents for extra fds
  - reinstate "WIN32 MemoryTracking: track wcsdup() _wcsdup() and _tcsdup()
  - ftp_do_more: consider DO_MORE complete when server connects back
  - curl_easy_perform: gradually increase the delay time
  - curl: fix symbolic names for CURLUSESSL_* enum in --libcurl output
  - curl: fix upload of a zip file in OpenVMS
  - build: fix linking on Solaris 10
  - curl_formadd: CURLFORM_FILECONTENT wrongly rejected some option combos
  - curl_formadd: fix file upload on VMS
  - curl_easy_pause: on unpause, trigger mulit-socket handling
  - md5 and metalink: use better build macros on Apple operating systems
  - darwinssl: fix build error in crypto authentication under Snow Leopard
  - curl: make --progress-bar update the line less frequently
  - configure: don't error out on variable confusions (CFLAGS, LDFLAGS etc.)
  - mk-ca-bundle: skip more untrusted certificates
  - formadd: wrong pointer for file name when CURLFORM_BUFFERPTR used
  - FTP: when EPSV gets a 229 but fails to connect, retry with PASV
  - mk-ca-bundle.1: don't install on make install
  - VMS: lots of updates and fixes of the build procedure
  - global dns cache: didn't work (regression)
  - global dns cache: fix memory leak
- adjust multilib and UTF8 patches
- drop upstreamed patches

* Sat Aug  3 2013 Paul Howarth <paul@city-fan.org> - 7.31.0-5.0.cf
- rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue Jul  9 2013 Paul Howarth <paul@city-fan.org> - 7.31.0-4.0.cf
- mention all options listed in 'curl --help' in curl.1 man page

* Mon Jul  1 2013 Paul Howarth <paul@city-fan.org> - 7.31.0-3.0.cf
- restore the functionality of 'curl -u :'

* Wed Jun 26 2013 Paul Howarth <paul@city-fan.org> - 7.31.0-2.0.cf
- build the curl tool with metalink support

* Mon Jun 24 2013 Paul Howarth <paul@city-fan.org> - 7.31.0-1.1.cf
  - test1230: avoid using hard-wired port number

* Sat Jun 22 2013 Paul Howarth <paul@city-fan.org> - 7.31.0-1.0.cf
- update to 7.31.0:
  - SECURITY VULNERABILITY: curl_easy_unescape() may parse data beyond the end
    of the input buffer (CVE-2013-2174)
  - darwinssl: add TLS session resumption
  - darwinssl: add TLS crypto authentication
  - imap/pop3/smtp: added support for ;auth=<mech> in the URL
  - imap/pop3/smtp: added support for ;auth=<mech> to CURLOPT_USERPWD
  - usercertinmem.c: add example showing user cert in memory
  - url: added smtp and pop3 hostnames to the protocol detection list
  - imap/pop3/smtp: added support for enabling the SASL initial response
  - curl -E: allow to use ':' in certificate nicknames
  - FTP: access files in root dir correctly
  - configure: try pthread_create without -lpthread
  - FTP: handle a 230 welcome response
  - curl-config: don't output static libs when they are disabled
  - CURL_CHECK_CA_BUNDLE: don't check for paths when cross-compiling
  - Various documentation updates
  - getinfo.c: reset timecond when clearing session-info variables
  - FILE: prevent an artificial timeout event due to stale speed-check data
  - ftp_state_pasv_resp: connect through proxy also when set by env
  - sshserver: disable StrictHostKeyChecking
  - ftpserver: fixed imap logout confirmation data
  - curl_easy_init: use less mallocs
  - smtp: fixed unknown percentage complete in progress bar
  - smtp: fixed sending of double CRLF caused by first in EOB
  - bindlocal: move brace out of #ifdef
  - winssl: fixed invalid memory access during SSL shutdown
  - OS X framework: fix invalid symbolic link
  - OpenSSL: allow empty server certificate subject
  - axtls: prevent memleaks on SSL handshake failures
  - cookies: only consider full path matches
  - revert win32 MemoryTracking: wcsdup() _wcsdup() and _tcsdup()
  - Curl_cookie_add: handle IPv6 hosts
  - ossl_send: SSL_write() returning 0 is an error too
  - ossl_recv: SSL_read() returning 0 is an error too
  - digest auth: escape user names with \ or " in them
  - curl_formadd.3: fixed wrong "end-marker" syntax
  - libcurl-tutorial.3: fix incorrect backslash
  - curl_multi_wait: reduce timeout if the multi handle wants to
  - tests/Makefile: typo in the perlcheck target
  - axtls: honor disabled VERIFYHOST
  - OpenSSL: avoid double free in the PKCS12 certificate code
  - multi_socket: reduce timeout inaccuracy margin
  - digest: support auth-int for empty entity body
  - axtls: now done non-blocking
  - lib1900: use tutil_tvnow instead of gettimeofday
  - curl_easy_perform: avoid busy-looping
  - CURLOPT_COOKIELIST: take cookie share lock
  - multi_socket: react on socket close immediately
- adjust multilib patch
- drop upstreamed patches

* Fri Apr 26 2013 Paul Howarth <paul@city-fan.org> - 7.30.0-2.0.cf
- limit the excessive use of sed in %%prep
- prevent an artificial timeout event due to stale speed-check data (#906031)

* Sat Apr 13 2013 Paul Howarth <paul@city-fan.org> - 7.30.0-1.1.cf
- reinstate test port adjustment fixes

* Fri Apr 12 2013 Paul Howarth <paul@city-fan.org> - 7.30.0-1.0.cf
- update to 7.30.0:
  - SECURITY ADVISORY: cookie tailmatching to avoid cross-domain leakage
    (CVE-2013-1944)
  - imap: Changed response tag generation to be completely unique
  - imap: Added support for SASL-IR extension
  - imap: Added support for the list command
  - imap: Added support for the append command
  - imap: Added custom request parsing
  - imap: Added support to the fetch command for UID and SECTION properties
  - imap: Added parsing and verification of the UIDVALIDITY mailbox attribute
  - darwinssl: Make certificate errors less techy
  - imap/pop3/smtp: Added support for the STARTTLS capability
  - checksrc: ban use of sprintf, vsprintf, strcat, strncat and gets
  - curl_global_init() now accepts the CURL_GLOBAL_ACK_EINTR flag
  - Added CURLMOPT_MAX_HOST_CONNECTIONS, CURLMOPT_MAX_TOTAL_CONNECTIONS for
    new multi interface connection handling
  - Added CURLMOPT_MAX_PIPELINE_LENGTH, CURLMOPT_CONTENT_LENGTH_PENALTY_SIZE,
    CURLMOPT_CHUNK_LENGTH_PENALTY_SIZE, CURLMOPT_PIPELINING_SITE_BL and
    CURLMOPT_PIPELINING_SERVER_BL for new pipelining control
  - darwinssl: Fix build under Leopard
  - DONE: consider callback-aborted transfers premature
  - ntlm: Fixed memory leaks
  - smtp: Fixed an issue when processing EHLO failure responses
  - pop3: Fixed incorrect return value from pop3_endofresp()
  - pop3: Fixed SASL authentication capability detection
  - pop3: Fixed blocking SSL connect when connecting via POP3S
  - imap: Fixed memory leak when performing multiple selects
  - nss: fix misplaced code enabling non-blocking socket mode
  - AddFormData: prevent only directories from being posted
  - darwinssl: fix infinite loop if server disconnected abruptly
  - metalink: fix improbable crash parsing metalink filename
  - show proper host name on failed resolve
  - MacOSX-Framework: Make script work in Xcode 4.0 and later
  - strlcat: remove function
  - darwinssl: Fix send glitchiness with data > 32 or so KB
  - polarssl: better 1.1.x and 1.2.x support
  - various documentation improvements
  - multi: NULL pointer reference when closing an unused multi handle
  - SOCKS: fix socks proxy when noproxy matched
  - install-sh: updated to support multiple source files as arguments
  - PolarSSL: added human readable error strings
  - resolver_error: remove wrong error message output
  - docs: updates HTML index and general improvements
  - curlbuild.h.dist: enhance non-configure GCC ABI detection logic
  - sasl: Fixed null pointer reference when decoding empty digest challenge
  - easy: do not ignore poll() failures other than EINTR
  - darwinssl: disable ECC ciphers under Mountain Lion by default
  - CONNECT: count received headers
  - build: fixes for VMS
  - CONNECT: clear 'rewindaftersend' on success
  - HTTP proxy: insert slash in URL if missing
  - hiperfifo: updated to use current libevent API
  - getinmemory.c: abort the transfer nicely if not enough memory
  - improved win32 memorytracking
  - corrected proxy header response headers count
  - FTP quote operations on re-used connection
  - tcpkeepalive on win32
  - tcpkeepalive on Mac OS X
  - easy: acknowledge the CURLOPT_MAXCONNECTS option properly
  - easy interface: restore default MAXCONNECTS to 5
  - win32: don't set SO_SNDBUF for windows vista or later versions
  - HTTP: made cookie sort function more deterministic
  - winssl: Fixed memory leak if connection was not successful
  - FTP: wait on both connections during active STOR state
  - connect: treat a failed local bind of an interface as a non-fatal error
  - darwinssl: disable insecure ciphers by default
  - FTP: handle "rubbish" in front of directory name in 257 responses
  - mk-ca-bundle: Fixed lost OpenSSL output with "-t"
- remove upstreamed patches
- temporarily drop the switching of ports for tests as it causes test suite
  failures
- add patch to fix linking of tests 1900 and 2033

* Tue Mar 12 2013 Paul Howarth <paul@city-fan.org> - 7.29.0-4.0.cf
- do not ignore poll() failures other than EINTR (#919127)
- curl_global_init() now accepts the CURL_GLOBAL_ACK_EINTR flag (#919127)

* Wed Mar  6 2013 Paul Howarth <paul@city-fan.org> - 7.29.0-3.0.cf
- switch SSL socket into non-blocking mode after handshake
- drop the hide_selinux.c hack no longer needed in %%check

* Fri Feb 22 2013 Paul Howarth <paul@city-fan.org> - 7.29.0-2.0.cf
- fix a SIGSEGV when closing an unused multi handle (#914411)

* Wed Feb  6 2013 Paul Howarth <paul@city-fan.org> - 7.29.0-1.0.cf
- update to 7.29.0:
  - fix POP3/IMAP/SMTP SASL buffer overflow vulnerability (CVE-2013-0249)
  - test: offer "automake" output and check for perl better
  - always-multi: always use non-blocking internals
  - imap: added support for sasl digest-md5 authentication
  - imap: added support for sasl cram-md5 authentication
  - imap: added support for sasl ntlm authentication
  - imap: added support for sasl login authentication
  - imap: added support for sasl plain text authentication
  - imap: added support for login disabled server capability
  - mk-ca-bundle: add -f, support passing to stdout and more
  - writeout: -w now supports remote_ip/port and local_ip/port
  - nss: prevent NSS from crashing on client auth hook failure
  - darwinssl: fixed inability to disable peer verification on Snow Leopard and
    Lion
  - curl_multi_remove_handle: fix memory leak triggered with CURLOPT_RESOLVE
  - SCP: relative path didn't work as documented
  - setup_once.h: HP-UX <sys/socket.h> issue workaround
  - configure: fix cross pkg-config detection
  - runtests: do not add undefined values to @INC
  - build: fix compilation with CURL_DISABLE_CRYPTO_AUTH flag
  - multi: fix re-sending request on early connection close
  - HTTP: remove stray CRLF in chunk-encoded content-free request bodies
  - build: fix AIX compilation and usage of events/revents
  - VC Makefiles: add missing hostcheck
  - nss: clear session cache if a client certificate from file is used
  - nss: fix error messages for CURLE_SSL_{CACERT,CRL}_BADFILE
  - fix HTTP CONNECT tunnel establishment upon delayed response
  - --libcurl: fix for non-zero default options
  - FTP: reject illegal port numbers in EPSV 229 responses
  - build: use per-target '_CPPFLAGS' for those currently using default
  - configure: fix automake 1.13 compatibility
  - curl: ignore SIGPIPE
  - pop3: added support for non-blocking SSL upgrade
  - pop3: fixed default authentication detection
  - imap: fixed usernames and passwords that contain escape characters
  - packages/DOS/common.dj: remove COFF debug info generation
  - imap/pop3/smtp: fixed failure detection during TLS upgrade
  - pop3: fixed no known authentication mechanism when fallback is required
  - formadd: reject trying to read a directory where a file is expected
  - formpost: support quotes, commas and semicolon in file names
  - docs: update the comments about loading CA certs with NSS
  - docs: fix typos in man pages
  - darwinssl: fix bug where packets were sometimes transmitted twice
  - winbuild: include version info for .dll .exe
  - schannel: Removed extended error connection setup flag
  - VMS: fix and generate the VMS build config
- drop upstreamed patches and update others as needed

* Tue Jan 15 2013 Paul Howarth <paul@city-fan.org> - 7.28.1-3.0.cf
- prevent NSS from crashing on client auth hook failure
- clear session cache if a client cert from file is used
- fix error messages for CURLE_SSL_{CACERT,CRL}_BADFILE

* Tue Nov 20 2012 Paul Howarth <paul@city-fan.org> - 7.28.1-1.0.cf
- update to 7.28.1:
  - metalink/md5: use CommonCrypto on Apple operating systems
  - href_extractor: new example code extracting href elements
  - NSS can be used for metalink hashing
  - fix broken libmetalink-aware OpenSSL build
  - gnutls: fix the error is fatal logic
  - darwinssl: un-broke iOS build, fix error on server disconnect
  - asyn-ares: restore functionality with c-ares < 1.6.1
  - tlsauthtype: deal with the string case insensitively
  - fixed MSVC libssh2 static build
  - evhiperfifo: fix the pointer passed to WRITEDATA
  - BUGS: fix the bug tracker URL
  - winbuild: use machine type of development environment
  - FTP: prevent the multi interface from blocking
  - uniformly use AM_CPPFLAGS, avoid deprecated INCLUDES
  - httpcustomheader.c: free the headers after use
  - fix >2000 bytes POST over NTLM-using proxy
  - redirects to URLs with fragments
  - don't send '#' fragments when using proxy
  - OpenSSL: show full issuer string
  - fix HTTP auth regression
  - CURLOPT_SSL_VERIFYHOST: stop supporting the 1 value
  - ftp: EPSV-disable fix over SOCKS
  - Digest: Add microseconds into nounce calculation
  - SCP/SFTP: improve error code used for send failures
  - SSL: several SSL-backend related fixes
  - removed the notorious "additional stuff not fine" debug output
  - OpenSSL: disable SSL/TLS compression - avoid the "CRIME" attack
  - FILE: make upload-writes unbuffered
  - custom memory callbacks failure with HTTP proxy (and more)
  - TFTP: handle resends
  - autoconf: don't force-disable compiler debug option
  - winbuild: fix PDB file output
  - test2032: spurious failure caused by premature termination
  - memory leak: CURLOPT_RESOLVE with multi interface
- re-enable test2032
- update UTF8 and debug patches
- fix bogus dates in spec changelog

* Wed Oct 31 2012 Paul Howarth <paul@city-fan.org> - 7.28.0-1.0.cf
- update to 7.28.0:
  - SSH: added agent based authentication
  - ftp: active conn, allow application to set sockopt after accept() call
    with CURLSOCKTYPE_ACCEPT
  - multi: add curl_multi_wait()
  - metalink: added support for Microsoft Windows CryptoAPI
  - md5: added support for Microsoft Windows CryptoAPI
  - parse_proxy: treat "socks://x" as a socks4 proxy
  - socks: added support for IPv6 connections through SOCKSv5 proxy
  - WSAPoll disabled on Windows builds due to its bugs
  - fix segfault on request retries
  - curl-config: parentheses fix
  - VC build: add define for openssl
  - globbing: fix segfault when >9 globs were used
  - fixed a few clang-analyzer warnings
  - metalink: change code order to build with gnutls-nettle
  - gtls: fix build failure by including nettle-specific headers
  - change preferred HTTP auth on a handle previously used for another auth
  - file: use fdopen() to avoid race condition
  - added DWANT_IDN_PROTOTYPES define for MSVC too
  - verbose: fixed (nil) output of hostnames in re-used connections
  - metalink: un-broke the build when building --with-darwinssl
  - curl man page cleanup
  - avoid leak of local device string when reusing connection
  - Curl_socket_check: fix return code for timeout
  - nss: do not print misleading NSS error codes
  - configure: remove the --enable/disable-nonblocking options
  - darwinssl: add TLS 1.1 and 1.2 support, replace deprecated functions
  - NTLM: re-use existing connection better
  - schannel crash on multi and easy handle cleanup
  - SOCKS: truly disable it if CURL_DISABLE_PROXY is defined
  - mk-ca-bundle: detect start of trust section better
  - gnutls: do not fail on non-fatal handshake errors
  - SMTP: only send SIZE if supported
  - ftpserver: respond with a 250 to SMTP EHLO
  - ssh: do not crash if MD5 fingerprint is not provided by libssh2
  - winbuild: added support for building with SPNEGO enabled
  - metalink: fixed validation of binary files containing EOF
  - setup.h: fixed for MS VC10 build
  - cmake: use standard findxxx modules for cmake v2.8+
  - HTTP_ONLY: disable more protocols
  - Curl_reconnect_request: clear pointer on failure
  - https.c example: remember to call curl_global_init()
  - metalink: Filter resource URLs by type
  - multi interface: CURLOPT_LOW_SPEED_* fix during rate limitation
  - curl_schannel: Removed buffer limit and optimized buffer strategy
- drop patches now included in upstream release
- update UTF8 and debug patches
- disable tests 1112 and 2032 for now

* Mon Oct  1 2012 Paul Howarth <paul@city-fan.org> - 7.27.0-3.1.cf
- do not crash if MD5 fingerprint is not provided by libssh2

* Mon Aug  6 2012 Paul Howarth <paul@city-fan.org> - 7.27.0-3.0.cf
- use the upstream facility to disable problematic tests

* Wed Aug  1 2012 Paul Howarth <paul@city-fan.org> - 7.27.0-2.0.cf
- eliminate unnecessary inotify events on upload via file protocol (#844385)

* Sat Jul 28 2012 Paul Howarth <paul@city-fan.org> - 7.27.0-1.0.cf
- update to 7.27.0:
  - nss: use human-readable error messages provided by NSS
  - added --metalink for metalink download support
  - pop3: added support for sasl plain text authentication
  - pop3: added support for sasl login authentication
  - pop3: added support for sasl ntlm authentication
  - pop3: added support for sasl cram-md5 authentication
  - pop3: added support for sasl digest-md5 authentication
  - pop3: added support for apop authentication
  - added support for Schannel (Native Windows) SSL/TLS encryption
  - added support for Darwin SSL (Native Mac OS X and iOS)
  - http: print reason phrase from HTTP status line on error
  - pop3: fixed the issue of having to supply the user name for all requests
  - configure: fix LDAPS disabling related misplaced closing parenthesis
  - cmdline: made -D option work with -O and -J
  - configure: fix libcurl.pc and curl-config generation for static MingW*
    cross builds
  - ssl: fix duplicated SSL handshake with multi interface and proxy
  - winbuild: fix Makefile.vc ignoring USE_IPV6 and USE_IDN flags
  - OpenSSL: support longer certificate subject names
  - openldap: OOM fixes
  - log2changes.pl: fix the Version output
  - lib554.c: use curl_formadd() properly
  - urldata.h: fix cyassl build clash with wincrypt.h
  - cookies: changed the URL in the cookiejar headers
  - http-proxy: keep CONNECT connections alive (for NTLM)
  - NTLM SSPI: fixed to work with unicode user names and passwords
  - OOM fix in the curl tool when cloning cmdline options
  - fixed some examples to use curl_global_init() properly
  - cmdline: stricter numerical option parser
  - HTTP HEAD: don't force-close after response-headers
  - test231: fix wrong -C use
  - docs: switch to proper UTF-8 for text file encoding
  - keepalive: DragonFly uses milliseconds
  - HTTP Digest: Client's "qop" value should not be quoted
  - make distclean works again
- update patches as necessary

* Mon Jul 23 2012 Paul Howarth <paul@city-fan.org> - 7.26.0-6.0.cf
- print reason phrase from HTTP status line on error (#676596)

* Wed Jul 18 2012 Paul Howarth <paul@city-fan.org> - 7.26.0-5.0.cf
- rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sat Jun  9 2012 Paul Howarth <paul@city-fan.org> - 7.26.0-4.0.cf
- fix duplicated SSL handshake with multi interface and proxy (#788526)

* Wed May 30 2012 Paul Howarth <paul@city-fan.org> - 7.26.0-3.0.cf
- disable test 1319 on ppc64; server times out

* Mon May 28 2012 Paul Howarth <paul@city-fan.org> - 7.26.0-2.0.cf
- use human-readable error messages provided by NSS (upstream commit 72f4b534)

* Thu May 24 2012 Paul Howarth <paul@city-fan.org> - 7.26.0-1.0.cf
- update to 7.26.0:
  - nss: the minimal supported version of NSS bumped to 3.12.x
  - nss: human-readable names are now provided for NSS errors if available
  - add a manual page for mk-ca-bundle
  - added --post303 and the CURL_REDIR_POST_303 option for CURLOPT_POSTREDIR
  - smtp: add support for DIGEST-MD5 authentication
  - pop3: added support for additional pop3 commands
  - nss: libcurl now uses NSS_InitContext() to prevent collisions if available
  - URL parse: reject numerical IPv6 addresses outside brackets
  - MD5: fix OOM memory leak
  - OpenSSL cert: provide more details when cert check fails
  - HTTP: empty chunked POST ended up in two zero size chunks
  - fixed a regression when curl resolved to multiple addresses and the first
    isn't supported
  - -# progress meter: avoid superfluous updates and duplicate lines
  - headers: surround GCC attribute names with double underscores
  - PolarSSL: correct return code for CRL matches
  - PolarSSL: include version number in version string
  - PolarSSL: add support for asynchronous connect
  - mk-ca-bundle: revert the LWP usage
  - IPv6 cookie domain: get rid of the first bracket before the second
  - connect.c: return changed to CURLE_COULDNT_CONNECT when opensocket fails
  - OpenSSL: made cert hostname check conform to RFC 6125
  - HTTP: reset expected DL/UL sizes on redirects
  - CMake: fix Windows LDAP/LDAPS option handling
  - CMake: fix MS Visual Studio x64 unsigned long long literal suffix
  - configure: update detection logic of getaddrinfo() thread-safeness
  - configure: check for gethostbyname in the watt lib
  - curl-config.1: fix curl-config usage in example
  - smtp: Fixed non-escaping of dot character at beginning of line
  - MakefileBuild.vc: use the correct IDN variable
  - autoconf: improve handling of versioned symbols
  - curl.1: clarify -x usage
  - curl: shorten user-agent
  - smtp: issue with the multi-interface always sending postdata
  - compile error with GnuTLS+Nettle fixed
  - winbuild: fix IPv6 enabled build
- drop upstream patches
- re-diff other patches as necessary

* Wed Apr 25 2012 Paul Howarth <paul@city-fan.org> - 7.25.0-3.0.cf
- resync with Rawhide

* Fri Apr 13 2012 Paul Howarth <paul@city-fan.org> - 7.25.0-2.0.cf
- use NSS_InitContext() to initialize NSS if available (#738456)
- provide human-readable names for NSS errors (upstream commit a60edcc6)

* Fri Mar 23 2012 Paul Howarth <paul@city-fan.org> - 7.25.0-1.0.cf
- update to 7.25.0:
  - configure: add option disable --libcurl output
  - --ssl-allow-beast and CURLOPT_SSL_OPTIONS added
  - added CURLOPT_TCP_KEEPALIVE, CURLOPT_TCP_KEEPIDLE, CURLOPT_TCP_KEEPINTVL
  - curl: use new library-side TCP_KEEPALIVE options
  - added a new CURLOPT_MAIL_AUTH option
  - added support for --mail-auth
  - --libcurl now also works with -F and more!
  - --max-redirs: allow negative numbers as option value
  - parse_proxy: bail out on zero-length proxy names
  - configure: don't modify LD_LIBRARY_PATH for cross compiles
  - curl_easy_reset: reset the referer string
  - curl tool: don't abort glob-loop due to failures
  - CONNECT: send correct Host: with IPv6 numerical address
  - explicitly link to the nettle/gcrypt libraries
  - more resilient connection times among IP addresses
  - winbuild: fix IPV6 and IDN options
  - SMTP: fixed error when using CURLOPT_CONNECT_ONLY
  - cyassl: update to CyaSSL 2.0.x API
  - smtp: fixed an issue with the EOB checking
  - pop3: fixed drop of final CRLF in EOB checking
  - smtp: fixed an issue with writing postdata
  - smtp: added support for returning SMTP response codes
  - CONNECT: fix ipv6 address in the Request-Line
  - curl-config: only provide libraries with --libs
  - LWIP: don't consider HAVE_ERRNO_H to be winsock
  - ssh: tunnel through HTTP proxy if requested
  - cookies: strip off [brackets] from numerical ipv6 host names
  - libcurl docs: version corrections
  - cmake: list_spaces_append_once failure
  - resolve with c-ares: don't resolve IPv6 when not working
  - smtp: changed error code for EHLO and HELO responses
  - parsedate: fix a numeric overflow
- update debug, multilib and UTF8 patches
- drop support for distributions prior to FC-3:
  - don't need to handle pkgconfig ≤ 0.15 with no URL support
  - don't need workaround for RHL-9's LD_PRELOAD issues

* Tue Jan 24 2012 Paul Howarth <paul@city-fan.org> - 7.24.0-1.0.cf
- update to 7.24.0:
  - curl was vulnerable to a data injection attack for certain protocols
    (CVE-2012-0036, http://curl.haxx.se/docs/adv_20120124.html)
  - curl was vulnerable to a SSL CBC IV vulnerability when built to use OpenSSL
    (CVE-2011-3389, http://curl.haxx.se/docs/adv_20120124B.html)
  - CURLOPT_QUOTE: SFTP supports the '*'-prefix now
  - CURLOPT_DNS_SERVERS: set name servers if possible
  - add support for using nettle instead of gcrypt as gnutls backend
  - CURLOPT_INTERFACE: avoid resolving interfaces names with magic prefixes
  - added CURLOPT_ACCEPTTIMEOUT_MS
  - configure: add symbols versioning option --enable-versioned-symbols
  - SSL session share: move the age counter to the share object
  - -J -O: use -O name if no Content-Disposition header comes!
  - protocol_connect: show verbose connect and set connect time
  - query-part: ignore the URI part for given protocols
  - gnutls: only translate winsock errors for old versions
  - POP3: fix end of body detection
  - POP3: detect when LIST returns no mails
  - TELNET: improved treatment of options
  - configure: add support for pkg-config detection of libidn
  - CyaSSL 2.0+ library initialization adjustment
  - multi interface: only use non-NULL socker function pointer
  - call opensocket callback properly for active FTP
  - don't call close socket callback for sockets created with accept()
  - differentiate better between host/proxy errors
  - SSH: fix CURLOPT_SSH_HOST_PUBLIC_KEY_MD5 and --hostpubmd5
  - multi: handle timeouts on DNS servers by checking for new sockets
  - CURLOPT_DNS_SERVERS: fix return code
  - POP3: fixed escaped dot not being stripped out
  - OpenSSL: check for the SSLv2 function in configure
  - MakefileBuild: fix the static build
  - create_conn: don't switch to HTTP protocol if tunneling is enabled
  - multi interface: fix block when CONNECT_ONLY option is used
  - fix connection reuse for TLS upgraded connections
  - multiple file upload with -F and custom type
  - multi interface: active FTP connections are no longer blocking
  - Android build fix
  - timer: restore PRETRANSFER timing
  - libcurl.m4: fix quoting arguments of AC_LANG_PROGRAM
  - appconnect time fixed for non-blocking connect ssl backends
  - do not include SSL handshake into time spent waiting for 100-continue
  - handle dns cache case insensitive
  - use new host name casing for subsequent HTTP requests
  - CURLOPT_RESOLVE: avoid adding already present host names
  - SFTP mkdir: use correct permission
  - resolve: don't leak pre-populated dns entries
  - --retry: retry transfers on timeout and DNS errors
  - negotiate with SSPI backend: use the correct buffer for input
  - SFTP dir: increase buffer size counter to avoid cut off file names
  - TFTP: fix resending (again)
  - c-ares: don't include getaddrinfo-using code
  - FTP: CURLE_PARTIAL_FILE will not close the control channel
  - win32-threaded-resolver: stop using a dummy socket
  - OpenSSL: remove reference to openssl internal struct
  - OpenSSL: SSL_OP_NETSCAPE_REUSE_CIPHER_CHANGE_BUG option no longer enabled
  - OpenSSL: fix PKCS#12 certificate parsing related memory leak
  - OpenLDAP: fix LDAP connection phase memory leak
  - Telnet: use correct file descriptor for telnet upload
  - Telnet: Remove bogus optimisation of telnet upload
  - URL parse: user name with ipv6 numerical address
  - polarssl: show cipher suite name correctly with 1.1.0
  - polarssl: havege_rand is not present in version 1.1.0 (WARNING: we still
    use the old API which is said to be insecure - see:
    http://polarssl.org/trac/wiki/SecurityAdvisory201102)
  - gnutls: enforced use of SSLv3
- drop patches from upstream now included in release tarball
- don't include fix for broken applications with curl multi from Fedora 14
  onwards (#599340)
- update debug and UTF8 patches

* Mon Jan  2 2012 Paul Howarth <paul@city-fan.org> - 7.23.1-5.0.cf
- add upstream patch that allows FTPS tests to run with nss-3.13 (#760060)

* Tue Dec 27 2011 Paul Howarth <paul@city-fan.org> - 7.23.1-4.0.cf
- allow to run FTPS tests with nss-3.13 (#760060)

* Mon Dec 26 2011 Paul Howarth <paul@city-fan.org> - 7.23.1-3.0.cf
- avoid unnecessary timeout event when waiting for 100-continue (#767490)

* Mon Nov 21 2011 Paul Howarth <paul@city-fan.org> - 7.23.1-2.0.cf
- curl -JO now uses -O name if no C-D header comes (upstream commit c532604)

* Fri Nov 18 2011 Paul Howarth <paul@city-fan.org> - 7.23.1-1.0.cf
- update to 7.23.1:
  - Windows: curl would fail if it found no CA cert, unless -k was used - even
    if a non-SSL protocol URL was used

* Wed Nov 16 2011 Paul Howarth <paul@city-fan.org> - 7.23.0-1.0.cf
- update to 7.23.0:
  - empty headers can be sent in HTTP requests by terminating with a semicolon
  - SSL session sharing support added to curl_share_setopt()
  - added support to MAIL FROM for the optional SIZE parameter
  - smtp: added support for NTLM authentication
  - curl tool: code split into tool_*.[ch] files
  - handle HTTP redirects to "//hostname/path"
  - SMTP without --mail-from caused segfault
  - prevent extra progress meter headers between multiple files
  - allow Content-Length to be replaced when sending HTTP requests
  - curl now always sets postfieldsize to allow --data-binary and --data
    to be mixed in the same command line
  - curl_multi_fdset: avoid FD_SET out of bounds
  - lots of MinGW build tweaks
  - Curl_gethostname: return un-qualified machine name
  - fixed the openssl version number configure check
  - nss: certificates from files are no longer looked up by file base names
  - returning abort from the progress function when using the multi interface
    would not properly cancel the transfer and close the connection
  - fix libcurl.m4 to not fail with modern gcc versions
  - ftp: improved the failed PORT host name resolved error message
  - TFTP timeout and unexpected block adjustments
  - HTTP and GOPHER test server-side connection closing adjustments
  - fix endless loop upon transport connection timeout
  - don't clobber errno on failed connect
  - typecheck: allow NULL to unset CURLOPT_ERRORBUFFER
  - formdata: ack read callback abort
  - make --show-error properly position independent
  - set the ipv6-connection boolean correctly on connect
  - SMTP: fix end-of-body string escaping
  - gtls: only call gnutls_transport_set_lowat with <gnutls-2.12.0
  - HTTP: handle multiple auths in a single WWW-Authenticate line
  - curl_multi_fdset: correct fdset with FTP PORT use
  - windbuild: fix the static build
  - fix builds with GnuTLS version 3
  - fix calling of OpenSSL's ERR_remove_state(0)
  - HTTP auth: fix proxy Negotiate bug when Negotiate not requested
  - ftp PORT: don't hang if bind() fails
  - -# would crash on terminals wider than 256 columns
- drop upstreamed patch for nss
- update patch for broken applications using curl multi (#599340)
- update UTF8 patch

* Mon Sep 19 2011 Paul Howarth <paul@city-fan.org> - 7.22.0-2.0.cf
- nss: select client certificates by DER (#733657)

* Tue Sep 13 2011 Paul Howarth <paul@city-fan.org> - 7.22.0-1.0.cf
- update to 7.22.0:
  - added CURLOPT_GSSAPI_DELEGATION
  - added support for NTLM delegation to Samba's winbind daemon helper ntlm_auth
  - display notes from setup file in testcurl.pl
  - BSD-style lwIP TCP/IP stack experimental support on Windows
  - OpenSSL: use SSL_MODE_RELEASE_BUFFERS if available
  - --delegation was added to set CURLOPT_GSSAPI_DELEGATION
  - nss: start with no database if the selected database is broken
  - telnet: allow programatic use on Windows
  - curl_getdate: detect some illegal dates better
  - when sending a request and an error is received before the (entire) request
    body is sent, stop sending the request and close the connection after
    having received the entire response; this is equally true if an Expect:
    100-continue header was used
  - when using both -J and a single -O with multiple URLs, a missing init
    could cause a segfault
  - -J fixed for escaped quotes
  - -J fixed for file names with semicolons
  - progress: reset flags at transfer start to avoid wrong
    CURLINFO_CONTENT_LENGTH_DOWNLOAD
  - curl_gssapi: guard files with HAVE_GSSAPI and rename private header
  - silence picky compilers: mark unused parameters
  - help output: more gnu-like output
  - libtests: stop checking for CURLM_CALL_MULTI_PERFORM
  - setting a non-HTTP proxy with an environment variable or with CURLOPT_PROXY
    / --proxy (without specifying CURLOPT_PROXYTYPE) would still make it do
    proxy-like HTTP requests
  - CURLFORM_BUFFER: insert filename as documented (regression)
  - SOCKS: fix the connect timeout
  - ftp_doing: bail out on error properly while multi interfacing
  - improved Content-Encoded decoding error message
  - asyn-thread: check for dotted addresses before thread starts
  - cmake: find winsock when building on windows
  - Curl_retry_request: check return code
  - cookies: handle 'secure=' as if it was 'secure'
  - tests: break busy loops in tests 502, 555, and 573
  - FTP: fix proxy connect race condition with multi interface and SOCKS proxy
  - RTSP: GET_PARAMETER requests have a body
  - fixed several memory leaks in OOM situations
  - bad expire(0) caused multi_socket API to hang
  - avoid ftruncate() static define with mingw64
  - mk-ca-bundle.pl: ignore untrusted certs
  - builds with PolarSSL 1.0.0
- curl-config now provides dummy --static-libs option (#733956)
- update UTF8 patch

* Sun Aug 21 2011 Paul Howarth <paul@city-fan.org> - 7.21.7-4.1.cf
- actually fix SIGSEGV of curl -O -J given more than one URL (#723075)

* Tue Aug 16 2011 Paul Howarth <paul@city-fan.org> - 7.21.7-4.0.cf
- fix SIGSEGV of curl -O -J given more than one URL (#723075)
- introduce the --delegation option of curl (#730444)
- initialize NSS with no database if the selected database is broken (#728562)

* Wed Aug  3 2011 Paul Howarth <paul@city-fan.org> - 7.21.7-3.0.cf
- add a new option CURLOPT_GSSAPI_DELEGATION (#719939)

* Wed Jul 13 2011 Paul Howarth <paul@city-fan.org> - 7.21.7-2.0.cf
- for builds using c-ares, have libcurl require at least the version of c-ares
  that it was built against to ensure that all required symbols are available
  (similar issue to that with libssh2 fixed in 7.21.2-2.0.cf)
- upstream release no longer has spurious exec permissions for source files
- use a patch rather than a scripted iconv to re-code docs as UTF-8
- fix dist tag for CentOS 6 and Scientific Linux

* Thu Jun 23 2011 Paul Howarth <paul@city-fan.org> - 7.21.7-1.0.cf
- update to 7.21.7:
  - SECURITY ADVISORY: inappropriate GSSAPI delegation (CVE-2011-2192); full
    details at http://curl.haxx.se/docs/adv_20110623.html
  - recognize the [protocol]:// prefix in proxy hosts where the protocol is one
    of socks4, socks4a, socks5 or socks5h
  - added CURLOPT_CLOSESOCKETFUNCTION and CURLOPT_CLOSESOCKETDATA
  - NTLM: work with unicode
  - fix connect with SOCKS proxy when using the multi interface
  - anyauthput.c: stdint.h must not be included unconditionally
  - CMake: improved build
  - SCP/SFTP enable non-blocking earlier
  - GnuTLS handshake: fix timeout
  - cyassl: build without filesystem
  - HTTPS over HTTP proxy using the multi interface
  - speedcheck: invalid timeout event on a reused handle
  - force connection close for HTTP 200 OK when time condition matched
  - curl_formget: fix FILE * leak
  - configure: improved OpenSSL detection
  - android build: support gingerbread
  - CURLFORM_STREAM: acknowledge CURLFORM_FILENAME
  - windows build: use correct MS CRT
  - pop3: remove extra space in LIST command
- drop upstream patches

* Wed Jun  8 2011 Paul Howarth <paul@city-fan.org> - 7.21.6-3.0.cf
- avoid an invalid timeout event on a reused handle (#679709)

* Wed May 25 2011 Paul Howarth <paul@city-fan.org> - 7.21.6-2.0.cf
- further fix for https via http proxy
  (http://curl.haxx.se/mail/lib-2011-05/0214.html)

* Sat Apr 23 2011 Paul Howarth <paul@city-fan.org> - 7.21.6-1.0.cf
- update to 7.21.6:
  - added --tr-encoding and CURLOPT_TRANSFER_ENCODING
  - curl-config: fix --version
  - curl_easy_setopt.3: CURLOPT_PROXYTYPE clarification
  - use HTTPS properly after CONNECT
  - SFTP: close file before post quote operations
- drop upstreamed patches

* Thu Apr 21 2011 Paul Howarth <paul@city-fan.org> - 7.21.5-3.0.cf
- fix problem with https via http proxy falling back to http
  (http://curl.haxx.se/mail/lib-2011-04/0134.html)

* Mon Apr 18 2011 Paul Howarth <paul@city-fan.org> - 7.21.5-2.0.cf
- fix the output of curl-config --version (upstream commit 82ecc85)

* Mon Apr 18 2011 Paul Howarth <paul@city-fan.org> - 7.21.5-1.0.cf
- update to 7.21.5:
  - SOCKOPTFUNCTION: callback can say already-connected
  - added --netrc-file
  - added (new) support for cyassl
  - TLS-SRP: enabled with OpenSSL
  - added CURLE_NOT_BUILT_IN and CURLE_UNKNOWN_OPTION
  - nss: avoid memory leak on SSL connection failure
  - nss: do not ignore failure of SSL handshake
  - multi: better failed connect handling when using FTP, SMTP, POP3 and IMAP
  - runtests.pl: fix pid number concatenation that prevented it from killing
    the correct process at times
  - PolarSSL: return 0 on receiving TLS CLOSE_NOTIFY alert
  - curl_easy_setopt.3: removed wrong reference to CURLOPT_USERPASSWORD
  - multi: close connection on timeout
  - IMAP in multi mode does SSL connections non-blocking
  - honours the --disable-ldaps configure option
  - force setopt constants written by --libcurl to be long
  - ssh_connect: treat libssh2 return code better
  - SFTP upload could stall the state machine when the multi_socket API was used
  - SFTP and SCP could leak memory when used with the multi interface and
    the connection was closed
  - added missing file to repair the MSVC makefiles
  - fixed detection of recvfrom arguments on Android/bionic
  - GSS: handle reuse fix
  - transfer: avoid insane conversion of time_t
  - nss: do not ignore value of CURLOPT_SSL_VERIFYPEER in certain cases
  - SMTP-multi: non-blocking connect
  - SFTP-multi: set cselect for sftp and scp to fix "stall" risk
  - configure: removed wrongly claimed default paths
  - pop3: fixed torture tests to succeed
  - symbols-in-versions: many corrections
  - if a HTTP request gets retried because the connection was dead, rewind if
    any data was sent as part of it
  - only probe for working ipv6 once and then re-use that info for further
    requests
  - requests that are asked to bind to a local interface/port will no longer
    wrongly re-use connections that aren't bound to that interface/port
  - libcurl.m4: add missing quotes in AC_LINK_IFELSE
  - progress output: don't print the last update on a separate line
  - POP3: the command to send is STLS, not STARTTLS
  - POP3: PASS command was not sent after upgrade to TLS
  - configure: fix libtool warning
  - nss: allow to use multiple client certificates for a single host
  - HTTP pipelining: fix handling of zero-length responses
  - don't list NTLM in curl-config when HTTP is disabled
  - curl_easy_setopt.3: CURLOPT_RESOLVE typo version
  - OpenSSL: build fine with no-sslv2 versions
  - checkconnection: don't call with NULL pointer with RTSP and multi interface
  - Borland makefile updates
  - configure: libssh2 link fix without pkg-config
  - certinfo crash
  - CCC crash
- drop upstreamed patches
- update debug and pkgconfig patches
- nobody else likes macros for commands

* Sat Mar  5 2011 Paul Howarth <paul@city-fan.org> - 7.21.4-5.0.cf
- work around valgrind bug (#678518)

* Tue Feb 22 2011 Paul Howarth <paul@city-fan.org> - 7.21.4-2.0.cf
- do not ignore failure of SSL handshake (upstream commit 7aa2d10)

* Thu Feb 17 2011 Paul Howarth <paul@city-fan.org> - 7.21.4-1.0.cf
- update to 7.21.4:
  - CURLINFO_FTP_ENTRY_PATH now supports SFTP
  - introduced new framework for unit-testing
  - ares: ask for both IPv4 and IPv6 addresses
  - SMTP: add brackets for MAIL FROM
  - multi: connect fail => use next IP address
  - use the timeout when using multiple IP addresses similar to how the easy
    interface does it
  - cookies: tricked dotcounter fixed
  - pubkey_show: allocate buffer to fit any-size result
  - Curl_nss_connect: avoid PATH_MAX
  - Curl_do: avoid using stale conn pointer
  - tftpd test server: avoid buffer overflow report from glibc
  - nss: avoid CURLE_OUT_OF_MEMORY given a file name without any slash
  - nss: fix a bug in handling of CURLOPT_CAPATH
  - OpenSSL get_cert_chain: support larger data sets
  - SCP/SFTP transfers: acknowledge speedcheck
  - connect problem: use UDP correctly
  - OpenSSL: improved error message on SSL_CTX_new failures
  - HTTP: memory leak on multiple Location:
  - ares_query_completed_cb: don't touch invalid data
  - ares: memory leak fix
  - mk-ca-bundle: use new cacert url
  - Curl_gmtime: added a portable gmtime and check for NULL
  - curl.1: typo in -v description
  - CURLOPT_SOCKOPTFUNCTION: return proper error code
  - --keepalive-time: warn if not supported properly
  - file: add support for CURLOPT_TIMECONDITION
  - nss: avoid memory leaks and failure of NSS shutdown
  - multi: fix CURLM_STATE_TOOFAST for multi_socket
- update debug patch
- avoid memory leak on SSL connection failure (upstream commit a40f58d)
- drop upstreamed patches
- drop ares-ipv6 patch

* Tue Feb  8 2011 Paul Howarth <paul@city-fan.org> - 7.21.3-3.0.cf
- rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Jan 12 2011 Paul Howarth <paul@city-fan.org> - 7.21.3-2.0.cf
- build libcurl with --enable-hidden-symbols

* Thu Dec 16 2010 Paul Howarth <paul@city-fan.org> - 7.21.3-1.0.cf
- update to 7.21.3:
  - added --noconfigure switch to testcurl.pl
  - added --xattr option
  - added CURLOPT_RESOLVE and --resolve
  - added CURLAUTH_ONLY
  - added version-check.pl to the examples dir
  - check for libcurl features for some command line options
  - Curl_setopt: disallow CURLOPT_USE_SSL without SSL support
  - http_chunks: remove debug output
  - URL-parsing: consider ? a divider
  - SSH: avoid using the libssh2_ prefix
  - SSH: use libssh2_session_handshake() to work on win64
  - ftp: prevent server from hanging on closed data connection when stopping
    a transfer before the end of the full transfer (ranges)
  - LDAP: detect non-binary attributes properly
  - ftp: treat server's response 421 as CURLE_OPERATION_TIMEDOUT
  - gnutls->handshake: improved timeout handling
  - security: pass the right parameter to init
  - krb5: use GSS_ERROR to check for error
  - TFTP: resend the correct data
  - configure: fix autoconf 2.68 warning: no AC_LANG_SOURCE call detected
  - GnuTLS: now detects socket errors on Windows
  - symbols-in-versions: updated en masse
  - added a couple of examples that were missing from the tarball
  - Curl_send/recv_plain: return errno on failure
  - Curl_wait_for_resolv (for c-ares): correct timeout
  - ossl_connect_common: detect connection re-use
  - configure: prevent link errors with --librtmp
  - openldap: use remote port in URL passed to ldap_init_fd()
  - url: provide dead_connection flag in Curl_handler::disconnect
  - lots of compiler warning fixes
  - ssh: fix a download resume point calculation
  - fix getinfo CURLINFO_LOCAL* for reused connections
  - multi: the returned running handles counter could turn negative
  - multi: only ever consider pipelining for connections doing HTTP(S)
- drop upstream patches now in tarball
- update bz650255 and ares-ipv6 patches to apply against new codebase
- add workaround for false-positive glibc-detected buffer overflow in tftpd
  test server with FORTIFY_SOURCE (similar to #515361)

* Sat Nov 13 2010 Paul Howarth <paul@city-fan.org> - 7.21.2-5.0.cf
- do not send QUIT to a dead FTP control connection (#650255)
- pull back glibc's implementation of str[n]casecmp(); #626470 appears fixed

* Tue Nov  9 2010 Paul Howarth <paul@city-fan.org> - 7.21.2-4.0.cf
- prevent FTP client from hanging on unrecognized ABOR response (#649347)
- return more appropriate error code in case FTP server session idle
  timeout has been exceeded (#650255)

* Fri Oct 29 2010 Paul Howarth <paul@city-fan.org> - 7.21.2-3.0.cf
- prevent FTP server from hanging on closed data connection (#643656)

* Thu Oct 14 2010 Paul Howarth <paul@city-fan.org> - 7.21.2-2.0.cf
- enforce versioned libssh2 dependency for libcurl (#642796)

* Wed Oct 13 2010 Paul Howarth <paul@city-fan.org> - 7.21.2-1.0.cf
- update to 7.21.2:
  - curl -T: ignore file size of special files
  - added GOPHER protocol support
  - c-ares build now requires c-ares >= 1.6.0
  - --remote-header-name security vulnerability fixed:
    http://curl.haxx.se/docs/adv_20101013.html
  - multi: support the timeouts correctly, fixes known bug #62
  - multi: use timeouts properly for MAX_RECV/SEND_SPEED
  - negotiation: Wrong proxy authorization
  - multi: avoid sending multiple complete messages
  - cmdline: make -F type= accept ;charset=
  - RESUME_FROM: clarify what ftp uploads do
  - http: handle trailer headers in all chunked responses
  - Curl_is_connected: use correct errno
  - progress: callback for POSTs less than MAX_INITIAL_POST_SIZE
  - link curl and the test apps with -lrt explicitly when necessary
  - chunky parser: only rewind stream internally if needed
  - remote-header-name: don't output filename when NULL
  - Curl_timeleft: avoid returning "no timeout" by mistake
  - timeout: use the correct start value as offset
  - FTP: fix wrong timeout trigger
  - buildconf got better output on failures
  - rtsp: avoid SIGSEGV on malformed header
  - LDAP: support for tunnelling queries through HTTP proxy
  - configure's --enable-werror had a bashism
  - test565: don't hardcode IP:PORT
  - configure: check for gcrypt if using GnuTLS
  - configure: don't enable RTMP if the lib detect fails
  - curl_easy_duphandle: clone the c-ares handle correctly
  - support URL containing colon without trailing port number
  - parsedate: allow time specified without seconds
  - curl_easy_escape: don't escape "unreserved" characters
  - SFTP: avoid downloading negative sizes
  - lots of GSS/KRB FTP fixes
  - TFTP: work around tftpd-hpa upload bug
  - libcurl.m4: several fixes
  - HTTP: remove special case for 416
  - examples: use example.com in example URLs
  - globbing: fix crash on unbalanced open brace
  - cmake: build fixed
- drop upstream patches
- make 0102-curl-7.21.2-debug.patch less intrusive
- update workaround for broken applications using curl multi
- use LD_PRELOAD hack to get sshd running in test suite with SELinux enforcing
- drop SELinux buildreqs, no longer needed

* Thu Sep 30 2010 Paul Howarth <paul@city-fan.org> - 7.21.1-6.0.cf
- rebuild for gcc bug (#634757)

* Sat Sep 11 2010 Paul Howarth <paul@city-fan.org> - 7.21.1-5.0.cf
- make it possible to run SCP/SFTP tests on x86_64 (#632914)

* Wed Sep  8 2010 Paul Howarth <paul@city-fan.org> - 7.21.1-4.0.cf
- work around glibc/valgrind problem on x86_64 (#631449)

* Tue Aug 24 2010 Paul Howarth <paul@city-fan.org> - 7.21.1-3.0.cf
- sync patches with Rawhide
- drop dependency on automake for devel package from F-14, where
  %%{_datadir}/aclocal is included in the filesystem package
- drop dependency on pkgconfig for devel package from F-11, where
  pkgconfig dependencies are auto-generated

* Mon Aug 23 2010 Paul Howarth <paul@city-fan.org> - 7.21.1-2.1.cf
- fix kerberos proxy authentication for https (#625676)
- work around glibc/valgrind problem on x86_64 (#626470)

* Thu Aug 19 2010 Paul Howarth <paul@city-fan.org> - 7.21.1-2.0.cf
- modify system headers to work around gcc bug (#617757)
- curl -T now ignores file size of special files (#622520)

* Thu Aug 12 2010 Paul Howarth <paul@city-fan.org> - 7.21.1-1.0.cf
- update to 7.21.1:
  - added support for NTLM authentication when compiled with NSS
  - curl-config: --built-shared returns shared info
  - multi: call the progress callback in all states
  - multi: unmark handle as used when no longer head of pipeline
  - sendrecv: treat all negative values from send/recv as errors
  - ftp-wildcard: avoid tight loop when used without any pattern
  - multi_socket: re-use of same socket without notifying app
  - ftp wildcard: FTP LIST parser FIX
  - urlglobbing backslash escaping bug
  - multi: CURLINFO_LASTSOCKET doesn't work after remove_handle
  - --libcurl: use *_LARGE options with typecasted constants
  - --libcurl: hide setopt() calls setting default options
  - curl: avoid setting libcurl options to its default
  - --libcurl: list the tricky options instead of using [REMARK]
  - http: don't enable chunked during authentication negotiations
  - upload: warn users trying to upload from stdin with anyauth
  - threaded resolver: fix timeout issue
  - multi: fix condition that remove timers before trigger
  - examples: add curl_multi_timeout
  - --retry: access violation with URL part sets continued
  - remote-header-name: chop filename at next semicolon
  - ftp: response timeout bug in "quote" sending
  - CUSTOMREQUEST: shouldn't be disabled when HTTP is disabled
  - NTLM tests: boost coverage by forcing the hostname
  - multi: fix FTPS connecting the data connection with OpenSSL
  - retry: consider retrying even if -f is used
  - fix SOCKS problem when using multi interface
  - typecheck-gcc: add checks for recently added options
  - SCP: send large files properly with new enough libssh2
  - multi_socket: set timeout for 100-continue
  - ";type=" URL suffix over HTTP proxy
  - acknowledge progress callback error returns during connect
- drop upstreamed NTLM-with-NSS patch
- rediff other patches where necessary
- use LD_PRELOAD with absolute directory on RHL-9 to avoid test failures

* Mon Jun 28 2010 Paul Howarth <paul@city-fan.org> - 7.21.0-2.0.cf
- add support for NTLM authentication (#603783)

* Fri Jun 18 2010 Paul Howarth <paul@city-fan.org> - 7.21.0-1.0.cf
- update to 7.21.0
  new features:
  - added the --proto and -proto-redir options
  - new configure option --enable-threaded-resolver
  - improve TELNET ability with libcurl
  - added support for PolarSSL
  - added support for FTP wildcard matching and downloads
  - added support for RTMP
  - introducing new LDAP code for new enough OpenLDAP
  - OpenLDAP support enabled for cygwin builds
  - added CURLINFO_PRIMARY_PORT, CURLINFO_LOCAL_IP and CURLINFO_LOCAL_PORT
  bugfixes:
  - prevent needless reverse name lookups
  - detect GSS on ancient Linux distros
  - GnuTLS: EOF caused error when it wasn't
  - GnuTLS: SSL handshake phase is non-blocking
  - -J/--remote-header-name strips CRLF
  - MSVC makefiles now use ws2_32.lib instead of wsock32.lib
  - -O crash on windows
  - SSL handshake timeout underflow in libcurl-NSS
  - multi interface missed storing connection time
  - broken CRL support in libcurl-NSS
  - ignore response-body on redirect even if compressed
  - OpenSSL handshake state-machine for multi interface
  - TFTP timeout option sent correctly
  - TFTP block id wrap
  - curl_multi_socket_action() timeout handles inaccuracy in timers better
  - SCP/SFTP failure to respect the timeout
  - spurious SSL connection aborts with OpenSSL
- rename patches as per Fedora package
- drop applied patches
- update %%description

* Fri Jun  4 2010 Paul Howarth <paul@city-fan.org> - 7.20.1-8.0.cf
- workaround for broken applications using curl multi (#599340)
- enable threaded DNS lookup instead of using c-ares for F-12 and F-13 builds

* Tue May 25 2010 Paul Howarth <paul@city-fan.org> - 7.20.1-7.0.cf
- fix -J/--remote-header-name to strip CR-LF (upstream patch)

* Wed May 12 2010 Paul Howarth <paul@city-fan.org> - 7.20.1-6.0.cf
- CRL support now works again (#581926)
- fix dist tag for RHEL-6 Beta

* Thu Apr 29 2010 Paul Howarth <paul@city-fan.org> - 7.20.1-5.0.cf
- fix the test suite so that the SSH server can start in an SELinux enforcing
  environment (#521087)

* Sun Apr 25 2010 Paul Howarth <paul@city-fan.org> - 7.20.1-4.0.cf
- upstream patch preventing failure of test536 with threaded DNS resolver
- upstream patch preventing SSL handshake timeout underflow

* Tue Apr 20 2010 Paul Howarth <paul@city-fan.org> - 7.20.1-2.1.cf
- experimentally enable threaded DNS lookup instead of using c-ares
  (Rawhide [F-14] builds only)
- fix multilib confict in curl-config --configure (#584107)
- tighten up dependency on libcurl from libcurl-devel to use %%{?_isa}
- replace Rawhide s390-sleep patch with a more targeted patch adding a
  delay after tests 513 and 514 rather than after all tests
- add patch disabling valgrind in test623 as it identifies a memory leak in
  libssh2 and breaks the build

* Tue Apr 20 2010 Paul Howarth <paul@city-fan.org> - 7.20.1-1.1.cf
- sync patches with Rawhide
- remove redundant compiler/linker flags from libcurl.pc

* Thu Apr 15 2010 Paul Howarth <paul@city-fan.org> - 7.20.1-1.0.cf
- update to 7.20.1 (see RELEASE-NOTES for details)
- drop upstreamed patches
- add patch to fix GSSAPI support for ancient distros like RHEL-3

* Wed Mar 24 2010 Paul Howarth <paul@city-fan.org> - 7.20.0-4.0.cf
- add missing quote in libcurl.m4 (#576252)
- resync cc-err patch with Fedora

* Sun Mar 21 2010 Paul Howarth <paul@city-fan.org> - 7.20.0-3.0.cf
- throw CURLE_SSL_CERTPROBLEM in case peer rejects a certificate (#565972)
- handle move of kerberos installation prefix in krb5 >= 1.8
- drop libidn-devel dependency for libcurl-devel; no longer needed

* Tue Feb 23 2010 Paul Howarth <paul@city-fan.org> - 7.20.0-2.0.cf
- merge patches with Fedora: s390-sleep, debug, multilib, ares-ipv6
- drop privlibs patch, no longer useful
- add patch forcing -lrt when linking the curl tool and test-cases

* Tue Feb  9 2010 Paul Howarth <paul@city-fan.org> - 7.20.0-1.0.cf
- update to 7.20.0 (added support for IMAP(S), POP3(S), SMTP(S) and RTSP)
- drop upstream patches
- update multilib, privlibs and s390-sleep patches

* Sun Jan 31 2010 Paul Howarth <paul@city-fan.org> - 7.19.7-11.0.cf
- upstream patch adding a new option -J/--remote-header-name
- dropped temporary workaround for #545779

* Tue Dec 22 2009 Paul Howarth <paul@city-fan.org> - 7.19.7-9.0.cf
- re-enable c-ares support, with temporary workaround for IPv4/IPv6 issue
  (ticket:2, #548269) - c-ares support is needed to resolve #539809

* Thu Dec 10 2009 Paul Howarth <paul@city-fan.org> - 7.19.7-8.0.cf
- use different ports in the test suites for different builds so we can run
  the builds in parallel
- temporary workaround for NSS_VersionCheck issues (#545779)
- skip the (lengthy) test suite on EOL Fedora releases (over ~400 days old);
  the tests are still run for all RHEL releases, which should provide
  sufficient back-compatibility coverage

* Mon Dec  7 2009 Paul Howarth <paul@city-fan.org> - 7.19.7-5.0.cf
- avoid use of uninitialized value in lib/nss.c
- attempt to fix failures for tests 513, 514, and 1097
- no longer leave debug data for test suite around
- disable c-ares support (causes problems reaching hosts that have both IPv4
  and IPv6 addresses - http://curl.haxx.se/mail/lib-2009-12/0057.html)

* Tue Dec  1 2009 Paul Howarth <paul@city-fan.org> - 7.19.7-4.0.cf
- dist tag for Rawhide no longer needs special-casing

* Thu Nov 12 2009 Paul Howarth <paul@city-fan.org> - 7.19.7-3.0.cf
- fix crash on doubly closed NSPR descriptor (#534176)
- new version of patch for broken TLS servers (#525496, #527771)
- run test suite to completion and leave debug data around

* Wed Nov  4 2009 Paul Howarth <paul@city-fan.org> - 7.19.7-2.0.cf
- new upstream release, dropped applied patches
- workaround for broken TLS servers (#525496, #527771)
- build libcurl with c-ares support (#514771)
- update multilib and privlibs patches to match Fedora versions
- update debug patch to apply against 7.19.7
- bump NSS version requirement to 3.12.3 (test suite now fails w/NSS on
  Fedora 8 and 9 so revert to OpenSSL for those releases)

* Sun Sep 27 2009 Paul Howarth <paul@city-fan.org> - 7.19.6-10.0.cf
- explicitly buildreq/req libssh2 >= 1.2 due to its ABI change (#525002)
- note: unlike the Fedora package I'm not running the test suite with valgrind
  as it takes long enough already and valgrind isn't available on some of the
  ancient distros I'm supporting

* Wed Sep 23 2009 Paul Howarth <paul@city-fan.org> - 7.19.6-8.0.cf
- rebuild for libssh2 1.2

* Fri Sep 18 2009 Paul Howarth <paul@city-fan.org> - 7.19.6-7.0.cf
- make curl test-suite more verbose

* Fri Sep 18 2009 Paul Howarth <paul@city-fan.org> - 7.19.6-6.0.cf
- update polling patch to the latest upstream version

* Fri Sep  4 2009 Paul Howarth <paul@city-fan.org> - 7.19.6-5.0.cf
- buildreq openssh server and clients for ssh coverage in test suite

* Fri Sep  4 2009 Paul Howarth <paul@city-fan.org> - 7.19.6-4.0.cf
- use pkg-config to find nss and libssh2 if possible
- better patch (not only) for SCP/SFTP polling
- improve error message for not matching common name (#516056)

* Sun Aug 23 2009 Paul Howarth <paul@city-fan.org> - 7.19.6-3.0.cf
- avoid tight loop during a sftp upload
  (see http://permalink.gmane.org/gmane.comp.web.curl.library/24744)

* Tue Aug 18 2009 Paul Howarth <paul@city-fan.org> - 7.19.6-2.0.cf
- let curl package depend on the same version of libcurl
- change NSS code to not ignore the value of ssl.verifyhost and produce more
  verbose error messages (#516056)
- renumber patches as per Fedora version
- avoid tests 513, 514, and 1097, which regularly fail on the buildsystem

* Thu Aug 13 2009 Paul Howarth <paul@city-fan.org> - 7.19.6-1.0.cf
- update to 7.19.6
- drop FTP socket and NSS cert patches; issues now fixed upstream

* Fri Jul 10 2009 Paul Howarth <paul@city-fan.org> - 7.19.5-7.0.cf
- fix SIGSEGV when using NSS client certificates, thanks to Claes Jakobsson

* Mon Jul  6 2009 Paul Howarth <paul@city-fan.org> - 7.19.5-6.0.cf
- resync with Fedora

* Sun Jul  5 2009 Paul Howarth <paul@city-fan.org> - 7.19.5-5.0.cf
- run test suite after build (add buildreq stunnel)
- enable built-in manual (requires buildreq groff)

* Wed Jun 24 2009 Paul Howarth <paul@city-fan.org> - 7.19.5-4.0.cf
- Fedora version now fixes header multilib issue in much the same way as this
  version (#504857)

* Mon Jun 15 2009 Paul Howarth <paul@city-fan.org> - 7.19.5-2.0.cf
- renumber patches as per Fedora version

* Mon May 18 2009 Paul Howarth <paul@city-fan.org> - 7.19.5-1.0.cf
- update to 7.19.5
- remove upstreamed memory leak and infinite loop patches
- update debug patch (upstream moved from autoconf 2.61 to 2.63)

* Tue May 12 2009 Paul Howarth <paul@city-fan.org> - 7.19.4-11.0.cf
- fix infinite loop while loading a private key, thanks to Michael Cronenworth
  (#453612)
- fix curl/nss memory leaks while using client certificate (#453612, accepted
  by upstream)

* Thu Apr 23 2009 Paul Howarth <paul@city-fan.org> - 7.19.4-9.0.cf
- fix debuginfo creation (#496778), but unlike Fedora, without running the
  autotools during the build process

* Wed Apr 15 2009 Paul Howarth <paul@city-fan.org> - 7.19.4-6.0.cf
- upstream patch fixing memory leak in lib/nss.c (#453612)

* Wed Mar 18 2009 Paul Howarth <paul@city-fan.org> - 7.19.4-5.0.cf
- enable 6 additional crypto algorithms by default (#436781,
  accepted by upstream)

* Mon Mar 16 2009 Paul Howarth <paul@city-fan.org> - 7.19.4-4.0.cf
- fix memory leak in src/main.c (accepted by upstream)
- make libcurl-devel multilib-clean (#488922)

* Mon Mar  9 2009 Paul Howarth <paul@city-fan.org> - 7.19.4-2.0.cf
- drop .easy-leak patch, causes problems in pycurl (#488791)
- add libssh-devel dependency in libcurl-devel (#488895)

* Thu Mar  5 2009 Paul Howarth <paul@city-fan.org> - 7.19.4-1.0.cf
- update to 7.19.4 (fixes CVE-2009-0037, #485271)
- fix leak in curl_easy* functions, thanks to Kamil Dudka
- drop nss-fix patch, applied upstream

* Tue Feb 17 2009 Paul Howarth <paul@city-fan.org> - 7.19.3-1.1.cf
- add updated badsocket patch from Fedora, renamed to reflect curl version it
  applies to
- add nss-fix patch from Fedora
- build using NSS rather than OpenSSL where supported again

* Tue Jan 20 2009 Paul Howarth <paul@city-fan.org> - 7.19.3-1.0.cf
- update to 7.19.3

* Fri Nov 14 2008 Paul Howarth <paul@city-fan.org> - 7.19.2-1.0.cf
- update to 7.19.2

* Thu Nov  6 2008 Paul Howarth <paul@city-fan.org> - 7.19.1-1.0.cf
- update to 7.19.1
- NSS thread safety issues addressed upstream, patch removed

* Fri Sep 19 2008 Paul Howarth <paul@city-fan.org> - 7.19.0-1.2.cf
- NSS support is broken again, always build with OpenSSL

* Thu Sep  4 2008 Paul Howarth <paul@city-fan.org> - 7.19.0-1.1.cf
- add thread safety to libcurl NSS cleanup() functions (#459297)

* Tue Sep  2 2008 Paul Howarth <paul@city-fan.org> - 7.19.0-1.0.cf
- update to 7.19.0
- drop badsocket patch, issue now addressed upstream
- drop nssproxy patch, now applied upstream

* Fri Aug 22 2008 Paul Howarth <paul@city-fan.org> - 7.18.2-5.0.cf
- remove note about libcurl.so.3 now that it's gone in Fedora too

* Fri Aug 22 2008 Paul Howarth <paul@city-fan.org> - 7.18.2-4.0.cf
- add note in %%description about not providing libcurl.so.3

* Fri Jul  4 2008 Paul Howarth <paul@city-fan.org> - 7.18.2-3.0.cf
- enable support for libssh2 (#453958)
- tweak dist tag macros to work on current Rawhide with three-part releasenum

* Wed Jun 18 2008 Paul Howarth <paul@city-fan.org> - 7.18.2-2.0.cf
- fix curl_multi_perform() over a proxy (#450140), thanks to Rob Crittenden

* Thu Jun  5 2008 Paul Howarth <paul@city-fan.org> - 7.18.2-1.0.cf
- update to 7.18.2

* Wed May  7 2008 Paul Howarth <paul@city-fan.org> - 7.18.1-2.0.cf
- use a different libtool hack to avoid bogus rpaths; no longer need to
  buildreq libtool on x86_64
- add ABI docs for libcurl

* Mon Mar 31 2008 Paul Howarth <paul@city-fan.org> - 7.18.1-1.0.cf
- update to 7.18.1 (fixes #397911)
- no longer need _GNU_SOURCE
- ca_bundle.crt no longer included upstream

* Tue Feb 19 2008 Paul Howarth <paul@city-fan.org> - 7.18.0-2.0.cf
- define _GNU_SOURCE so that NI_MAXHOST gets defined from glibc

* Tue Jan 29 2008 Paul Howarth <paul@city-fan.org> - 7.18.0-1.0.cf
- update to 7.18.0
- update multilib patch (--static-libs option removed as we don't ship
  static libs)
- drop curl-config patch, obsoleted by @SSL_ENABLED@ autoconf
  substitution (#432667)
- sslgen patch now included upstream and no longer needed

* Tue Jan 22 2008 Paul Howarth <paul@city-fan.org> - 7.17.1-6.1.cf
- fix curl-devel obsoletes so that we don't break F8->F9 upgrade
  path (#429612)

* Fri Jan 11 2008 Paul Howarth <paul@city-fan.org> - 7.17.1-5.1.cf
- do not attempt to close a bad socket (#427966), thanks to Caolan McNamara

* Fri Dec  7 2007 Paul Howarth <paul@city-fan.org> - 7.17.1-4.1.cf
- rebuild for new openldap in Rawhide

* Fri Nov 30 2007 Paul Howarth <paul@city-fan.org> - 7.17.1-3.1.cf
- add LDAP/LDAPS to %%description
- simplify compiler flag setup

* Thu Nov 29 2007 Paul Howarth <paul@city-fan.org> - 7.17.1-2.2.cf
- add -DHAVE_PK11_CREATEGENERICOBJECT to CPPFLAGS when building with NSS to
  maintain compatibility with openssl-based builds
- explictly buildreq krb5-devel, needed for GSSAPI support
- rework pkgconfig version check to avoid SRPM build problems

* Thu Nov 22 2007 Paul Howarth <paul@city-fan.org> - 7.17.1-2.1.cf
- update description to contain complete supported servers list (#393861)

* Mon Nov 19 2007 Paul Howarth <paul@city-fan.org> - 7.17.1-1.3.cf
- include patch to enable SSL usage in NSS when a socket is opened
  nonblocking, thanks to Rob Crittenden (rcritten@redhat.com)

* Tue Nov  6 2007 Paul Howarth <paul@city-fan.org> - 7.17.1-1.2.cf
- strip URL variable from pkgconfig file on older distributions
  that have broken curl-config scripts in its presence

* Thu Nov  1 2007 Paul Howarth <paul@city-fan.org> - 7.17.1-1.1.cf
- update to 7.17.1
- switch to NSS by default again for distributions that support it, but
  support building using --without nss for traditional OpenSSL builds
- provide webclient (#225671)
- list features correctly when curl is compiled against NSS (#316191)
- create libcurl and libcurl-devel subpackages (#130251)

* Fri Sep 14 2007 Paul Howarth <paul@city-fan.org> - 7.17.0-1.1.cf
- update to 7.17.0
- remove anonymous ftp login patch, now upstream
- remove LDAP version detection in spec since LDAP libraries are now linked
  directly rather than using dlopen()
- enable LDAPS support
- make sure docs have UTF-8 encoding

* Wed Sep  5 2007 Paul Howarth <paul@city-fan.org> - 7.16.4-4.1.cf
- revert back to using OpenSSL by default (#266021), but support --with nss
  as a build option for those distributions that support it

* Mon Aug 27 2007 Paul Howarth <paul@city-fan.org> - 7.16.4-3.2.cf
- use nss rather than openssl for Fedora 5, RHEL 5 onwards

* Fri Aug 24 2007 Paul Howarth <paul@city-fan.org> - 7.16.4-3.1.cf
- rebuild for BuildID inclusion
  (http://fedoraproject.org/wiki/Releases/FeatureBuildId)

* Fri Aug 10 2007 Jindrich Novy <jnovy@redhat.com> - 7.16.4-2
- fix anonymous ftp login (#251570), thanks to David Cantrell

* Wed Jul 11 2007 Paul Howarth <paul@city-fan.org> - 7.16.4-1.1.cf
- update to 7.16.4

* Mon Jun 25 2007 Paul Howarth <paul@city-fan.org> - 7.16.3-1.1.cf
- update to 7.16.3
- remove print like crazy patch, no longer needed

* Fri Jun 22 2007 Paul Howarth <paul@city-fan.org> - 7.16.2-6.cf
- move docs/CONTRIBUTE to devel package

* Mon Jun 18 2007 Jindrich Novy <jnovy@redhat.com> - 7.16.2-5
- don't print like crazy (#236981), backported from upstream CVS

* Fri Jun  1 2007 Paul Howarth <paul@city-fan.org> - 7.16.2-2.cf
- package libcurl.m4 in curl-devel (#239664), thanks to Quy Tonthat

* Thu Apr 12 2007 Paul Howarth <paul@city-fan.org> - 7.16.2-1.cf
- update to 7.16.2
- update multilib and privlibs patches
- try to avoid spurious linker options for looking in standard libraries
- don't create/ship static libraries (#225671)
- honour %%{_smp_mflags}
- try to preserve timestamps where possible by using install -p

* Thu Mar 22 2007 Paul Howarth <paul@city-fan.org> - 7.16.1-2.cf
- use versioned obsolete for compat-libcurl
- buildreq libidn-devel

* Tue Jan 30 2007 Paul Howarth <paul@city-fan.org> - 7.16.1-1.cf
- update to 7.16.1
- don't package generated makefiles for docs/examples to avoid
  multilib conflicts
- update privlibs patch, not fully incorporated upstream
- remove redundant buildreq automake
- use system libtool to avoid bogus rpaths on x86_64
- fix dist tag for Fedora 7

* Wed Nov 22 2006 Paul Howarth <paul@city-fan.org> - 7.16.0-3.cf
- prevent curl from dlopen()ing missing ldap libraries so that ldap://
  requests work without needing openldap-devel at runtime (#215928)

* Wed Nov  1 2006 Paul Howarth <paul@city-fan.org> - 7.16.0-2.cf
- add Requires: pkgconfig for curl-devel
- move LDFLAGS and LIBS to Libs.private in libcurl.pc.in (#213278)
- fix multilib problem using pkg-config

* Mon Oct 30 2006 Paul Howarth <paul@city-fan.org> - 7.16.0-1.cf
- update to 7.16.0
- further dist tag tweaks for rawhide
- convert spec file to UTF8

* Thu Sep 14 2006 Paul Howarth <paul@city-fan.org> - 7.15.5-2.cf
- fix dist tag for development releases
- add buildreq zlib-devel

* Mon Aug  7 2006 Paul Howarth <paul@city-fan.org> - 7.15.5-1.cf
- update to 7.15.5
- define %%{__id_u} in a more portable way

* Mon Jun 12 2006 Paul Howarth <paul@city-fan.org> - 7.15.4-1.cf
- update to 7.15.4

* Tue Mar 21 2006 Paul Howarth <paul@city-fan.org> - 7.15.3-2.cf
- fix multilib problem - #181290 -
  curl-devel.i386 not installable together with curl-devel.x86-64

* Mon Mar 20 2006 Paul Howarth <paul@city-fan.org> - 7.15.3-1.cf
- update to 7.15.3

* Tue Feb 28 2006 Paul Howarth <paul@city-fan.org> - 7.15.2-1.cf
- update to 7.15.2
- support building on CentOS

* Wed Dec  7 2005 Paul Howarth <paul@city-fan.org> - 7.15.1-1.cf
- update to 7.15.1
- remove buildroot unconditionally in %%clean and %%install
- simplify distribution detection
- include pkgconfig file in devel subpackage

* Fri Oct 14 2005 Paul Howarth <paul@city-fan.org> - 7.15.0-1.cf
- compat package renamed to libcurlVERSION for forward compatibility when a new
  soname is used in upstream curl, so that multiple versions of the libcurl
  library can be installed in parallel
- don't use %%{_bindir} in command paths, use /usr/bin explicitly
- spec file cleanup

* Mon Sep  5 2005 Paul Howarth <paul@city-fan.org> - 7.14.1-2.cf
- build fully distro-specific packages to avoid dependency issues

* Fri Sep  2 2005 Paul Howarth <paul@city-fan.org> - 7.14.1-1.cf
- update to 7.14.1

* Wed Jul 27 2005 Paul Howarth <paul@city-fan.org> - 7.14.0-3.cf
- different summary, group, and description in compat mode
- use the correct cert bundle location for FC4
- use exclude in the file lists rather than deleting files from
  the buildroot
- add explicit requirement for the CA bundle file
- license is MIT, not MPL

* Thu Jun 30 2005 Paul Howarth <paul@city-fan.org> - 7.14.0-2.cf
- enable building with dist tag if required:
  e.g. $ rpmbuild --define "dist .fc4" ...

* Tue May 17 2005 Paul Howarth <paul@city-fan.org> - 7.14.0-1.cf
- update to 7.14.0

* Wed Apr  6 2005 Paul Howarth <paul@city-fan.org> - 7.13.2-1.cf
- update to 7.13.2
- remove SSL patch, included upstream

* Sat Mar  5 2005 Paul Howarth <paul@city-fan.org> - 7.13.1-1.cf
- update to 7.13.1
- add patch to fix SSL breakage
- modify install process to avoid need for path patch

* Fri Feb 25 2005 Paul Howarth <paul@city-fan.org> - 7.13.0-2.cf
- fix for CAN-2005-0490

* Wed Feb  2 2005 Paul Howarth <paul@city-fan.org> - 7.13.0-1.cf
- update to 7.13.0

* Mon Jan 31 2005 Paul Howarth <paul@city-fan.org> - 7.12.3-2.cf
- add .cf repo tag
- remove INSTALL from docs
- enable GSSAPI auth (#129353)

* Tue Dec 21 2004 Paul Howarth <paul@city-fan.org> - 7.12.3-1
- update to 7.12.3

* Fri Nov 26 2004 Paul Howarth <paul@city-fan.org> - 7.12.2-2
- add libidn-devel dependency to curl-devel
  (http://www.redhat.com/archives/fedora-list/2004-November/msg07551.html)

* Tue Oct 19 2004 Paul Howarth <paul@city-fan.org> - 7.12.2-1
- update to 7.12.2

* Wed Oct  6 2004 Paul Howarth <paul@city-fan.org> - 7.12.1-2
- include facility to build compat-libcurl package containing
  only the library
- remove certaltname patch completely
- include COPYING
- general tidy-up of spec file

* Wed Aug 11 2004 Paul Howarth <paul@city-fan.org> - 7.12.1-1
- update to 7.12.1

* Thu Jun 03 2004 Paul Howarth <paul@city-fan.org> - 7.12.0-1
- update to 7.12.0

* Tue Apr 27 2004 Paul Howarth <paul@city-fan.org> - 7.11.2-1
- update to 7.11.2
- remove parts of curl-7.10.6-certaltname.patch that fix
  no-longer-applicable cosmetic issues and rename to
  curl-7.11.2-certaltname.patch

* Mon Mar 22 2004 Paul Howarth <paul@city-fan.org> - 7.11.1-1
- update to 7.11.1
- remove no-longer-applicable curl-7.10.4-nousr.patch

* Fri Jan 23 2004 Paul Howarth <paul@city-fan.org> - 7.11.0-1
- update to 7.11.0

* Wed Oct 15 2003 Adrian Havill <havill@redhat.com> - 7.10.6-7
- aclocal before libtoolize
- move OpenLDAP license so it's present as a doc file, present in
  both the source and binary as per conditions

* Mon Oct 13 2003 Adrian Havill <havill@redhat.com> - 7.10.6-6
- add OpenLDAP copyright notice for usage of code, add OpenLDAP
  license for this code

* Tue Oct 07 2003 Adrian Havill <havill@redhat.com> - 7.10.6-5
- match serverAltName certs with SSL (#106168)

* Tue Sep 16 2003 Adrian Havill <havill@redhat.com> - 7.10.6-4.1
- bump n-v-r for RHEL

* Tue Sep 16 2003 Adrian Havill <havill@redhat.com> - 7.10.6-4
- restore ca cert bundle (#104400)
- require openssl, we want to use its ca-cert bundle

* Sun Sep  7 2003 Joe Orton <jorton@redhat.com> - 7.10.6-3
- rebuild

* Fri Sep  5 2003 Joe Orton <jorton@redhat.com> - 7.10.6-2.2
- fix to include libcurl.so

* Mon Aug 25 2003 Adrian Havill <havill@redhat.com> - 7.10.6-2.1
- bump n-v-r for RHEL

* Mon Aug 25 2003 Adrian Havill <havill@redhat.com> - 7.10.6-2
- devel subpkg needs openssl-devel as a Require (#102963)

* Mon Jul 28 2003 Adrian Havill <havill@redhat.com> - 7.10.6-1
- bumped version

* Tue Jul 01 2003 Adrian Havill <havill@redhat.com> - 7.10.5-1
- bumped version

* Wed Jun 04 2003 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Sat Apr 12 2003 Florian La Roche <Florian.LaRoche@redhat.de>
- update to 7.10.4
- adapt nousr patch

* Wed Jan 22 2003 Tim Powers <timp@redhat.com>
- rebuilt

* Tue Jan 21 2003 Joe Orton <jorton@redhat.com> - 7.9.8-4
- don't add -L/usr/lib to 'curl-config --libs' output

* Tue Jan  7 2003 Nalin Dahyabhai <nalin@redhat.com> - 7.9.8-3
- rebuild

* Wed Nov  6 2002 Joe Orton <jorton@redhat.com> - 7.9.8-2
- fix `curl-config --libs` output for libdir!=/usr/lib
- remove docs/LIBCURL from docs list; remove unpackaged libcurl.la
- libtoolize and reconf

* Mon Jul 22 2002 Trond Eivind Glomsrød <teg@redhat.com> - 7.9.8-1
- 7.9.8 (# 69473)

* Fri Jun 21 2002 Tim Powers <timp@redhat.com>
- automated rebuild

* Sun May 26 2002 Tim Powers <timp@redhat.com>
- automated rebuild

* Thu May 16 2002 Trond Eivind Glomsrød <teg@redhat.com> - 7.9.7-1
- 7.9.7

* Wed Apr 24 2002 Trond Eivind Glomsrød <teg@redhat.com> - 7.9.6-1
- 7.9.6

* Thu Mar 21 2002 Trond Eivind Glomsrød <teg@redhat.com> - 7.9.5-2
- Stop the curl-config script from printing -I/usr/include
  and -L/usr/lib (#59497)

* Fri Mar  8 2002 Trond Eivind Glomsrød <teg@redhat.com> - 7.9.5-1
- 7.9.5

* Tue Feb 26 2002 Trond Eivind Glomsrød <teg@redhat.com> - 7.9.3-2
- Rebuild

* Wed Jan 23 2002 Nalin Dahyabhai <nalin@redhat.com> - 7.9.3-1
- update to 7.9.3

* Wed Jan 09 2002 Tim Powers <timp@redhat.com> - 7.9.2-2
- automated rebuild

* Wed Jan  9 2002 Trond Eivind Glomsrød <teg@redhat.com> - 7.9.2-1
- 7.9.2

* Fri Aug 17 2001 Nalin Dahyabhai <nalin@redhat.com>
- include curl-config in curl-devel
- update to 7.8 to fix memory leak and strlcat() symbol pollution from libcurl

* Wed Jul 18 2001 Crutcher Dunnavant <crutcher@redhat.com>
- added openssl-devel build req

* Mon May 21 2001 Tim Powers <timp@redhat.com>
- built for the distro

* Tue Apr 24 2001 Jeff Johnson <jbj@redhat.com>
- upgrade to curl-7.7.2.
- enable IPv6.

* Fri Mar  2 2001 Tim Powers <timp@redhat.com>
- rebuilt against openssl-0.9.6-1

* Thu Jan  4 2001 Tim Powers <timp@redhat.com>
- fixed mising ldconfigs
- updated to 7.5.2, bug fixes

* Mon Dec 11 2000 Tim Powers <timp@redhat.com>
- updated to 7.5.1

* Mon Nov  6 2000 Tim Powers <timp@redhat.com>
- update to 7.4.1 to fix bug #20337, problems with curl -c
- not using patch anymore, it's included in the new source. Keeping
  for reference

* Fri Oct 20 2000 Nalin Dahyabhai <nalin@redhat.com>
- fix bogus req in -devel package

* Fri Oct 20 2000 Tim Powers <timp@redhat.com>
- devel package needed defattr so that root owns the files

* Mon Oct 16 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to 7.3
- apply vsprintf/vsnprintf patch from Colin Phipps via Debian

* Mon Aug 21 2000 Nalin Dahyabhai <nalin@redhat.com>
- enable SSL support
- fix packager tag
- move buildroot to %%{_tmppath}

* Tue Aug 1 2000 Tim Powers <timp@redhat.com>
- fixed vendor tag for bug #15028

* Mon Jul 24 2000 Prospector <prospector@redhat.com>
- rebuilt

* Tue Jul 11 2000 Tim Powers <timp@redhat.com>
- workaround alpha build problems with optimizations

* Mon Jul 10 2000 Tim Powers <timp@redhat.com>
- rebuilt

* Mon Jun 5 2000 Tim Powers <timp@redhat.com>
- put man pages in correct place
- use %%makeinstall

* Mon Apr 24 2000 Tim Powers <timp@redhat.com>
- updated to 6.5.2

* Wed Nov 3 1999 Tim Powers <timp@redhat.com>
- updated sources to 6.2
- gzip man page

* Mon Aug 30 1999 Tim Powers <timp@redhat.com>
- changed group

* Thu Aug 26 1999 Tim Powers <timp@redhat.com>
- changelog started
- general cleanups, changed prefix to /usr, added manpage to files section
- including in Powertools
