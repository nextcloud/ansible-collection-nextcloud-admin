# Ansible role: download

An ansible role that downloads the Nextcloud server archive and configures app archives from the official download-server and app-store respectivel. The archives are downloaded to the control-host.

## Requirements

The role does not require any additional tools on the control host, only ansible version > 2.11.
You'll need enough space on the control host file system, typically 250MB for nextcloud server and largly different sizes for apps.

## Role Variables

### Locating the nextcloud download server

The role has to know the nextcloud download server and app download server address. The defaults are defined in `defaults/main.yml` and if needed can be changed. Note that they should not include a trailing slash `/`.

```yaml
# The URL where the server-package and the apps can be found.
nextcloud_repository: "https://download.nextcloud.com/server"  # Domain URL where to download Nextcloud server.
nextcloud_app_repository: "https://apps.nextcloud.com/apps"    # Domain URL where to download Nextcloud apps.
```

### Adjusting what to download

The role allows to either download only the nextcloud server archive or the apps or both by setting the respective variable to true.
Example:
```yaml
# Control if the server archive or the apps are downloaded or both.
nextcloud_download_server: true   # If set to true, download the nextcloud server archive
nextcloud_download_apps: true     # If set to true, download the configured apps from the online apps-store.
```

### Adjusting the nextcloud version for which to download archives.

The role supplements the nextcloud server information with the nextcloud version to download to. The settings needed depend on the setting for `nextcloud_download_server` and `nextcloud_download_apps`.
If `nextcloud_download_server` is set to true, then `nextcloud_version_channel` must to be specified. If set to `releases`, then `nextcloud_version_full` is required to be set, with the full version number. For example `29.0.1` for nextcloud with major version `29` and sub-version `0.1`.
Example:
```yaml
nextcloud_version_channel: "releases"  # mandatory, can be one of (releases/latest)
nextcloud_version_full: "29.0.1"       # full version string
```

If set to `latest` however, only `nextcloud_version_major` needs to be provided.
Example:
```yaml
nextcloud_version_channel: "releases"  # mandatory, can be one of (releases/latest)
nextcloud_version_major: "29"          # major version string only.
```
If `nextcloud_download_server` is set to `false` and for `nextcloud_download_apps` set to `true`, only `nextcloud_version_full` or `nextcloud_version_major` need to be provided. The variable `nextcloud_version_channel` is in this case not used.
Example:
```yaml
nextcloud_version_major: "29"          # major version string only.
```
or
```yaml
nextcloud_version_full: "29.0.1"       # major version string only.
```

The full configuration is:

```yaml
# An URL will be generated following naming rules used by nextcloud's repository
# Not following this rules correctly will make the role unable to download nextcloud.
nextcloud_version_channel: "releases"  # mandatory, can be one of (releases/latest)
# channel releases requires nextcloud_version_full set.
# channel lastest requires nextcloud_version_major set.
# Mandatory. Specify either nextcloud_version_full or nextcloud_version_major
# nextcloud_version_major: 25 # (24/25/26) for releases or for daily (master/stable25/stable26...)
nextcloud_version_full: "29.0.1" # full version string
```

### Adjusting the download directory

The role will download the files to the control-host to the directory where ansible-playbook was invoked - the current directory. This is typically the directory of the playbook. With `nextcloud_download_dir` a path relative to this current path can be specified. In the below example the files will be stored in subdirectories `files/nc` relative to the current directory. Note: Don't use a trailing slash `/`.
```yaml
nextcloud_download_dir: files/nc # The directory to download the files to on the control host. No trailing slash.
```

### Adjusting the apps to download

The role will download all specified apps in the `nextcloud_apps` dictionary. The dictionary `key` is the app name as shown e.g. on the command-line with `occ`-command. The dictionary `value` is a name, which may be used in the official-app store. The `value` is therefore only needed, if the store deviates from the `normal` behaviour. This can be seen, when the URL of the official WEB-store does not contain the app name.
For example, the `user_saml` app will be found on the official nextcloud app-store and the URL will contain `<server>/apps/user_saml/`. If this URL does deviate, then the deviating string can be used and provided to the dictionary `value`. The role will then use the dictionary `value` instead of the `key` for composing the URL to retrieve the app from the official app store. Until up to now, no exception is known, but who knows if this will be needed.

Example:
```yaml
# This example will download the nextcloud apps files_accesscontrol and user_saml.
nextcloud_apps:
  files_accesscontrol:
  user_saml: user_saml
```

## The Dependencies

None

## Example Playbook

### Download Nextcloud Server archive and apps to control-host

This example playbook will download the Nextcloud server archive for nextcloud version 29.0.1 and the Apps `files_access_control` and `user_saml` from the official Nextcloud Apps-store and store it on the control-host in the directory `files/nc/29` relative to the playbook.

```yaml
---
- name: Download Nextcloud server package and apps to control host.
  hosts:
    - localhost
  tasks:
    - name: Download Nextcloud server package and apps to control host.
      ansible.builtin.include_role:
        name: mktest_nextcloud.admin.download
      vars:
        nextcloud_download_dir: files/nc/29
        nextcloud_version_channel: releases
        nextcloud_version_full: 29.0.1
        nextcloud_download_server: true
        nextcloud_download_apps: true
        nextcloud_apps:
          files_accesscontrol:
          user_saml: user_saml
```

### Download Nextcloud Server archive only to control-host.

This example playbook will download the Nextcloud server archive for nextcloud version 29.0.1 and store it on the control-host in the directory `files/nc/29` relative to the playbook.

```yaml
---
- name: Download Nextcloud server package and apps to control host.
  hosts:
    - localhost
  tasks:
    - name: Download Nextcloud server package and apps to control host.
      ansible.builtin.include_role:
        name: mktest_nextcloud.admin.download
      vars:
        nextcloud_download_dir: files/nc/29
        nextcloud_version_channel: releases
        nextcloud_version_full: 29.0.1
        nextcloud_download_server: true
        nextcloud_download_apps: false
```

### Download Nextcloud Server apps to control-host

This example playbook will download the Apps `files_access_control` and `user_saml` from the official Nextcloud Apps-store for Nextcloud Version 29 and store it on the control-host in the directory `files/nc/29` relative to the playbook. Instead of `nextcloud_version_major` the `nextcloud_version_full` could be provided.

```yaml
---
- name: Download Nextcloud server package and apps to control host.
  hosts:
    - localhost
  tasks:
    - name: Download Nextcloud server package and apps to control host.
      ansible.builtin.include_role:
        name: mktest_nextcloud.admin.download
      vars:
        nextcloud_download_dir: files/nc/29
        nextcloud_version_major: 29
        nextcloud_download_server: false
        nextcloud_download_apps: true
        nextcloud_apps:
          files_accesscontrol:
          user_saml: user_saml
```

## Contributing

We encourage you to contribute to this role! Please check out the
[contributing guide](../CONTRIBUTING.md) for guidelines about how to proceed.

## License

BSD or GPG v2.0
