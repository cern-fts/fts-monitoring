#!/usr/bin/env bash
set -e

function print_info {
  printf "======================\n"
  printf "Distribution:\t%s\n" "${DIST}"
  printf "Branch:\t\t%s\n" "${BRANCH}"
  printf "Release:\t%s\n" "${RELEASE}"
  printf "======================\n"
}

TIMESTAMP=$(git log -1 --format="%at" | xargs -I{} date -d @{} +%y%m%d%H%M)
GITREF=`git rev-parse --short=7 HEAD`
RELEASE=r${TIMESTAMP}git${GITREF}

if [[ -z ${BRANCH} ]]; then
  BRANCH=`git name-rev $GITREF --name-only`
else
  printf "Using environment set variable BRANCH=%s\n" "${BRANCH}"
fi

if [[ $BRANCH =~ ^(tags/)?(v)[.0-9]+(-(rc)?([0-9]+))?(\^0)?$ ]]; then
  RELEASE="${BASH_REMATCH[4]}${BASH_REMATCH[5]}"
fi

DIST=$(rpm --eval "%{dist}" | cut -d. -f2)
print_info

RPMBUILD=${PWD}/build
SRPMS=${RPMBUILD}/SRPMS

cd packaging/
make srpm RELEASE=${RELEASE} RPMBUILD=${RPMBUILD} SRPMS=${SRPMS}

if [[ -f /usr/bin/dnf ]]; then
  dnf install -y epel-release || true
  dnf builddep -y ${SRPMS}/*
else
  yum-builddep -y ${SRPMS}/*
fi

rpmbuild --rebuild --define="_topdir ${RPMBUILD}" ${SRPMS}/*
