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
BuildRequires: chartmuseum
BuildRequires: portieris-helm
Requires: portieris-helm

%description
StarlingX Portieris Armada Helm Charts

%prep
%setup

%build
# Host a server for the charts
chartmuseum --debug --port=8879 --context-path='/charts' --storage="local" --storage-local-rootdir="." &
sleep 2
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
