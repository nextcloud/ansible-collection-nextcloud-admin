nextcloud.admin.upgrade
=======================

Upgrades a Nextcloud instance step-by-step along a defined upgrade path. The role auto-detects the current version and iterates through each intermediate release up to the target version.

In summary, at each step the role:
- Checks PHP and PostgreSQL version compatibility (can be skipped), and optionally upgrades them
- Runs version-specific pre-upgrade tasks (if any)
- Runs the Nextcloud updater, managing maintenance mode
- Runs version-specific post-upgrade tasks (if any)

A backup of your Nextcloud instance is recommended prior to upgrading.

At the moment, this role only works in APT-based systems (Debian 12/13). Additionally, some features are missing, like MySQL/MariaDB support or PHP/PostgreSQL variable auto-detection. PRs are encouraged!

Requirements
------------

- Ansible >= 2.14
- Jmespath
- Xmltodict
- APT-based system (Debian 12/13)
- *Optional* - for automatic PHP upgrades: `geerlingguy.php` and `geerlingguy.php_versions` roles
- *Optional* - for automatic PostgreSQL upgrades: `geerlingguy.postgresql` role and `community.postgresql` collection

Role Variables
--------------

### Basic

| Variable | Default | Description |
|---|---|---|
| `nextcloud_webroot` | `/opt/nextcloud` | Path to the Nextcloud installation |
| `nextcloud_websrv_user` | `www-data` | System user running the web server |
| `nextcloud_initial_version` | auto-detected | Starting version (set to override detection) |
| `nextcloud_target_version` | last version in `nextcloud_upgrade_path` | Target version to upgrade to |
| `nextcloud_upgrade_path` | `[20.0.14, ..., 32.0.6]` | Ordered list of versions to step through |

### PHP upgrade

| Variable | Default | Description |
|---|---|---|
| `nextcloud_skip_php` | `false` | Skip PHP version check. Use at your own risk! |
| `nextcloud_upgrade_php` | `false` | Enable automatic PHP version upgrades |
| `nextcloud_php_requirements` | see defaults | Supported PHP versions per Nextcloud major release |

When enabled, the role installs a PHP version compatible with both the current and target Nextcloud versions, using distribution packages when possible.  
At the moment, it is absolutely necessary to set PHP role variables for the proper configuration of the newly installed PHP version.  
**Warning:** this uninstalls all other PHP versions and may add/remove third-party repositories. See defaults for more information.

### PostgreSQL upgrade

| Variable | Default | Description |
|---|---|---|
| `nextcloud_skip_postgresql` | `false` | Skip PostgreSQL version check. Use at your own risk! |
| `nextcloud_upgrade_postgresql` | `false` | Enable automatic PostgreSQL version upgrades |
| `nextcloud_db_name` | `nextcloud` | PostgreSQL database name |
| `nextcloud_postgresql_requirements` | see defaults | Supported PostgreSQL versions per Nextcloud major release |

When enabled, the role installs a PostgreSQL version compatible with both the current and target Nextcloud versions, using distribution packages when possible.  
At the moment, it is absolutely necessary to set PostgreSQL role variables for the proper configuration of the newly installed PostgreSQL version.  
**Warning:** this uninstalls all existing PostgreSQL versions, dumps/restores the DB, and may add/remove third-party repositories. See defaults for more information.

Example Playbook
----------------

```yaml
- hosts: nextcloud_servers
  roles:
    - role: nextcloud.admin.upgrade
      vars:
        nextcloud_webroot: /var/www/nextcloud
        nextcloud_target_version: "32.0.6"
        nextcloud_upgrade_php: true
```

License
-------

BSD

Author Information
------------------

Francisco Zadikian ([@fzadikian](https://github.com/fzadikian))

Based on playbooks by [@andrespias](https://github.com/andrespias) and [template](https://git.interior.edu.uy/cielito/upgrade) by [@ulvida](https://github.com/ulvida).
