[![Ansible-lint status](https://github.com/aalaesar/backup_nextcloud/actions/workflows/ansible-lint.yml/badge.svg)](https://github.com/aalaesar/backup_nextcloud/actions?workflow=Ansible%20Lint)
[![YAML-lint status](https://github.com/aalaesar/backup_nextcloud/actions/workflows/yamllint.yml/badge.svg)](https://github.com/aalaesar/backup_nextcloud/actions?workflow=Yaml%20Lint)
# backup_nextcloud

An ansible role that creates a backup of a Nextcloud server. The backup is kept on the server.

## Requirements

The roles requires the following tools to be available on the host:
- tar
- gzip
- rsync
- a mysql or postgreSQL client if the database has to be dumped.

You'll need enough space on the target file system, depending on the size of your nextcloud server.

## Role Variables

### Setting Ansible `become` method
On different hosts `become` method used by Ansible could be different. Some host may be run on `root`, other on unprivileged user, some of hosts has `sudo` command installed, some not.
You can tweak this setting using these flags:
```yaml
ansible_become_method: "su" # set default become method: (su/sudo)
ansible_become_flags: "-s /bin/sh" # set become flags or leave empty if additional flags are not needed
```

### Locating the nextcloud server

The role has to know where the server files are, how to access it and where to store the backup.

```yaml
nextcloud_backup_target_dir: "/opt/nextcloud_backups"
nextcloud_webroot: "/opt/nextcloud"
# nextcloud_data_dir: "/var/ncdata" # optional.
nextcloud_websrv_user: www-data # you may need to change this to the nextcloud file owner depending of your setup and OS
```

### Adjusting the backup name:
The backup name can be adjusted with

```yaml
nextcloud_instance_name: "nextcloud" # a human identifier for the server
nextcloud_backup_suffix: "" # some arbitrary information at the end of the archive name
nextcloud_backup_format: "tgz" # extension of the archive. use a supported format used by the archive module (Choices: bz2, gz, tar, xz, zip)
```

Or you can change it completely by redefining

```yaml
nc_archive_name: "{{ nextcloud_instance_name }}_nextcloud-{{ nc_status.versionstring }}_{{ ansible_date_time.iso8601_basic_short }}{{ nextcloud_backup_suffix }}"
```

### Adjusting the backup content:

The role will __always__:
 - backup the server's config
 - create a list of installed & enabled applications(along with the version numbers)
 - download the proper server archive from the nextcloud download site.

You can adjust the scope of the backup by enabling/disabling some flags defined in default:

```yaml
nextcloud_backup_app_data: true
nextcloud_backup_user: true
nextcloud_backup_database: true
```

### Adjusting app data backup:

You may want to exclude some app_data folders from the backup.
But you cannot target a specific app to backup, this requires knowledge of the app's code.

```yaml
nextcloud_backup_app_data_exclude_folder:
  - preview
```

By default the preview folder is excluded from the backup as it can be notoriously __large__

### Adjusting user backup:

You can exclude a list of user(s) from the backup
```yaml
nextcloud_backup_exclude_users: []
```

You can also decide to include or not some side-folders.
```yaml
nextcloud_backup_user_files_trashbin: true
nextcloud_backup_user_files_versions: true
nextcloud_backup_user_uploads: true
nextcloud_backup_user_cache: true
```
### Other
 You can leave the server in maintenance mode at the end of the process by turning false
 ```yaml
 nextcloud_exit_maintenance_mode: true
 ```

## The Dependencies

None

## Example Playbook

### Running a full backup of your nextcloud server:
```yaml
- hosts: nextcloud
  roles:
    - role: aalaesar.backup_nextcloud
```

### Making a partial backup with only the app_data
```yaml
- hosts: nextcloud
  roles:
    - role: aalaesar.backup_nextcloud
  vars:
    nextcloud_backup_suffix: _only_app_data
    nextcloud_backup_user: false
    nextcloud_backup_database: false
```

## License

GPL-3.0
