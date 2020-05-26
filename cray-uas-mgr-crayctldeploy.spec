#
# RPM spec file for cray-uas-mgr deployment
# Copyright 2018 Cray Inc. All Rights Reserved.
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
