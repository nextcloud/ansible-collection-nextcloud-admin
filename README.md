# nextcloud collection for ansible

This repository hosts the `aalaesar.nextcloud`  Ansible Collection (formerly the role `aalaesar.install_nextcloud`).

The collection includes a variety of Ansible content to help automate the management of nextcloud, as well as provisioning and maintenance of instances of nextcloud.

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.10.0**.

Plugins and modules within a collection may be tested with only specific Ansible versions.
<!--end requires_ansible-->

## Python Support

* Collection tested on 3.10+

Note: Python2 is deprecated from [1st January 2020](https://www.python.org/doc/sunset-python-2/). Please switch to Python3.

## Nextcloud Version Support

This collection supports Nextcloud versions >=24.

## Included content

<!--start collection content-->
### Modules
Name | Description
--- | ---
aalaesar.nextcloud.run_occ|Run the occ command line tool with given arguments

### Roles
Name | Description
--- | ---
aalaesar.nextcloud.install_nextcloud|Install and configure an Nextcloud instance for a Debian/Ubuntu server - formerly `aalaesar.install_nextcloud`

<!--end collection content-->

## Installation and Usage

### Installing the Collection from Ansible Galaxy

Before using the nextcloud collection, you need to install it with the Ansible Galaxy CLI:

    ansible-galaxy collection install aalaesar.nextcloud

You can also include it in a `requirements.yml` file and install it via `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: aalaesar.nextcloud
    version: 2.0.0
```

### Installing the netaddr Python Library

Content in this collection requires the [network address manipulation library](https://pypi.org/project/netaddr/) to APIs. You can install it with:

    pip3 install netaddr

### Using modules from the Nextcloud Collection in your playbooks

It's preferable to use content in this collection using their Fully Qualified Collection Namespace (FQCN), for example `aalaesar.nextcloud.run_occ`:

```yaml
---
- hosts: nextcloud_host
  gather_facts: false
  become: true
  tasks:
    - name: list installed apps
      aalaesar.nextcloud.run_occ:
        nextcloud_path: /var/www/nextcloud
        command: app:list
```

If upgrading older playbooks from <2.0.0, you can minimise your changes by defining `collections` in your play and refer to this collection's role as `install_nextcloud`, instead of `aalaesar.install_nextcloud`, as in this example:

```yaml
---
- hosts: localhost
  gather_facts: false
  connection: local

  collections:
    - aalaesar.nextcloud

  tasks:
    - name: deploy nextcloud and dependencies
      include_role:
        name: install_nextcloud
        # previously:
        # name: aalaesar.install_nextcloud
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

GNU General Public License v3.0 or later

See LICENCE to see the full text.
