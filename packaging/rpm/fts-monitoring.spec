Name:       fts-monitoring
Version:    3.14.1
Release:    1%{?dist}
BuildArch:  noarch
Summary:    FTS3 Web Application for monitoring
Group:      Applications/Internet
License:    ASL 2.0
URL:        https://fts.web.cern.ch/
# wget https://gitlab.cern.ch/fts/fts-monitoring/repository/archive.tar.gz?ref=v3.14.1 -O fts-monitoring-3.14.1.tar.gz
Source0:    %{name}-%{version}.tar.gz

Requires:   httpd
Requires:   mod_ssl
Requires:   python3
Requires:   python%{python3_pkgversion}-mysqlclient
Requires:   python%{python3_pkgversion}-decorator
Requires:   python%{python3_pkgversion}-django
Requires:   python%{python3_pkgversion}-mod_wsgi

%description
FTS v3 web application for monitoring,
it gives a detailed view of the current state of FTS
including the queue with submitted transfer-jobs,
the active, failed and finished transfers, as well
as some statistics (e.g. success rate)

%post
service httpd condrestart

%package selinux
Summary:        SELinux support for fts-monitoring
Group:          Applications/Internet
Requires:       fts-monitoring = %{version}-%{release}
Requires:       policycoreutils-python-utils

%description selinux
This package labels port 8449, used by fts-monitoring, as http_port_t,
so Apache can bind to it.

%post selinux
if [ $1 -gt 0 ] ; then # First install
    semanage port -a -t http_port_t -p tcp 8449
    setsebool -P httpd_can_network_connect=1
    semanage fcontext -a -t httpd_log_t "/var/log/fts3web(/.*)?"
    restorecon -R /var/log/fts3web
    libnzz="/usr/lib64/oracle/11.2.0.3.0/client/lib64/libnnz11.so"
    if [ -f "$libnzz" ]; then
        execstack -c "$libnzz"
    fi
fi

%preun selinux
if [ $1 -eq 0 ] ; then # Final removal
    semanage port -d -t http_port_t -p tcp 8449
    setsebool -P httpd_can_network_connect=0
    libnzz="/usr/lib64/oracle/11.2.0.3.0/client/lib64/libnnz11.so"
    if [ -f "$libnzz" ]; then
        execstack -s "$libnzz"
    fi
fi

%prep
%setup -q

%build
# Make sure the specfile version matches "src/settings/version.py"
ftsmon_settings_ver=`grep "^VERSION" src/settings/version.py | grep -o [0-9.]*`
ftsmon_specfile_ver=`expr "%{version}" : '\([0-9]*\\.[0-9]*\\.[0-9]*\)'`
if [ "$ftsmon_settings_ver" != "$ftsmon_specfile_ver" ]; then
    echo "The src/settings/version.py does not match the specfile version! ($ftsmon_settings_ver != $ftsmon_specfile_ver)"
    exit 1
fi

%install
shopt -s extglob
mkdir -p %{buildroot}%{_datadir}/fts3web/
mkdir -p %{buildroot}%{_sysconfdir}/fts3web/
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d/
mkdir -p %{buildroot}%{_var}/log/fts3web
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d/
cp -r -p src/* %{buildroot}%{_datadir}/fts3web/
cp -r -p conf/fts3web %{buildroot}%{_sysconfdir}
cp conf/logrotate/fts3web.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/fts3web
install -m 644 conf/httpd.conf.d/ftsmon.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/

# Create fts3 user and group
%pre
getent group fts3 >/dev/null || groupadd -r fts3
getent passwd fts3 >/dev/null && usermod -a -G apache fts3
getent passwd fts3 >/dev/null || \
    useradd -r -m -g fts3 -G apache -d /var/log/fts3 -s /sbin/nologin \
    -c "File Transfer Service user" fts3
exit 0

%files
%{_datadir}/fts3web
%config(noreplace) %{_sysconfdir}/httpd/conf.d/ftsmon.conf
%config(noreplace) %dir %{_sysconfdir}/fts3web/
%config(noreplace) %attr(640, root, apache) %{_sysconfdir}/fts3web/fts3web.ini
%config(noreplace) %{_sysconfdir}/logrotate.d/fts3web
%attr(0755,fts3,fts3) /var/log/fts3web
%doc LICENSE

%files selinux

%changelog
* Tue Jun 17 2025 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.14.1-1
- New upstream release
- Address exploit in "/linkinfo" endpoint

* Wed Apr 30 2025 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.14.0-1
- FTS v3.14 Token Release

* Wed Apr 02 2025 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.13.2-1
- New upstream release
- Configurable display of the "/config/audit" endpoint

* Fri Jan 24 2025 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.13.1-1
- New upstream release
- Configurable display of the "/config/gfal2" endpoint

* Thu May 30 2024 Mihai Patrascoiu <mihai.patrascoiu@cern.ch> - 3.13.0-1
- Alma9 release

* Tue Aug 08 2023 Joao Lopes <batistal@cern.ch> - 3.12.2-1
- New upstream release

* Wed Jan 25 2023 Joao Lopes <batistal@cern.ch> - 3.12.1-1
- New upstream release
- Add configurable timeout to stop long running database queries

* Fri Jul 15 2022 Joao Lopes <batistal@cern.ch> - 3.12.0-1
- New upstream release
- Migration to Python3 and newer Django version
- New feature to display link and storage limits information

* Wed Sep 22 2021 Joao Lopes <batistal@cern.ch> - 3.11.0-1
- New upstream release

* Mon Dec 07 2020 Mihai Patrascoiu <mipatras@cern.ch> - 3.10.0-1
- New upstream release
- Support for Archive Monitoring

* Tue Aug 27 2019 Andrea Manzi <amanzi@cern.ch> - 3.9.1-1
- New upstream release

* Wed May 8 2019 Andrea Manzi <amanzi@cern.ch> - 3.9.0-1
- Align package version to fts minor release

* Wed Feb 20 2019 Andrea Manzi <amanzi@cern.ch> - 3.8.3-1
- Update for new upstream release

* Mon Sep 24 2018 Andrea Manzi <amanzi@cern.ch> - 3.8.0-1
- Update for new upstream release

* Thu Jun 07 2018 Andrea Manzi <amanzi@cern.ch> - 3.7.10-1
- Update for new upstream release

* Mon Sep 07 2015 Alejandro Alarez Ayllon <aalvarez@cern.ch> - 3.3.0-1
- Update for new upstream release

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.32-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Fri Mar 06 2015 Alejandro Alarez Ayllon <aalvarez@cern.ch> - 3.2.32-1
- Update for new upstream release

* Wed Nov 26 2014 Alejandro Alarez Ayllon <aalvarez@cern.ch> - 3.2.30-1
- Update for new upstream release

* Mon May 12 2014 Michal Simon <michal.simon@cern.ch> - 3.2.26.2-2
- Update for new upstream release

* Mon May 12 2014 Michal Simon <michal.simon@cern.ch> - 3.2.26-1
- Update for new upstream release

* Tue Oct 08 2013 Alejandro Alvarez <aalvarez@cern.ch> - 3.1.27-1
- Added selinux rpm

* Mon Sep 02 2013 Michal Simon <michal.simon@cern.ch> - 3.1.1-2
- since it is a noarch package removing '%{?_isa}' sufix

* Wed Aug 28 2013 Michal Simon <michal.simon@cern.ch> - 3.1.1-1
- replacing '--no-preserve=ownership'
- python macros have been removed
- comments regarding svn have been removed
- '%{_builddir}/%{name}-%{version}/' prefix is not used anymore
- more detailed description

* Tue Apr 30 2013 Michal Simon <michal.simon@cern.ch> - 3.1.0-1
- First EPEL release
