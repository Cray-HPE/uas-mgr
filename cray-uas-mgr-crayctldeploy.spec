#
# RPM spec file for cray-uas-mgr deployment
# MIT License
#
# (C) Copyright [2020] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
%define crayctl_dir /opt/cray/crayctl
%define ansible_dir %{crayctl_dir}/ansible_framework
%define test_dir /opt/cray/tests

Name: cray-uas-mgr-crayctldeploy
License: Cray Software License Agreement
Summary: User Access Service Manager Deployment
Version: %(cat .version)
Release: %(echo ${BUILD_METADATA})
Source: %{name}-%{version}.tar.bz2
Vendor: Cray Inc.
Group: Productivity/Clustering/Computing

BuildRequires: cme-premium-cf-crayctldeploy-buildmacro

Requires: cme-premium-cf-crayctldeploy
Requires: cray-crayctl
Requires: sms-crayctldeploy
Requires: kubernetes-crayctldeploy
Requires: cray-ct-driver-crayctldeploy
Requires: python3-PyYAML

%description
This package provides an ansible role and playbook for deploying the User Access
Service Manager and User Access Service ID to a Cray Shasta system.

%files
%dir %{crayctl_dir}
%{ansible_dir}
%{test_dir}
%{cme_premium_plays_dir}
%{cme_premium_roles_dir}

%prep
%setup -q

%build

%install
# Install ansible files
mkdir -p %{buildroot}%{crayctl_dir}
cp -R ansible %{buildroot}%{ansible_dir}
cp -R tests %{buildroot}%{test_dir}

install -D -m 644 ansible/customer_runbooks/uas-mgr.yml %{buildroot}%{cme_premium_plays_dir}/uas-mgr.yml
mkdir -p %{buildroot}%{cme_premium_roles_dir}
cp -R ansible/roles/cray_* %{buildroot}%{cme_premium_roles_dir}

%changelog
