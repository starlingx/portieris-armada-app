# Application tunables (maps to metadata)
%global app_name stx-portieris
%global helm_repo starlingx
#%global helm_folder  /usr/lib/helm
#%global armada_folder  /usr/lib/armada
#%global app_folder  /usr/local/share/applications/helm

# Install location
%global app_folder /usr/local/share/applications/helm

# Build variables
%global helm_folder /usr/lib/helm

Summary: StarlingX portieris Helm charts
Name: portieris-helm
Version: 0.7.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: Wind River <info@windriver.com>
URL: unknown

Source0: portieris-%{version}.tgz
Source1: repositories.yaml
Source2: index.yaml

BuildArch: noarch

Patch01: 0001-Squash-required-portieris-fixes.patch

BuildRequires: helm
BuildRequires: chartmuseum

%description
StarlingX portieris charts

%prep
%setup -n portieris
%patch01 -p1

%build
# Host a server for the charts
chartmuseum --debug --port=8879 --context-path='/charts' --storage="local" --storage-local-rootdir="." &
sleep 2
helm repo add local http://localhost:8879/charts


# Create a chart tarball compliant with sysinv kube-app.py
%define app_staging %{_builddir}/staging
%define app_tarball portieris-%{version}.tgz

# Make the charts. These produce a tgz file
make helm.package
cd %{_builddir}/portieris
tar -xvf %{app_tarball}
tar -zcf %{app_tarball} portieris
cd -

# Terminate helm server (the last backgrounded task)
kill %1

%install
install -d -m 755 ${RPM_BUILD_ROOT}%{helm_folder}
install -p -D -m 755 %{_builddir}/portieris/%{app_tarball} ${RPM_BUILD_ROOT}%{helm_folder}

%files
%defattr(-,root,root,-)
%{helm_folder}/*
