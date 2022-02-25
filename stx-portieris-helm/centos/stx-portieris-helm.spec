# Application tunables (maps to metadata)
%global app_name portieris
%global helm_repo stx-platform
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

# psp-rolebinding source from stx/helm-charts/psp-rolebinding
# plugins source from stx/portieris-armada-app/python-k8sapp-portieris
# portieris-certs sources is in SRC_DIR already

BuildArch: noarch

BuildRequires: helm
BuildRequires: chartmuseum
BuildRequires: portieris-helm
BuildRequires: python-k8sapp-portieris
BuildRequires: python-k8sapp-portieris-wheels

%description
StarlingX Portieris Armada Helm Charts

%package fluxcd
Summary: StarlingX Portieris Application FluxCD Helm Charts
Group: base
License: Apache-2.0

%description fluxcd
StarlingX Portieris Application FluxCD Helm Charts

%prep
%setup

%build
# Host a server for the charts
chartmuseum --debug --port=8879 --context-path='/charts' --storage="local" --storage-local-rootdir="." &
sleep 2
helm repo add local http://localhost:8879/charts

# Make the charts. These produce a tgz file
cd helm-charts
helm lint portieris-certs
helm package portieris-certs

# psp-rolebinding source is copied by the function of build_srpm.data
# COPY_LIST_TO_TAR
make psp-rolebinding

# switch back to source root
cd -

# terminate helm server (the last backgrounded task)
kill %1

# Create a chart tarball compliant with sysinv kube-app.py
%define app_staging %{_builddir}/staging
%define app_tarball_armada %{app_name}-%{version}-%{tis_patch_ver}.tgz
%define app_tarball_fluxcd %{app_name}-fluxcd-%{version}-%{tis_patch_ver}.tgz

# Setup staging
mkdir -p %{app_staging}
cp files/metadata.yaml %{app_staging}
cp manifests/manifest.yaml %{app_staging}
mkdir -p %{app_staging}/charts

# copy portieris-certs, psp-rolebinding charts
cp helm-charts/*.tgz %{app_staging}/charts

# copy portieris-helm chart
cp %{helm_folder}/portieris*.tgz %{app_staging}/charts

# Copy the plugins: installed in the buildroot
mkdir -p %{app_staging}/plugins
cp /plugins/%{app_name}/*.whl %{app_staging}/plugins

# Populate metadata
cd %{app_staging}
sed -i 's/@APP_NAME@/%{app_name}/g' %{app_staging}/metadata.yaml
sed -i 's/@APP_VERSION@/%{version}-%{tis_patch_ver}/g' %{app_staging}/metadata.yaml
sed -i 's/@HELM_REPO@/%{helm_repo}/g' %{app_staging}/metadata.yaml

# calculate checksum of all files in app_staging
find . -type f ! -name '*.md5' -print0 | xargs -0 md5sum > checksum.md5
tar -zcf %{_builddir}/%{app_tarball_armada} -C %{app_staging}/ .

# switch back to source root
cd -

# Prepare app_staging for fluxcd package
rm -f %{app_staging}/manifest.yaml

cp -R fluxcd-manifests %{app_staging}/

# calculate checksum of all files in app_staging
cd %{app_staging}
find . -type f ! -name '*.md5' -print0 | xargs -0 md5sum > checksum.md5
# package fluxcd app
tar -zcf %{_builddir}/%{app_tarball_fluxcd} -C %{app_staging}/ .

# switch back to source root
cd -

# Cleanup staging
rm -fr %{app_staging}

%install
install -d -m 755 %{buildroot}/%{app_folder}
install -p -D -m 755 %{_builddir}/%{app_tarball_armada} %{buildroot}/%{app_folder}
install -p -D -m 755 %{_builddir}/%{app_tarball_fluxcd} %{buildroot}/%{app_folder}

%files
%defattr(-,root,root,-)
%{app_folder}/%{app_tarball_armada}

%files fluxcd
%defattr(-,root,root,-)
%{app_folder}/%{app_tarball_fluxcd}
