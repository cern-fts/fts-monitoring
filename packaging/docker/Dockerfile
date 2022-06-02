#
# FTS-Monitoring Docker file
#

FROM centos:7
LABEL maintainer="FTS Team, fts-support@cern.ch, CERN 2021"

# Add EPEL repos
ADD https://linuxsoft.cern.ch/epel/epel-release-latest-7.noarch.rpm /tmp/epel-release-7.noarch.rpm
RUN yum localinstall /tmp/epel-release-7.noarch.rpm -y \
        && /usr/bin/yum --enablerepo=*-testing clean all \
        && rm /tmp/epel-release-7.noarch.rpm \
        && rm -rf /var/cache/yum

# Add FTS repo
ARG ftsrepo=https://fts-repo.web.cern.ch/fts-repo/fts3-continuous-el7.repo
ADD $ftsrepo /etc/yum.repos.d/fts.repo

# Add DMC repo
ARG dmcrepo=https://dmc-repo.web.cern.ch/dmc-repo/dmc-ci-el7.repo
ADD $dmcrepo /etc/yum.repos.d/dmc.repo
RUN yum clean all

# Install FTS-Monitoring packages
RUN yum install -y fts-monitoring fts-monitoring-selinux gridsite

# Install VOMS packages
RUN yum install -y voms-config-wlcg voms-config-vo-dteam

# Add fts3 user
RUN useradd fts3
RUN usermod -a -G fts3 apache

# Expose ports
EXPOSE 8449

CMD ["/usr/sbin/apachectl", "-DFOREGROUND"]
