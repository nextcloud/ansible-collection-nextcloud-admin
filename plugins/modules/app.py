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
    description:
      - Manage the following nextcloud application from the [nextcloud app store](https://apps.nextcloud.com/).
      - Attention! Use the application `technical` name (available at the end of the app's page url).
    type: str
    required: true
    aliases:
      - "id"

  state:
    description:
      - The desired state for the application.
      - If set to `present`, the application is installed and set to enabled.
      - If set to `absent` or `removed`, the application will be removed.
      - If set to `disabled`, disable the application if it is present or else install it _but do not enable it_.
      - If set to `updated`, equivalent to `present` if the app is absent or update to the version proposed by the server.
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
    id: contacts
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
      type: str
version:
  description: App version present or updated on the server.
  returned: always
  type: str
miscellaneous:
  description: Informative messages sent by the server during app operation.
  returned: when not empty
  type: list
  contains:
    misc:
      description: Something reported by the server.
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
    name=dict(type="str", aliases=["id"], required=True),
    state=dict(
        type="str",
        required=False,
        default="present",
        choices=["present", "absent", "removed", "disabled", "updated"],
        aliases=["status"],
    ),
)


def main():
    global module
    misc_msg = []
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
    if (target_state == "disabled" and nc_app.state == "present") or (
        target_state == "present" and nc_app.state == "disabled"
    ):
        if module.check_mode:
            result["actions_taken"] = [target_state]
        else:
            try:
                actions_taken, misc_msg = nc_app.toggle()
                result["actions_taken"].extend(actions_taken)
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
                actions_taken, misc_msg = nc_app.install(enable=enable)
                result["actions_taken"].extend(actions_taken)
                result["version"] = nc_app.version
            except AppExceptions as e:
                e.fail_json(module, **result)
    # case3: remove the application
    elif target_state in ["absent", "removed"] and nc_app.state in [
        "disabled",
        "present",
    ]:
        result["version"] = nc_app.version
        if module.check_mode:
            result["actions_taken"] = ["removed"]
            if nc_app.state == "present":
                result["actions_taken"].insert(0, "disabled")
        else:
            try:
                actions_taken, misc_msg = nc_app.remove()
                result["actions_taken"].extend(actions_taken)
            except AppExceptions as e:
                e.fail_json(module, **result)
    # case3: update the application if posible
    elif target_state == "updated" and nc_app.state == "present":
        if nc_app.update_available:
            if module.check_mode:
                result["actions_taken"].append("updated")
                result["version"] = nc_app.update_version_available
            else:
                try:
                    previous_version, result["version"] = nc_app.update()
                    result["actions_taken"].append("updated")
                except AppExceptions as e:
                    e.fail_json(module, **result)
    if misc_msg:
        result.update(miscellaneous=misc_msg)
    result.update(changed=bool(result["actions_taken"]))
    if not result["version"]:
        result["version"] = nc_app.version
    module.exit_json(**result)


if __name__ == "__main__":
    main()
