[![Ansible-lint status](https://github.com/aalaesar/install_nextcloud/actions/workflows/ansible-lint.yml/badge.svg)](https://github.com/aalaesar/install_nextcloud/actions?workflow=Ansible%20Lint)
[![YAML-lint status](https://github.com/aalaesar/install_nextcloud/actions/workflows/yamllint.yml/badge.svg)](https://github.com/aalaesar/install_nextcloud/actions?workflow=Yaml%20Lint)
[![Tests](https://github.com/aalaesar/install_nextcloud/actions/workflows/tests.yml/badge.svg)](https://github.com/aalaesar/install_nextcloud/actions?workflow=Tests)

# Ansible role: install_nextcloud

This role installs and configures an Nextcloud instance for a Debian/Ubuntu server.

The role's main actions are:
-   [x] Packages dependencies installation.
-   [x] Database configuration (if located on the same host).
-   [x] Strengthened files permissions and ownership following Nextcloud recommendations.
-   [x] Web server configuration.
-   [x] Redis Server installation.
-   [x] Strengthened TLS configuration following _Mozilla SSL Configuration Generator_, intermediate profile by default, modern profile available.
-   [x] Post installation of Nextcloud applications

## Requirements

### Ansible version

Ansible >= 2.10

### Python libraries
To use `ipwrap` filter in Ansible, you need to install the netaddr Python library on a computer on which you use Ansible (it is not required on remote hosts). It can usually be installed with either your system package manager or using pip:

```bash
$ pip install netaddr
```

### Setup module:
The role uses facts gathered by Ansible on the remote host. If you disable the Setup module in your playbook, the role will not work properly.
### Root access
This role requires root access, so either configure it in your inventory files, run it in a playbook with a global `become: true` or invoke the role in your playbook like:
> playbook.yml:

```yaml
- hosts: dnsserver
  become: true
  roles:
    - role: aalaesar.install_nextcloud
```

## Dependencies

- [geerlingguy.php-versions](https://github.com/geerlingguy/ansible-role-php-versions)

You can install it by running either `ansible-galaxy role install geerlingguy.php-versions`
or  `ansible-galaxy role install -r ./requirements.yml` when working in this role directory
## Role Variables

Role's variables (and their default values):

### Choose the version

An URL will be generated following naming rules used in the nextcloud repository
_Not following this rules correctly may make the role unable to download nextcloud._

#### Repository naming rules

Some variables changes depending on the channel used and if get_latest is true.
This table summarize the possible cases.

|channel|latest|major&latest|major|full|special|
|---|---|---|---|---|---|
|**releases**|yes/no|_null_ \|24\|25\|...|_null_|"25.0.2"|_null_|
|**prereleases**|_null_|_null_|_null_|"25.0.3"|_null_ \|"RC(n)\|beta(n)"|
|**daily**|yes/no|_null_ \|master\|stable9\|...|master\|24\|25\|...|_null_|_null_ \|"YYYY-MM-DD"|

**major&latest** = major value when latest is true
_null_ = "not used"

#### Version variables

```yaml
nextcloud_version_channel: "releases" # releases | prereleases | daily
```

Specify the main channel to use.

```yaml
nextcloud_get_latest: true
```

Specify if the "latest" archive should be downloaded.

```yaml
# nextcloud_version_major: 25
```

Specify what major version you desire.

```yaml
# nextcloud_version_full: "25.0.3"
```

The full version of the desired nextcloud instance. type **M.F.P** _(Major.Feature.Patch)_

```yaml
# nextcloud_version_special: ""
```

Specify a special string in the archive's filename.
For prereleases: "RCn|beta" | for daily "YYYY-MM-DD"

```yaml
nextcloud_repository: "https://download.nextcloud.com/server"
```

Repository's URL.

```yaml
nextcloud_archive_format: "zip" # zip | tar.bz2
```

Choose between the 2 archive formats available in the repository.

```yaml
# nextcloud_full_url:
```

_If you don't like rules..._
Specify directly a full URL to the archive. The role will skip the url generation and download the archive. **Requires nextcloud_version_major to be set along**.

#### Examples:
- Download your own archive:
  (_you **must** specify the nextcloud major version along_)

```yaml
nextcloud_full_url: https://download.nextcloud.com/server/releases/nextcloud-25.0.0.zip
nextcloud_version_major: 42
```

-   Choose the latest release (default):

```yaml
nextcloud_version_channel: "releases"
nextcloud_get_latest: true
```

-   Choose the latest v25 release:

```yaml
nextcloud_version_channel: "releases"
nextcloud_get_latest: true
nextcloud_version_major: 25
```

-   Choose a specific release:

```yaml
nextcloud_version_channel: "releases"
nextcloud_get_latest: false
nextcloud_version_full: "25.0.0"
```

-   Get the nextcloud 25.0.3 prerelease 1:

```yaml
nextcloud_version_channel: "prereleases"
nextcloud_version_full: "25.0.3"
nextcloud_version_special: "RC3"
```

-   Get the latest daily:

```yaml
nextcloud_version_channel: "daily"
nextcloud_get_latest: true
```

-   Get the latest daily for stable 25:

```yaml
nextcloud_version_channel: "daily"
nextcloud_get_latest: true
nextcloud_version_major: "stable25"
```

-   Get the daily for master at january 1rst 2022:

```yaml
nextcloud_version_channel: "daily"
nextcloud_get_latest: false
nextcloud_version_major: "master"
nextcloud_version_special: "2022-01-01"
```

### Main configuration

```yaml
nextcloud_trusted_domain:
  - "{{ ansible_fqdn }}"
  - "{{ ansible_default_ipv4.address }}"
```

The list of domains you will use to access the same Nextcloud instance.

```yaml
nextcloud_trusted_proxies: []
```

The list of trusted proxies IPs if Nextcloud runs through a reverse proxy.

```yaml
nextcloud_instance_name: "{{ nextcloud_trusted_domain | first }}"
```

The name of the Nextcloud instance. By default, the first element in the list of trusted domains

### WebServer configuration

```yaml
nextcloud_install_websrv: true
```

The webserver setup can be skipped if you have one installed already.

```yaml
nextcloud_websrv: "apache2"
```

The http server used by nextcloud. Available values are: **apache2** or **nginx**.

```yaml
nextcloud_disable_websrv_default_site: false
```

Disable the default site of the chosen http server. (`000-default.conf` in Apache, `default` in Nginx.)

```yaml
nextcloud_websrv_template: "templates/{{nextcloud_websrv}}_nc.j2"
```

The jinja2 template creating the instance configuration for your webserver.
You can provide your own through this parameter.

```yaml
nextcloud_webroot: "/opt/nextcloud"
```

The Nextcloud root directory.

```yaml
nextcloud_data_dir: "/var/ncdata"
```

The Nextcloud data directory. This directory will contain all the Nextcloud files. Choose wisely.

```yaml
nextcloud_admin_name: "admin"
```

Defines the Nextcloud admin's login.

```yaml
nextcloud_admin_pwd: "secret"
```

Defines the Nextcloud admin's password.
**Not defined by default**
If not defined by the user, a random password will be generated.

```yaml
nextcloud_max_upload_size: "512m"
```

Defines the max size allowed to be uploaded on the server.
Use 0 to __disable__.

### Redis Server configuration

```yaml
nextcloud_install_redis_server: true
```

Whenever the role should install a redis server on the same host.

```yaml
nextcloud_redis_host: '/var/run/redis/redis.sock'
```

The Hostname of redis server. It is set to use UNIX socket as redis is on same host. Set to hostname if it is not the case.

```yaml
nextcloud_redis_port: 0
```

The port of redis server. Port 0 is for socket use. Default redis port is 6379.

```yaml
nextcloud_redis_settings:
  - { name: 'redis host', value: '"{{ nextcloud_redis_host }}"' }
  - { name: 'redis port', value: "{{ nextcloud_redis_port }}" }
  - { name: 'memcache.locking', value: '\OC\Memcache\Redis' }
```

Settings to use redis server with Nextcloud

### Nextcloud Background Jobs

```yaml
nextcloud_background_cron: true
```

Set operating system cron for executing Nextcloud regular tasks. This method enables the execution of scheduled jobs without the inherent limitations the Web server might have.

### Custom nextcloud settings

```yaml
nextcloud_config_settings:
  - { name: 'default_phone_region', value: 'DE' } # set a country code using [ISO 3166-1](https://en.wikipedia.org/wiki/ISO_3166-1)
  - { name: 'overwrite.cli.url', value: 'https://{{ nextcloud_trusted_domain | first }}' }
  - { name: 'memcache.local', value: '\OC\Memcache\APCu' }
  - { name: 'open_basedir', value: '/dev/urandom' }
  - { name: 'mysql.utf8mb4', value: true }
  - { name: 'updater.release.channel', value: 'production' } # production | stable | daily | beta
```

Setting custom Nextcloud setting in config.php ( [Config.php Parameters Documentations](https://docs.nextcloud.com/server/stable/admin_manual/) )

Default custom settings:
-   **Base URL**: 'https:// {{nextcloud_instance_name}}'
-   **Memcache local**: APCu
-   **Mysql Character Set**: utf8mb4
-   **PHP read access to /dev/urandom**: Enabled
-   **Updater Relese Channel:** Production

### Database configuration

```yaml
nextcloud_install_db: true
```

Whenever the role should install and configure a database on the same host.

```yaml
nextcloud_db_host: "127.0.0.1"
```

The database server's ip/hostname where Nextcloud's database is located.

```yaml
nextcloud_db_backend: "mysql"
```

Database type used by nextcloud.

Supported values are:
-   mysql
-   mariadb
-   pgsql _(PostgreSQL)_

```yaml
nextcloud_db_name: "nextcloud"
```

The Nextcloud instance's database name.

```yaml
nextcloud_db_admin: "ncadmin"
```

The Nextcloud instance's database user's login

```yaml
nextcloud_db_pwd: "secret"
```

The Nextcloud instance's database user's password.

**Not defined by default.**

If not defined by the user, a random password will be generated.

### TLS configuration

```yaml
nextcloud_install_tls: true
```

TLS setup can be skipped if you manage it separately (e.g. behind a reverse proxy).

```yaml
nextcloud_tls_enforce: true
```

Force http to https.

```yaml
nextcloud_mozilla_modern_ssl_profile: true
```

Force Mozilla modern SSL profile in webserver configuration (intermediate profile is used when false).

```yaml
nextcloud_hsts: false
```

Set HTTP Strict-Transport-Security header (e.g. "max-age=15768000; includeSubDomains; preload").

_(Before enabling HSTS, please read into this topic first)_

```yaml
nextcloud_tls_cert_method: "self-signed"
```

Defines various method for retrieving a TLS certificate.
-   **self-signed**: generate a _one year_ self-signed certificate for the trusted domain on the remote host and store it in _/etc/ssl_.
-   **signed**: copy provided signed certificate for the trusted domain to the remote host or in /etc/ssl by default.
  Uses:

```yaml
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
-   **installed**: if the certificate for the trusted domain is already on the remote host, specify its location.

  Uses:

```yaml
  nextcloud_tls_cert: /path/to/cert
  # ^remote absolute path to the certificate's key. mandatory
  nextcloud_tls_cert_key: /path/to/cert/key
  # ^remote absolute path to the certificate. mandatory
  nextcloud_tls_cert_chain: /path/to/cert/chain
  # ^remote absolute path to the certificate's full chain- used only by apache - Optional
```

```yaml
nextcloud_tls_session_cache_size: 50m
```

Set the size of the shared nginx TLS session cache to 50 MB.

### System configuration

**_WARNING: Current Nextcloud requires php v8.0 or later. This role is tested and installs by default the recommended version through third party repos. See more details below._**

Nextcloud's [supported version of php](https://docs.nextcloud.com/server/25/admin_manual/installation/system_requirements.html#server) can often not be available in your distro official repository. `php_install_external_repos` will use [geerlingguy.php-versions](https://github.com/geerlingguy/ansible-role-php-versions) role to add the appropriate third party for your distribution version.

If you do not want to install the third party repository, you can set the following  variable to false, but you'll have to install php on your own before running this role. 
```yaml
php_install_external_repos: true
```

Install and use a custom version for PHP instead of the default one:

```yaml
php_ver: '8.1'
php_dir: "/etc/php/{{ php_ver }}"
php_bin: "php-fpm{{ php_ver }}"
php_pkg_apcu: "php-apcu"
php_pkg_spe:
  - "php{{ php_ver }}-imap"
  - "php{{ php_ver }}-imagick"
  - "php{{ php_ver }}-xml"
  - "php{{ php_ver }}-zip"
  - "php{{ php_ver }}-mbstring"
  - "php-redis"
php_socket: "/run/php/{{ php_ver }}-fpm.sock"
php_memory_limit: 512M
```

```yaml
nextcloud_websrv_user: "www-data"
```

System user for the http server

```yaml
nextcloud_websrv_group: "www-data"
```

System group for the http server

```yaml
nextcloud_mysql_root_pwd: "secret"
```

Root password for the mysql server

**Not defined by default**

If not defined by the user, and mysql/mariadb is installed during the run, a random password will be generated.

### Generated password

The role uses Ansible's password Lookup:

-   If a password is generated by the role, ansible stores it **locally** in **nextcloud_instances/{{ nextcloud_trusted_domain }}/** (relative to the working directory)
-   if the file already exist, it reuse its content
-   see [the ansible password lookup documentation](https://docs.ansible.com/ansible/latest/plugins/lookup/password.html) for more info

### Post installation:
#### Applications installation

Since **v1.3.0**, it is possible to download, install and enable nextcloud applications during a post-install process.

The application (app) to install have to be declared in the `nextcloud_apps` dictionary in a "key:value" pair.
-   The app name is the key
-   The download link, is the value.

```yaml
nextcloud_apps:
  app_name_1: "http://download_link.com/some_archive.zip"
  app_name_2: "http://getlink.com/another_archive.zip"
```

Alternatively, if you need to configure an application after enabling it, you can use this structure.

```yaml
nextcloud_apps:
  app_name_1:
    source: "http://download_link.com/some_archive.zip"
    conf:
      parameter1: ldap:\/\/ldapsrv
      parameter2: another_value
```

**Notes:**
-   Because the role is using nextcloud's occ, it is not possible to install an app from the official nextcloud app store.
-   If you know that the app is already installed, you can give an empty string to skip the download.
-   The app name need the be equal to the folder name located in the **apps folder** of the nextcloud instance, which is extracted from the downloaded archive.
The name may not be canon some times. (like **appName-x.y.z** instead of **appName**)
-   The role will **not** update an already enabled application.
-   The configuration is applied only when the app in enabled the first time:
Changing a parameter, then running the role again while the app is already enabled will **not** update its configuration.
-   this post_install process is tagged and can be called directly using the `--tags install_apps` option.

## Example Playbook
### Case 1: Installing a quick Nextcloud demo
In some case, you may want to deploy quickly many instances of Nextcloud on multiple hosts for testing/demo purpose and don't want to tune the role's variables for each hosts: Just run the playbook without any additional variable (all default) !

```yaml
---
- hosts: server
  roles:
   - role: aalaesar.install_nextcloud
```

-   This will install a Nextcloud 10.0.1 instance in /opt/nextcloud using apache2 and mysql.
-   it will be available at **https:// {{ ansible default ipv4 }}**  using a self signed certificate.
-   Generated passwords are stored in **nextcloud_instances/{{ nextcloud_trusted_domain }}/** from your working directory.

### Case 1.1: specifying the version channel, branch, etc.
You can choose the version channel to download a specific version of nextcloud. Here's a variation of the previous case, this time installing the latest nightly in master.

```yaml
---
- hosts: server
  roles:
   - role: aalaesar.install_nextcloud
     nextcloud_version_channel: "daily"
     nextcloud_version_major: "master"
```

### Case 2: Using letsencrypt with this role.
This role is not designed to manage letsencrypt certificates. However you can still use your certificates with nextcloud.

You must create first your certificates using a letsencrypt ACME client or an Ansible role like [this one] (https://github.com/jaywink/ansible-letsencrypt)

then call _install_nextcloud_ by setting `nextcloud_tls_cert_method: "installed"`

Here 2 examples for apache and nginx (because they have slightly different configurations)

```yaml
---
- hosts: apache_server
  roles:
   - role: aalaesar.install_nextcloud
     nextcloud_trusted_domain:
       - "example.com"
     nextcloud_tls_cert_method: "installed"
     nextcloud_tls_cert: "/etc/letsencrypt/live/example.com/cert.pem"
     nextcloud_tls_cert_key: "/etc/letsencrypt/live/example.com/privkey.pem"
     nextcloud_tls_cert_chain: "/etc/letsencrypt/live/example.com/chain.pem"

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
-   An Ansible master want to install a new Nextcloud instance on an existing Ubuntu 20.04 server with nginx & mariadb installed.
-   As is server do not meet the php requirements for Nextcloud 11, he chooses to use the lastest Nextcloud 10 release.
-   He wants it to be accessible from internet at _cloud.example.tld_ and from his intranet at _dbox.intra.net_.
-   He already have a valid certificate for the intranet domain in /etc/nginx/certs/ installed
-   he wants the following apps to be installed & enabled : files_external, calendar, agenda, richdocuments (Collabora)
-   The richdocuments app has to be configured to point out to the Collabora domain.

He can run the role with the following variables to install Nextcloud accordingly to its existing requirements .

```yaml
---
- hosts: server
  roles:
   - role: aalaesar.install_nextcloud
     nextcloud_version_major: 25
     nextcloud_trusted_domain:
       - "cloud.example.tld"
       - "dbox.intra.net"
     nextcloud_websrv: "nginx"
     nextcloud_admin_pwd: "secret007"
     nextcloud_webroot: "/var/www/nextcloud/"
     nextcloud_data_dir: "/ncdata"
     nextcloud_db_pwd: "secretagency"
     nextcloud_tls_cert_method: "installed"
     nextcloud_tls_cert: "/etc/nginx/certs/nextcloud.crt"
     nextcloud_tls_cert_key: "/etc/nginx/certs/nextcloud.key"
     nextcloud_mysql_root_pwd: "42h2g2"
     nextcloud_apps:
       files_external: "" # enable files_external which is already installed in nextcloud
       calendar: "https://github.com/nextcloud/calendar/releases/download/v1.5.0/calendar.tar.gz"
       contacts: "https://github.com/nextcloud/contacts/releases/download/v1.5.3/contacts.tar.gz"
       richdocuments-1.1.25: # the app name is equal to the extracted folder name from the archive
          source: "https://github.com/nextcloud/richdocuments/archive/1.1.25.zip"
          conf:
            wopi_url: 'https://office.example.tld'
```

## Contributing

We encourage you to contribute to this role! Please check out the
[contributing guide](CONTRIBUTING.md) for guidelines about how to proceed.

## License

BSD 

