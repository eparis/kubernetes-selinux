%define selinuxtype	targeted
%define modulenames kubernetes etcd

%define interface_dir	%{_datadir}/selinux/devel/include/contrib
%define policy_dir	%{_datadir}/selinux/packages

%define relabel_kube_files() \
	restorecon -R /usr/bin/kube-apiserver; \
	restorecon -R /usr/bin/kube-controller-manager; \
	restorecon -R /usr/bin/kube-scheduler; \
	restorecon -R /usr/bin/kubelet; \
	restorecon -R /usr/bin/kube-proxy; \
	restorecon -R /usr/lib/systemd/system/kube-apiserver.service; \
	restorecon -R /usr/lib/systemd/system/kube-controller-manager.service; \
	restorecon -R /usr/lib/systemd/system/kube-scheduler.service; \
	restorecon -R /usr/lib/systemd/system/kubelet.service; \
	restorecon -R /usr/lib/systemd/system/kube-proxy.service; \
	restorecon -R /var/lib/kubelet; \

%define relabel_etcd_files() \
	restorecon -R /usr/bin/etcd; \
	restorecon -R /usr/lib/systemd/system/etcd.service; \
	restorecon -R /var/lib/etcd;

# We do this in post install and post uninstall phases
%define relabel_files() \
	%relabel_kube_files \
	%relabel_etcd_files

# Version of SELinux we were using
%define selinux_policyver 3.13.1-72.fc21

# Package information
Name:			kubernetes-selinux
Version:		0.1.0
Release:		1%{?dist}
License:		GPLv2
Group:			System Environment/Base
Summary:		SELinux Policies for Kubernetes
BuildArch:		noarch
URL:			https://github.com/selinux-policy/selinux-policy
Requires:		policycoreutils, libselinux-utils
Requires(post):		selinux-policy-base >= %{selinux_policyver}, selinux-policy-targeted >= %{selinux_policyver}, policycoreutils
Requires(postun):	policycoreutils
BuildRequires:		selinux-policy selinux-policy-devel

Source0:	kubernetes.te
Source1:	kubernetes.fc
Source2:	kubernetes.if
Source3:	etcd.te
Source4:	etcd.fc
Source5:	etcd.if

%description
SELinux policy modules for Kubernetes, etcd, and maybe cadvisor
	
%prep
cp %{SOURCE0} .
cp %{SOURCE1} .
cp %{SOURCE2} .
cp %{SOURCE3} .
cp %{SOURCE4} .
cp %{SOURCE5} .

%build
for modulename in %{modulenames}; do
    make -f /usr/share/selinux/devel/Makefile ${modulename}.pp
done

%install

install -d %{buildroot}%{interface_dir}
install -d %{buildroot}%{policy_dir}

for modulename in %{modulenames}; do
    # Install SELinux interface
    install -p -m 644 ${modulename}.if %{buildroot}%{interface_dir}
    # Install policy module
    install -m 0644 ${modulename}.pp %{buildroot}%{policy_dir}
done

%post
#
# Install kubernetes module in a single transaction
#

for modulename in %{modulenames}; do
    %{_sbindir}/semodule -n -s %{selinuxtype} -i %{policy_dir}/${modulename}.pp
done

semanage port -n -m -t kubernetes_port_t -p tcp -r s0 8080
semanage port -n -m -t kubernetes_port_t -p tcp -r s0 10250-10252
semanage port -n -m -t kubernetes_port_t -p tcp -r s0 4001 #should be etcd_port_t
semanage port -n -m -t kubernetes_port_t -p tcp -r s0 7001 #should be etcd_port_t

if %{_sbindir}/selinuxenabled ; then
	%{_sbindir}/load_policy
	%relabel_files
fi


%postun
if [ $1 -eq 0 ]; then
	for modulename in %{modulenames}; do
	    %{_sbindir}/semodule -n -r ${modulename} || :
	done
	if %{_sbindir}/selinuxenabled ; then
		%{_sbindir}/load_policy
		%relabel_files
	fi
fi

%files
%attr(0600,root,root) %{policy_dir}/kubernetes.pp
%{interface_dir}/kubernetes.if
%attr(0600,root,root) %{policy_dir}/etcd.pp
%{interface_dir}/etcd.if

%changelog
* Mon Feb 11 2013 Miroslav Grepl <mgrepl@redhat.com> - 0.1.0-1
- Initial kubernetes SELinux policy
