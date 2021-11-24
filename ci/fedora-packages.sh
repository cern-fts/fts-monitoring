#!/usr/bin/env bash
set -e

if [[ -f /usr/bin/dnf ]]; then
  dnf install -y dnf-plugins-core git rpm-build tree which python2
else
  yum install -y yum-utils git rpm-build tree which python2
fi
