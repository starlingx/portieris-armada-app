# Application tunables (maps to metadata)
%global app_name stx-portieris
%global helm_repo starlingx
%global helm_folder  /usr/lib/helm
%global armada_folder  /usr/lib/armada
%global app_folder  /usr/local/share/applications/helm
%global toolkit_version 0.1.0
%global helmchart_version 0.1.0


Summary: StarlingX Portieris Armada Helm Charts
Name: stx-portieris-helm
Version: 1.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: Wind River <info@windriver.com>
URL: unknown

Source0: %{name}-%{version}.tar.gz

BuildArch: noarch

BuildRequires: helm
BuildRequires: portieris-helm
Requires: portieris-helm

%description
StarlingX Portieris Armada Helm Charts

%prep
%setup

%build
# initialize helm and build the toolkit
# helm init --client-only does not work if there is no networking
# The following commands do essentially the same as: helm init
%define helm_home  %{getenv:HOME}/.helm
mkdir  %{helm_home}
mkdir  %{helm_home}/repository
mkdir  %{helm_home}/repository/cache
mkdir  %{helm_home}/repository/local
mkdir  %{helm_home}/plugins
mkdir  %{helm_home}/starters
mkdir  %{helm_home}/cache
mkdir  %{helm_home}/cache/archive

# Stage a repository file that only has a local repo
cp files/repositories.yaml %{helm_home}/repository/repositories.yaml

# Stage a local repo index that can be updated by the build
cp files/index.yaml %{helm_home}/repository/local/index.yaml

# Host a server for the charts
helm serve --repo-path . &
helm repo rm local
helm repo add local http://localhost:8879/charts

# terminate helm server (the last backgrounded task)
kill %1

# Create a chart tarball compliant with sysinv kube-app.py
%define app_staging %{_builddir}/staging
%define app_tarball %{app_name}-%{version}-%{tis_patch_ver}.tgz

# Setup staging
mkdir -p %{app_staging}
cp files/metadata.yaml %{app_staging}
cp manifests/*.yaml %{app_staging}
mkdir -p %{app_staging}/charts
#cp helm-charts/*.tgz %{app_staging}/charts
cp %{helm_folder}/portieris*.tgz %{app_staging}/charts
cd %{app_staging}

# Populate metadata
sed -i 's/@APP_NAME@/%{app_name}/g' %{app_staging}/metadata.yaml
sed -i 's/@APP_VERSION@/%{version}-%{tis_patch_ver}/g' %{app_staging}/metadata.yaml
sed -i 's/@HELM_REPO@/%{helm_repo}/g' %{app_staging}/metadata.yaml

# package it up
find . -type f ! -name '*.md5' -print0 | xargs -0 md5sum > checksum.md5
tar -zcf %{_builddir}/%{app_tarball} -C %{app_staging}/ .

# Cleanup staging
rm -fr %{app_staging}

%install
install -d -m 755 %{buildroot}/%{app_folder}
install -p -D -m 755 %{_builddir}/%{app_tarball} %{buildroot}/%{app_folder}
install -d -m 755 %{buildroot}/%{helm_folder}
install -p -D -m 755 %{helm_folder}/portieris*.tgz %{buildroot}/%{helm_folder}
install -d -m 755 %{buildroot}/%{armada_folder}
install -p -D -m 755 manifests/*.yaml %{buildroot}/%{armada_folder}

%files
%defattr(-,root,root,-)
%{helm_folder}/*
%{armada_folder}/*
%{app_folder}/*
