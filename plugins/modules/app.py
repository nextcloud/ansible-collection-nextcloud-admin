#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Marc Crébassa <aalaesar@gmail.com>
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

DOCUMENTATION = r"""

module: app

short_description: Manage external applications in a Nextcloud server

author:
  - "Marc Crébassa (@aalaesar)"

description:
  - Install, remove, disable, update external applications in a Nextcloud instance
  - This module requires to be run with advanced privileges
    unless it is run as the user that own the occ tool.

extends_documentation_fragment:
  - nextcloud.admin.occ_common_options

options:
  name:
    description: manage the following application.
    type: str
    required: true

  state:
    description:
      - The desired state for the application.
      - If set to `present`, the application is installed and set to enabled
      - If set to `absent` or `removed`, the application will be removed.
      - If set to `disabled` while the application _is not installed_, the module will install it _but won't enable it_.
      - `updated` will update the app if possible. It is equivalent to `install` if the app is not present.
    type: str
    choices:
    - "present"
    - "absent"
    - "removed"
    - "disabled"
    - "updated"
    default: "present"
    required: false
    aliases:
      - "status"

requirements:
  - "python >=3.6"
"""

EXAMPLES = r"""
- name: Enable preinstalled contact application
  nextcloud.admin.app:
    name: contacts
    state: present
    nextcloud_path: /var/lib/www/nextcloud

- name: Update calendar application
  nextcloud.admin.app:
    name: calendar
    state: updated
    nextcloud_path: /var/lib/www/nextcloud
"""

RETURN = r"""
actions_taken:
  description: The informations collected for the application requested.
  returned: always
  type: list
  contains:
    state:
      description:
        - Action taken and reported by the nextcloud server.
      returned: always
      type: string
version:
  description: App version present of updated on the server.
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nextcloud.admin.plugins.module_utils.app import app
from ansible_collections.nextcloud.admin.plugins.module_utils.occ_args_common import (
    args_spec,
)

module_args_spec = dict(
    name=dict(type="str", required=True),
    state=dict(
        type="str",
        required=False,
        default="present",
        choices=["present", "absent", "removed", "enabled", "disabled", "updated"],
        version=dict(
            type="str",
            required=False,
            default=None,
        ),
        aliases=["status"],
    ),
)


def main():
    global module

    module = AnsibleModule(
        argument_spec=args_spec(module_args_spec),
        supports_check_mode=True,
    )
    app_name = module.params.get("name")
    target_state = module.params.get("state", "present")
    nc_app = app(module, app_name)
    if target_state in ["present", "enabled"]:
        result = nc_app.install()
    elif target_state in ["absent", "removed"]:
        result = nc_app.remove()
    elif target_state == "updated":
        result = nc_app.update()
    elif target_state == "disabled":
        if nc_app.state in ["present", "disabled"]:
            result = nc_app.change_status("disable")
        else:
            result = nc_app.install(enable=False)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
