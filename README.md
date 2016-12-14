[![Build Status](https://travis-ci.org/aalaesar/install_nextcloud.svg?branch=master)](https://travis-ci.org/aalaesar/install_nextcloud)
# install_nextcloud

This role installs and configures an Nextcloud instance for a debian/Ubuntu server.

The role's main actions are:
- [x] Packages dependencies installation.
- [x] Database configuration (if located on the same host).
- [x] Strengthened files permissions and ownership following Nextcloud recommendations.
- [x] Web server configuration.
- [x] Strengthened TLS configuration following _Mozilla SSL Configuration Generator_, intermediate profile.

## Requirements
### Ansible version
Ansible 2.0
### Setup module:
The role uses facts gathered by Ansible on the remote host. If you disable the Setup module in your playbook, the role will not work properly.
### Root access
This role requires root access, so either configure it in your inventory files, run it in a playbook with a global `become: yes` or invoke the role in your playbook like:
> playbook.yml:
```YAML
- hosts: dnsserver
  roles:
    - role: aalaesar.install_nextcloud
      become: yes
```

## Role Variables

Role's variables (and their default value):

### Installation configuration
> Source location will be calculated following channel, version and branch values.

```YAML
nextcloud_channel: "releases"
```
Defines the version channel you want to use for the installation
Available : releases | prereleases | daily | latest
```YAML
nextcloud_version: 10.0.2
```
Specify the version name for channels **releases**, **prereleases** and **daily**. (it may not be numbers at all)
```YAML
nextcloud_branch: "stable"
```
Specify the branch name for **daily** & **latest** channel
```YAML
nextcloud_repository: "https://download.nextcloud.com/server"
```
The Nextcloud's official repository. You may change it if you have the sources somewhere else.
### Main configuration
```YAML
nextcloud_trusted_domain: ["{{ ansible_default_ipv4.address }}"]
```
The list of domains you will use to access the same Nextcloud instance.
```YAML
nextcloud_instance_name: "{{ nextcloud_trusted_domain | first }}"
```
The name of the Nextcloud instance. By default, the first element in the list of trusted domains
```YAML
nextcloud_websrv: "apache2"
```
The http server used by nextcloud. Available values are: **apache2** or **nginx**.
```YAML
nextcloud_webroot: "/opt/nextcloud"
```
The Nextcloud root directory.
```YAML
nextcloud_data_dir: "/var/ncdata"
```
The Nextcloud data directory. This directory will contain all the Nextcloud files. Choose wisely.
```YAML
nextcloud_admin_name: "admin"
```
Defines the Nextcloud admin's login.
```YAML
nextcloud_admin_pwd: "secret"
```
Defines the Nextcloud admin's password.

**Not defined by default**

If not defined by the user, a random password will be generated.
### Database configuration
```YAML
nextcloud_install_db: true
```
Whenever the role should install and configure a database on the same host.
```YAML
nextcloud_db_host: "127.0.0.1"
```
The database server's ip/hostname where Nextcloud's database is located.
```YAML
nextcloud_db_backend: "mysql"
```
Database type used by nextcloud.

Supported values are:
- mysql
- mariadb
- pgsql _(PostgreSQL)_

```YAML
nextcloud_db_name: "nextcloud"
```
The Nextcloud instance's database name.
```YAML
nextcloud_db_admin: "ncadmin"
```
The Nextcloud instance's database user's login
```YAML
nextcloud_db_pwd: "secret"
```
The Nextcloud instance's database user's password.

**Not defined by default.**

If not defined by the user, a random password will be generated.

### TLS configuration
```YAML
nextcloud_tls_enforce: true
```
Force http to https.
```YAML
nextcloud_force_strong_apache_ssl: true
```
force strong ssl configuration in the virtualhost file
```YAML
nextcloud_tls_cert_method: "self-signed"
```
Defines various method for retrieving a TLS certificate.
- **self-signed**: generate a _one year_ self-signed certificate for the trusted domain on the remote host and store it in _/etc/ssl_.
- **signed**: copy provided signed certificate for the trusted domain to the remote host or in /etc/ssl by default.
  Uses:
```YAML
  # Mandatory:
  nextcloud_tls_src_cert: /local/path/to/cert
  # ^local path to the certificate's key.
  nextcloud_tls_src_cert_key: /local/path/to/cert/key
  # ^local path to the certificate.

  # Optional:
  nextcloud_tls_cert: "/etc/ssl/{{ nextcloud_trusted_domain }}.crt"
  # ^remote absolute path to the certificate's key.
  nextcloud_tls_cert_key: "/etc/ssl/{{ nextcloud_trusted_domain }}.key"
  # ^remote absolute path to the certificate.
```
- **installed**: if the certificate for the trusted domain is already on the remote host, specify its location.
  Uses:
```YAML
  nextcloud_tls_cert: /path/to/cert
  # ^remote absolute path to the certificate's key. mandatory
  nextcloud_tls_cert_key: /path/to/cert/key
  # ^remote absolute path to the certificate. mandatory
  nextcloud_tls_cert_chain: /path/to/cert/chain
  # ^remote absolute path to the certificate's full chain- used only by apache - Optional
```

### System configuration
```YAML
websrv_user: "www-data"
```
system user for the http server
```YAML
websrv_group: "www-data"
```
system group for the http server
```YAML
mysql_root_pwd: "secret"
```
root password for the mysql server

**Not defined by default**

If not defined by the user, and mysql/mariadb is installed during the run, a random password will be generated.

### Generated password
The role uses Ansible's password Lookup:
- If a password is generated by the role, ansible stores it **localy** in **nextcloud_instances/{{ nextcloud_trusted_domain }}/** (relative to the working directory)
- if the file already exist, it reuse its content
- see http://docs.ansible.com/ansible/playbooks_lookups.html#the-password-lookup for more info

## Dependencies

none

## Example Playbook
### Case 1: Installing a quick Nextcloud demo
In some case, you may want to deploy quickly many instances of Nextcloud on multiple hosts for testing/demo purpose and don't want to tune the role's variables for each hosts: Just run the playbook without any additional variable (all default) !

```YAML
---
- hosts: server
  roles:
   - role: aalaesar.install_nextcloud
```

- This will install a Nextcloud 10.0.1 instance in /opt/nextcloud using apache2 and mysql.
- it will be available at **https://{{ ansible default ipv4 }}**  using a self signed certificate.
- Generated passwords are stored in **nextcloud_instances/{{ nextcloud_trusted_domain }}/** from your working directory.

### Case 1.1: specifying the version channel, branch, etc.
You can choose the version channel to download a specific version of nextcloud. Here's a variation of the previous case, this time installing the latest nightly in master.
```YAML
---
- hosts: server
  roles:
   - role: aalaesar.install_nextcloud
     nextcloud_channel: "latest"
     nextcloud_branch: "master"
```

### Case 2: Using letsencrypt with this role.
This role is not designed to manage letsencrypt certificates. However you can still use your certificates with nextcloud.

You must create first your certificates using a letsencrypt ACME client or an Ansible role like [ this one] (https://github.com/jaywink/ansible-letsencrypt)

then call _install_nextcloud_ by setting `nextcloud_tls_cert_method: "installed"`

Here 2 examples for apache and nginx (because their have slightly different configuration)
```YAML
---
- hosts: apache_server
  roles:
   - role: aalaesar.install_nextcloud
     nextcloud_trusted_domain:
       - "example.com"
     nextcloud_tls_cert_method: "installed"
     nextcloud_tls_cert: "/etc/letsencrypt/live/example.com/cert.pem"
     nextcloud_tls_cert_key: "/etc/letsencrypt/live/example.com/privkey.pem"
     nextcloud_tls_cert_chain: "/etc/letsencrypt/live/example.com/fullchain.pem"

- hosts: nginx_server
  roles:
    - role: aalaesar.install_nextcloud
      nextcloud_trusted_domain:
        - "example2.com"
      nextcloud_tls_cert_method: "installed"
      nextcloud_tls_cert: "/etc/letsencrypt/live/example2.com/fullchain.pem"
      nextcloud_tls_cert_key: "/etc/letsencrypt/live/example2.com/privkey.pem"
```
### Case 3: integration to an existing system.
- An Ansible master want to install a new Nextcloud instance at _cloud.example.tld_ on an existing server.
- He already have a valid certificate for the trusted domain in /etc/nginx/certs/ installed
- He can run the role with the following variables to install Nextcloud accordingly to its existing infrastructure .

```YAML
---
- hosts: server
  roles:
   - role: aalaesar.install_nextcloud
     nextcloud_trusted_domain:
       - "cloud.example.tld"
     nextcloud_websrv: "nginx"
     nextcloud_admin_pwd: "secret007"
     nextcloud_webroot: "/var/www/nextcloud/"
     nextcloud_data_dir: "/ncdata"
     nextcloud_db_pwd: "secretagency"
     nextcloud_tls_cert_method: "installed"
     nextcloud_tls_cert: "/etc/nginx/certs/nextcloud.crt"
     nextcloud_tls_cert_key: "/etc/nginx/certs/nextcloud.key"
     mysql_root_pwd: "42h2g2"
```

License
-------
BSD
