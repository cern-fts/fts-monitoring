Summary:    FTS3 Web Application for monitoring
Name:       fts-monitoring
Version:    3.6.0
Release:    1%{?dist}
URL:        http://fts3-service.web.cern.ch
License:    ASL 2.0
Group:      Applications/Internet
BuildArch:  noarch
# wget https://gitlab.cern.ch/fts/fts-monitoring/repository/archive.tar.gz?ref=v3.6.0 -O fts-monitoring-3.6.0.tar.gz
Source0: %{name}-%{version}.tar.gz

BuildRequires:  python2-devel

#Requires:  cx_Oracle
Requires:   MySQL-python
Requires:   Django >= 1.3.7
Requires:   httpd
Requires:   mod_ssl
Requires:   mod_wsgi
Requires:   python
Requires:   python-decorator

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

%description selinux
This package labels port 8449, used by fts-monitoring, as http_port_t,
so Apache can bind to it.

%post selinux
if [ $1 -gt 0 ] ; then # First install
    semanage port -a -t http_port_t -p tcp 8449
    setsebool -P httpd_can_network_connect=1 
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

%install
shopt -s extglob
mkdir -p %{buildroot}%{_datadir}/fts3web/
mkdir -p %{buildroot}%{_sysconfdir}/fts3web/
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d/
cp -r -p src/* %{buildroot}%{_datadir}/fts3web/
cp -r -p conf/fts3web %{buildroot}%{_sysconfdir}
install -m 644 conf/httpd.conf.d/ftsmon.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/

%files
%{_datadir}/fts3web
%config(noreplace) %{_sysconfdir}/httpd/conf.d/ftsmon.conf
%config(noreplace) %dir %{_sysconfdir}/fts3web/
%config(noreplace) %attr(640, root, apache) %{_sysconfdir}/fts3web/fts3web.ini
%doc LICENSE

%files selinux

%changelog
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

