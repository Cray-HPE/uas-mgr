#
# RPM spec file for cray-uas-mgr deployment
# Copyright 2018 Cray Inc. All Rights Reserved.
#
%define ansible_dir /opt/cray/crayctl/ansible_framework

Name: cray-uas-mgr-crayctldeploy
License: Cray Software License Agreement
Summary: User Access Service Manager Deployment
Version: 0.9.0
Release: 1
Source: %{name}-%{version}.tar.bz2
Vendor: Cray Inc.
Group: Productivity/Clustering/Computing

%description
This package provides an ansible role and playbook for deploying the User Access
Service Manager and User Access Service ID to a Cray Shasta system.

Requires: cray-crayctl
Requires: sms-crayctldeploy
Requires: kubernetes-crayctldeploy

%files
%dir /opt/cray/crayctl
%{ansible_dir}
%dir %{ansible_dir}/customer_runbooks

%prep
%setup -q

%build

%install

# Install ansible files
install -m 755 -d %{buildroot}%{ansible_dir}
install -m 755 -d %{buildroot}%{ansible_dir}/customer_runbooks
cp -R ansible/roles %{buildroot}%{ansible_dir}/
cp -R ansible/main %{buildroot}%{ansible_dir}/
cp -R ansible/roles/cray_uas_mgr_localize/files/uas-mgr.yml %{buildroot}%{ansible_dir}/customer_runbooks/

%changelog
