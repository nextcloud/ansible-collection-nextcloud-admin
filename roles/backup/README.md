# Ansible role: backup

An ansible role that creates a backup of a Nextcloud server. The backup is kept on the server (unless you [fetch it](#fetching-backup-from-remote-to-local-machine)).

## Requirements

The roles requires the following tools to be available on the host:
- tar
- gzip
- rsync
- a mysql or postgreSQL client if the database has to be dumped.

You'll need enough space on the target file system, depending on the size of your nextcloud server.

## Role Variables

### Locating the nextcloud server

The role has to know where the server files are, how to access it and where to store the backup.

```yaml
nextcloud_backup_target_dir: "/opt/nextcloud_backups"
nextcloud_webroot: "/opt/nextcloud"
# nextcloud_data_dir: "/var/ncdata" # optional.
nextcloud_websrv_user: "www-data" # you may need to change this to the nextcloud file owner depending of your setup and OS
```

### Adjusting the backup owner
The backup owner can be adjusted with. This may be useful when operating user is different than nextcloud's process owner.

```yaml
nextcloud_backup_owner: "www-data" # user name who will get owner on backup_target_dir and final archive
nextcloud_backup_group: "www-data" # user group who will get owner on backup_target_dir and final archive
```

### Adjusting the backup name
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

### Adjusting the backup content

The role will __always__:
 - backup the server's config
 - create a list of installed & enabled applications(along with the version numbers)

You can adjust the scope of the backup by enabling/disabling some flags defined in default:

```yaml
nextcloud_backup_download_server_archive: true
nextcloud_backup_app_data: true
nextcloud_backup_user: true
nextcloud_backup_database: true
```

### Adjusting nextcloud-server archive included in backup
Role can download the proper server archive from the nextcloud download site and add it to backup archive. 
It can be turned on using: `nextcloud_backup_download_server_archive` variable.

### Adjusting app data backup

You may want to exclude some app_data folders from the backup.
But you cannot target a specific app to backup, this requires knowledge of the app's code.

```yaml
nextcloud_backup_app_data_exclude_folder:
  - preview
```

By default the preview folder is excluded from the backup as it can be notoriously __large__

### Adjusting user backup

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

### Fetching backup from remote to local machine

You can fetch created backup from remote by setting these variables.
WARNING: user which you are used in Ansible has to be set as [backup owner](#adjusting-the-backup-owner) due to Ansible limitation on using `become` with `ansible.builtin.fetch`

```yaml
nextcloud_backup_fetch_to_local: true
nextcloud_backup_fetch_local_path: "/local_path/nextcloud_backup"
```

### Other

You can leave the server in maintenance mode at the end of the process by turning false

```yaml
nextcloud_exit_maintenance_mode: true
```

## The Dependencies

None

## Example Playbook

### Running a full backup of your nextcloud server

```yaml
- hosts: nextcloud
  roles:
    - role: nextcloud.nextcloud.backup
```

### Making a partial backup with only the app_data

```yaml
- hosts: nextcloud
  roles:
    - role: nextcloud.nextcloud.backup
  vars:
    nextcloud_backup_suffix: _only_app_data
    nextcloud_backup_user: false
    nextcloud_backup_database: false
```

## Contributing

We encourage you to contribute to this role! Please check out the
[contributing guide](../CONTRIBUTING.md) for guidelines about how to proceed.

## License

BSD
