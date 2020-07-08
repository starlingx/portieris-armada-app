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
Version: 0.6.0
Release: %{tis_patch_ver}%{?_tis_dist}
License: Apache-2.0
Group: base
Packager: Wind River <info@windriver.com>
URL: unknown

Source0: portieris-%{version}.tgz
Source1: repositories.yaml
Source2: index.yaml
Source3: caCert.pem
Source4: caCert.srl
Source5: serverCert.pem
Source6: serverKey.pem

BuildArch: noarch

BuildRequires: helm
BuildRequires: chartmuseum

%description
StarlingX portieris charts

%prep
%setup -n portieris

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
mkdir $PWD/portieris/certs
cp %{SOURCE3} $PWD/portieris/certs
cp %{SOURCE4} $PWD/portieris/certs
cp %{SOURCE5} $PWD/portieris/certs
cp %{SOURCE6} $PWD/portieris/certs
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