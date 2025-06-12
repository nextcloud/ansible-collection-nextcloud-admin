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
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    AppExceptions,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools import (
    extend_nc_tools_args_spec,
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
    result = dict(
        actions_taken=[],
        version=None,
    )
    module = AnsibleModule(
        argument_spec=extend_nc_tools_args_spec(module_args_spec),
        supports_check_mode=True,
    )
    app_name = module.params.get("name")
    target_state = module.params.get("state", "present")
    nc_app = app(module, app_name)
    # case1: switch between enable/disable status
    if (target_state == "disabled" and nc_app.state == "enabled") or (
        target_state == "present" and nc_app.state == "disabled"
    ):
        if module.check_mode:
            result["actions_taken"] = [target_state]
        else:
            try:
                actions_taken = nc_app.toggle()
                result["actions_taken"].append(actions_taken)
            except AppExceptions as e:
                e.fail_json(module, **result)
    # case2: install and maybe enable the application
    elif (
        target_state in ["present", "updated", "disabled"] and nc_app.state == "absent"
    ):
        enable = target_state != "disabled"
        if module.check_mode:
            result["version"] = "undefined in check mode"
            result["actions_taken"] = ["installed"]
            if enable:
                result["actions_taken"].append("enabled")
        else:
            try:
                version, actions_taken = nc_app.install(enable=enable)
                if isinstance(actions_taken, list):
                    result["actions_taken"].extend(actions_taken)
                else:
                    result["actions_taken"].append(actions_taken)
                    result["version"] = version
            except AppExceptions as e:
                e.fail_json(module, **result)
    # case3: remove the application
    elif target_state in ["absent", "removed"] and nc_app.state in [
        "disabled",
        "present",
    ]:
        if module.check_mode:
            result["version"] = nc_app.version
            result["actions_taken"] = ["removed"]
            if nc_app.state == "present":
                result["actions_taken"].insert(0, "disabled")
        else:
            try:
                actions_taken, removed_version = nc_app.remove()
                if isinstance(actions_taken, list):
                    result["actions_taken"].extend(actions_taken)
                else:
                    result["actions_taken"].append(actions_taken)
                result["version"] = removed_version
            except AppExceptions as e:
                e.fail_json(module, **result)
    # case3: update the application if posible
    elif target_state == "updated" and nc_app.state in ["enabled", "present"]:
        if nc_app.update_available:
            if module.check_mode:
                result["actions_taken"].append("updated")
                result["version"] = nc_app.update_version_available
            else:
                try:
                    result["version"] = nc_app.update()
                    result["actions_taken"].append("updated")
                except AppExceptions as e:
                    e.fail_json(module, **result)

    result.update(changed=bool(result["actions_taken"]))
    if not result["version"]:
        result["version"] = nc_app.version
    module.exit_json(**result)


if __name__ == "__main__":
    main()
