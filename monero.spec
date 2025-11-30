Name:           monero
Version:        0.18.4.4
Release:        1%{?dist}
Summary:        Monero cryptocurrency tools (prebuilt binaries)

License:        BSD
URL:            https://www.getmonero.org/
Source0:        https://downloads.getmonero.org/cli/monero-linux-x64-v%{version}.tar.bz2

BuildArch:      x86_64
Requires(pre):  shadow-utils
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
This package provides the official prebuilt binaries from the Monero project.
It produces two subpackages: monerod (the node daemon) and monero-wallet (wallet tools).

# --- monerod subpackage ---
%package -n monerod
Summary: Monero full node daemon
Requires(pre): shadow-utils
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description -n monerod
The official monerod daemon, with a systemd unit, configuration directory,
firewalld service definition, logrotate policy, and correct ownership of its
data, log, and runtime directories via systemd-tmpfiles.
Note: the "monero" system user is created at install time and intentionally
left behind when uninstalling, to avoid accidental data loss.

# --- monero-wallet subpackage ---
%package -n monero-wallet
Summary: Monero wallet CLI and RPC tools

%description -n monero-wallet
The Monero wallet tools (CLI, RPC, blockchain utilities) provided as official prebuilt binaries.

%prep
rm -rf monero-%{version}
mkdir monero-%{version}
tar -xjf %{SOURCE0} -C monero-%{version} --strip-components=1

%build
# No compilation, we use the prebuilt binaries

%install
# --- monerod ---
mkdir -p %{buildroot}%{_bindir}
cp -a monero-%{version}/monerod %{buildroot}%{_bindir}/

mkdir -p %{buildroot}%{_unitdir}
cat > %{buildroot}%{_unitdir}/monerod.service <<'EOF'
[Unit]
Description=Monero Daemon
After=network.target

[Service]
ExecStart=/usr/bin/monerod --non-interactive \
  --config-file=/etc/monero/monerod.conf \
  --data-dir=/var/lib/monero \
  --log-file=/var/log/monero/monerod.log \
  --pidfile=/run/monero/monerod.pid
PIDFile=/run/monero/monerod.pid
RuntimeDirectory=monero
RuntimeDirectoryMode=0750
Restart=always
User=monero
Group=monero
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

# Config directory only (no default file)
mkdir -p %{buildroot}%{_sysconfdir}/monero

# Firewalld service definition
mkdir -p %{buildroot}%{_prefix}/lib/firewalld/services
cat > %{buildroot}%{_prefix}/lib/firewalld/services/monerod.xml <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<service>
  <short>Monero Daemon</short>
  <description>Monero P2P network port</description>
  <port protocol="tcp" port="18080"/>
</service>
EOF

# logrotate config
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
cat > %{buildroot}%{_sysconfdir}/logrotate.d/monerod <<'EOF'
/var/log/monero/monerod.log {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
    create 0640 monero monero
    sharedscripts
    postrotate
        /bin/systemctl kill -s HUP monerod.service >/dev/null 2>&1 || true
    endscript
}
EOF

# systemd-tmpfiles rules
mkdir -p %{buildroot}%{_tmpfilesdir}
cat > %{buildroot}%{_tmpfilesdir}/monerod.conf <<'EOF'
d /var/lib/monero 0750 monero monero -
d /var/log/monero 0750 monero monero -
EOF

# README note for admins
mkdir -p %{buildroot}%{_docdir}/monerod
cat > %{buildroot}%{_docdir}/monerod/README.user <<'EOF'
The monerod package creates a dedicated system user "monero" to run the daemon.
This user and group are intentionally left behind when uninstalling the package,
to avoid accidental data loss in /var/lib/monero or /var/log/monero.

If you wish to fully remove the account, run:
  sudo systemctl stop monerod
  sudo userdel -r monero
  sudo groupdel monero
EOF

# --- monero-wallet ---
cp -a monero-%{version}/monero-wallet-cli monero-%{version}/monero-wallet-rpc \
      monero-%{version}/monero-blockchain-* monero-%{version}/monero-gen-* \
      %{buildroot}%{_bindir}/

%pre -n monerod
# Ensure the service account exists BEFORE tmpfiles tries to set ownership
getent group monero >/dev/null || groupadd -r monero
getent passwd monero >/dev/null || \
    useradd -r -g monero -d /var/lib/monero -s /sbin/nologin \
    -c "Monero daemon user" monero

%post -n monerod
# Create directories now (and again at boot) with correct ownership via tmpfiles
/usr/bin/systemd-tmpfiles --create %{_tmpfilesdir}/monerod.conf || true
%systemd_post monerod.service

%preun -n monerod
%systemd_preun monerod.service

%postun -n monerod
%systemd_postun_with_restart monerod.service

%files -n monerod
%license monero-%{version}/LICENSE
%doc monero-%{version}/README.md
%doc %{_docdir}/monerod/README.user
%{_bindir}/monerod
%{_unitdir}/monerod.service
%dir %{_sysconfdir}/monero
%{_prefix}/lib/firewalld/services/monerod.xml
%config(noreplace) %{_sysconfdir}/logrotate.d/monerod
%{_tmpfilesdir}/monerod.conf

%files -n monero-wallet
%license monero-%{version}/LICENSE
%doc monero-%{version}/README.md
%{_bindir}/monero-wallet-cli
%{_bindir}/monero-wallet-rpc
%{_bindir}/monero-blockchain-*
%{_bindir}/monero-gen-*

%changelog
* Sun Nov 30 2025 Frederic <frederic@bousquet.eu> - 0.18.4.4-1
- Package official Monero binaries into two subpackages: monerod and monero-wallet
