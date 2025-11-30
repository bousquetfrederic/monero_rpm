A SPEC file to build a RPM package for the monero daemon and for the wallet.
The daemon can be started as a systemd service.
A firewalld service is created in order to open port 18080.

To build as root (tested on Rocky 10):

```
dnf install rpmdevtools git wget
rpmdev-setuptree
```

Put monero.spec in rpmbuild/SPECS/

```
wget https://downloads.getmonero.org/cli/monero-linux-x64-v0.18.4.4.tar.bz2 -P rpmbuild/SOURCES/
rpmbuild -ba rpmbuild/SPECS/monero.spec
```

To configure the firewall (optional), configure the node and start it:

```
firewall-cmd --permanent --add-service monero
```

Put monerod.conf in /etc/monero/

```
systemctl enable --now monerod
```
