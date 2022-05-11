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
### Locating the nextcloud server

The role has to know where the server files are, how to access it and where to store the backup.

```yaml
nextcloud_backup_target_dir: "/opt/nextcloud_backups"
nextcloud_webroot: "/opt/nextcloud"
# nextcloud_data_dir: "/var/ncdata" # optionnal.
nextcloud_websrv_user: www-data
```

### Adjusting the backup name:
The backup name can be adjusted with

```yaml
nextcloud_instance_name: "nextcloud" # a human identifier for the server
nextcloud_backup_suffix: "" # some artitrary information at the end of the archive name
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

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - { role: username.rolename, x: 42 }

## License

GPL-3.0
