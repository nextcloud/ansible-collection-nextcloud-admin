![GitHub License](https://img.shields.io/github/license/nextcloud/ansible-collection-nextcloud-admin)
![GitHub Release](https://img.shields.io/github/v/release/nextcloud/ansible-collection-nextcloud-admin?logo=Github)
![Ansible Collection Version](https://img.shields.io/ansible/collection/v/nextcloud/admin?logo=Ansible)
![Ansible Collection Downloads](https://img.shields.io/ansible/collection/d/nextcloud/admin?logo=Ansible)
[![Collection tests](https://github.com/nextcloud/ansible-collection-nextcloud-admin/actions/workflows/tests_and_release.yml/badge.svg?branch=main)](https://github.com/nextcloud/ansible-collection-nextcloud-admin/actions/workflows/tests_and_release.yml)
![Static Badge](https://img.shields.io/badge/Nextcloud_versions-32_%7C_31_%7C_30-green?logo=Nextcloud&logoColor=blue)


# Ansible collection for nextcloud administration

This repository hosts the `nextcloud.admin`  Ansible Collection.

The collection includes a variety of Ansible content to help automate the management of nextcloud, as well as provisioning and maintenance of instances of nextcloud.

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.15.0**.

Plugins and modules within a collection may be tested with only specific Ansible versions.
<!--end requires_ansible-->

## Python Support

* Collection tested on 3.12+

## Supported nextcloud version

This collection supports Nextcloud versions: `30`, `31`, `32(latest)`
The community makes it's best efforts to keep tested versions updated with [Nextcloud release schedule](https://github.com/nextcloud/server/wiki/Maintenance-and-Release-Schedule).

## Included content

<!--start collection content-->
### Modules

Name | Description
--- | ---
nextcloud.admin.run_occ|Run the occ command line tool with given arguments.
nextcloud.admin.app_info| Return state, version, updates and path of one external application.
nextcloud.admin.app | Manage nextcloud external applications (install, remove, disable, etc)
nextcloud.admin.user_list | List configured users on the server with optional user infos
nextcloud.admin.user | short_description: Manage a Nextcloud user.
nextcloud.admin.group_list | List configured groups on the server with optional group infos
nextcloud.admin.group | Manage Nextcloud groups.

### Roles

Name | Description
--- | ---
nextcloud.admin.backup (**beta**)|Create a backup of a Nextcloud server
nextcloud.admin.install_nextcloud | Install and configure an Nextcloud instance for a Debian/Ubuntu server

<!--end collection content-->

## Installation and Usage

### Dependencies

#### netaddr Python Library

Content in this collection requires the [network address manipulation library](https://pypi.org/project/netaddr/) to manipulate network address. You can install it with:
```
    pip3 install netaddr
```

#### required standalone roles

By default, some roles in this collection are dependant of standalone roles from other namespaces. (this can be disabled).

Due to some limitations, ansible-galaxy does not install them automatically, them need to be installed afterward.

Once the collection is installed, run the command `ansible-galaxy role install -r <this_collection_folder>/requirements.yml`.

Alternatively, you can also add the content of [this file](requirements.yml) in your own `requirements.yml` file prior to installing the collection

### Installing the Collection from Ansible Galaxy

Before using the nextcloud collection, you need to install it with the Ansible Galaxy CLI:

    ansible-galaxy collection install nextcloud.admin

You can also include it in a `requirements.yml` file and install it via `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: nextcloud.admin
    version: 2.3.0
```

### Using modules from the Nextcloud Collection in your playbooks

It's preferable to use content in this collection using their Fully Qualified Collection Namespace (FQCN), for example `nextcloud.admin.run_occ`:

```yaml
---
- hosts: nextcloud_host
  gather_facts: false
  become: true
  tasks:
    - name: list installed apps
      nextcloud.admin.run_occ:
        nextcloud_path: /var/www/nextcloud
        command: app:list
```

If upgrading older playbooks from <2.0.0, you can minimise your changes by defining `collections` in your play and refer to this collection's role as `install_nextcloud`, instead of `nextcloud.admin.install_nextcloud`, as in this example:

```yaml
---
- hosts: localhost
  gather_facts: false
  connection: local

  collections:
    - nextcloud.admin

  tasks:
    - name: deploy nextcloud and dependencies
      include_role:
        name: install_nextcloud
```

For documentation on how to use:
- __individual modules__: please use `ansible-doc` command after installing this collection.
- __included roles__: as per ansible standard, ansible role are documented in their own README file.

## Testing and Development

If you want to develop new content for this collection or improve what's already here, the easiest way to work on the collection is to clone it into one of the configured [`COLLECTIONS_PATHS`](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#collections-paths), and work on it there.

### Testing with `molecule`

The `tests` directory contains playbooks for running integration tests on various scenarios.
There are also integration tests in the `molecule` directory

## Publishing New Versions

Releases are automatically built and pushed to Ansible Galaxy for any new tag.

## License

BSD

See LICENCE to see the full text.
