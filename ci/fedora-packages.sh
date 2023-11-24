#!/usr/bin/env bash
set -e

if [[ -f /usr/bin/dnf ]]; then
  dnf install -y dnf-plugins-core git rpm-build make tree which
else
  yum install -y yum-utils git rpm-build make tree which epel-rpm-macros
fi
