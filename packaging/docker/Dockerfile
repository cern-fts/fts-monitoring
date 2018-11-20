FROM centos:7
MAINTAINER CERN

# Add EPEL repos
ADD  http://linuxsoft.cern.ch/epel/epel-release-latest-7.noarch.rpm  /tmp/epel-release-7.noarch.rpm
RUN  yum localinstall /tmp/epel-release-7.noarch.rpm -y \
        && /usr/bin/yum --enablerepo=*-testing clean all \
        && rm /tmp/epel-release-7.noarch.rpm \
        && rm -rf /var/cache/yum

# add FTS repo
ARG ftsrepo=http://fts-repo.web.cern.ch/fts-repo/fts3-continuous-el7.repo
ADD $ftsrepo /etc/yum.repos.d/fts.repo

#add DMC repo
ARG dmcrepo=http://dmc-repo.web.cern.ch/dmc-repo/dmc-ci-el7.repo
ADD $dmcrepo /etc/yum.repos.d/dmc.repo

RUN /usr/bin/yum clean all

#install fts packages
RUN /usr/bin/yum install -y fts-monitoring fts-monitoring-selinux mod_ssl gridsite
RUN /usr/bin/yum install -y voms-config-wlcg  voms-config-vo-dteam

#add user
RUN useradd fts3
RUN usermod -a -G fts3 apache

#expose ports

EXPOSE 8449

CMD ["/usr/sbin/apachectl","-DFOREGROUND"]

