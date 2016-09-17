Still a work in progress.
Some features are missing

Missing values: PostgreSQL and certbot
install_nextcloud
=========

This role installs an all in one nextcloud server. Database, web services will be on the same host.

Strenghtened permissions and ownership following Nextcloud recommandations.

Requirements
------------

Ansible 2.0

Role Variables
--------------
Settable variables and their default
```YAML
# [CONFIG]
nextcloud_version: 10.0.0 # nextcloud version you want to install
nextcloud_trusted_domain: ansible_default_ipv4.address # the first domain you will use to access the nextcloud server
nextcloud_websrv: "apache" # the http server nextcloud will run on. values are: apache or nginx
nextcloud_webroot: "/opt/nextcloud" # nextcloud installation directory. Warning: only the parent directory must exist on the first run.
nextcloud_data_dir: "{{ nextcloud_webroot }}/data" # nextcloud data directory
nextcloud_admin_name: "admin" # nextcloud admin login
# nextcloud_admin_pwd: "secret" # nextcloud admin password. not set by default, a ramdom password will be generated.
nextcloud_dl_url: "https://download.nextcloud.com/server/releases" # nextcloud repository

# [DATABASE]
nextcloud_db_backend: "mysql" # database backend used by nextcloud. values are: "mysql"/"mariadb" or "PostgreSQL"
nextcloud_db_name: "nextcloud" # database name.
nextcloud_db_admin: "ncadmin" # database user login
# nextcloud_db_pwd: "secret" # database user password. not set by default, a ramdom password will be generated.

# [TLS]
nextcloud_tls_enforce: true # force http trafic to https
nextcloud_tls_cert_method: "self-signed" # method for providing certificates:
# - self-signed: generate a one year self-signed certificate for the trusted domain on the remote host in /etc/ssl.
# - certbot: Use cerbot/letsencrypt to provide a signed certificate for the trusted domain.
# - signed: copy provided signed certificate for the trusted domain to the remote host or in /etc/ssl by default.
# - installed: if the certificate for the trusted domain is already on the remote host specify its location.
# nextcloud_tls_src_cert: /path/to/cert # local path to the certificate's key. used by "signed" (mandatory)
# nextcloud_tls_src_cert_key: /path/to/cert/key # local path to the certificate. used by "signed" (mandatory)
# the following should be absolute path:
# nextcloud_tls_cert: /path/to/cert # remote path to the certificate's key. used by "signed" (opt) and "installed" (mandatory)
# nextcloud_tls_cert_key: /path/to/cert/key # remote path to the certificate. used by "signed" (opt) and "installed" (mandatory)

# [SYSTEM]
websrv_user: "www-data" # system user for the http server
websrv_group: "www-data" # system group for the http server
#mysql_root_pwd: "secret" # root password for the mysql server !!only if necessary!!
```
Dependencies
------------

none

Example Playbook
----------------

Some user want to install a new nextcloud server on an existing host with already some services running like mysql and nginx. But he do not want to have redondant services on its host

He can run the role with the following values to install nextcloud accordingly to its server constraints.
```YAML
---
- hosts: servers
  roles:
   - role: install_nextcloud
     nextcloud_trusted_domain: "cloud.example.tld"
     nextcloud_websrv: "nginx"
     nextcloud_admin_pwd: "secret007"
     nextcloud_webroot: "/var/www/nextcloud/"
     nextcloud_data_dir: "/var/ncdata"
     nextcloud_db_pwd: "secretagency"
     mysql_root_pwd: "42h2g2"
```
License
-------

BSD

