#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Marc Crébassa <aalaesar@gmail.com>
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
---
module: group
short_description: Manage Nextcloud groups.
author:
  - Marc Crébassa (@aalaesar)
description:
  - This module allows for the addition or removal of groups in a Nextcloud instance.
  - It also supports adding or removing users from a group.
  - The module requires elevated privileges unless it is run as the user that owns the occ tool.
options:
  state:
    description:
      - Desired state of the group.
      - Use 'present' to ensure the group exists, 'absent' to ensure it does not.
      - Use 'append_users' to add users to the group without affecting existing members.
      - Use 'remove_users' to remove users from the group without affecting other members.
    choices: ['present', 'absent', 'append_users', 'remove_users']
    default: 'present'
    aliases: ['status', 'action']
    type: str
  id:
    description:
      - The unique identifier or name of the group.
    required: true
    aliases: ['name', 'group_id']
    type: str
  display_name:
    description:
      - The display name for the group.
    default: Null
    aliases: ['displayName']
    type: str
  users:
    description:
      - A list of usernames to be added or removed from the group.
      - When state is 'present', the module will match the exact list provided.
    default: Null
    elements: str
    aliases: ['members']
    type: list
  ignore_missing_users:
    description:
      - Whether to ignore errors when specified users are not found.
    default: False
    type: bool
  error_on_missing:
    description:
      - If set to True, the group is absent and any user management is expected, the module will fail.
      - The group will not be created.
    default: False
    type: bool
extends_documentation_fragment:
  - nextcloud.admin.occ_common_options
requirements:
  - python >= 3.12
"""

EXAMPLES = r"""
- name: Ensure group is present with display name
  group:
    id: "engineering"
    display_name: "Engineering Team"
    state: "present"

- name: Ensure group is absent
  group:
    id: "temporary_group"
    state: "absent"

- name: Ensure group has specific users
  group:
    id: "project_team"
    users:
      - "alice"
      - "bob"
    state: "present"

- name: Append users to a group
  group:
    id: "project_team"
    users:
      - "charlie"
    state: "append_users"

- name: Remove users from a group
  group:
    id: "old_project_team"
    users:
      - "dave"
    state: "remove_users"
"""

RETURN = r"""
changed:
  description: Indicates whether any changes were made to the group or its memberships.
  returned: always
  type: bool
added_users:
  description: A list of users that were successfully added to the group.
  returned: when users are added
  type: list
removed_users:
  description: A list of users that were successfully removed from the group.
  returned: when users are removed
  type: list
"""


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools import (
    extend_nc_tools_args_spec,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.identities import (
    idState,
    Group,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    IdentityNotPresent,
)

module_args_spec = dict(
    state=dict(
        type="str",
        required=False,
        choices=["present", "absent", "append_users", "remove_users"],
        aliases=["status", "action"],
        default="present",
    ),
    id=dict(
        type="str",
        aliases=["name", "group_id"],
        required=True,
    ),
    display_name=dict(
        required=False,
        aliases=["displayName"],
        default=None,
    ),
    users=dict(
        type="list",
        required=False,
        default=None,
        aliases=["members"],
        elements="str",
    ),
    ignore_missing_users=dict(
        type="bool",
        required=False,
        default=False,
    ),
    error_on_missing=dict(
        type="bool",
        required=False,
        default=False,
    ),
)


def main():
    global module
    module = AnsibleModule(
        argument_spec=extend_nc_tools_args_spec(module_args_spec),
        supports_check_mode=True,
    )
    result = dict(
        changed=False,
        added_users=[],
        removed_users=[],
    )
    group_id = module.params.get("id")

    nc_group = Group(module, group_id)

    display_name = module.params.get("display_name")
    ignore_missing_users = module.params.get("ignore_missing_users")
    error_on_missing = module.params.get("error_on_missing")

    if module.params.get("state") == "absent":
        group_desired_state = idState.ABSENT
    else:
        group_desired_state = idState.PRESENT

    if module.params.get("state") in ["append_users", "remove_users"]:
        users_mgnt = module.params.get("state")
    else:
        users_mgnt = "exact_match"
    users_list = module.params.get("users")

    # fails if the module is called with error_on_missing true with a non empty user list
    # while the group is missing AND status requested anything but 'absent'
    if (
        error_on_missing
        and nc_group.state is idState.ABSENT
        and users_list
        and group_desired_state is idState.PRESENT
    ):
        module.fail_json(
            msg=f"Group {group_id} is absent while trying to manage its users."
        )

    # add/delete group here
    if nc_group.state is not group_desired_state:
        if not module.check_mode:
            if group_desired_state is idState.ABSENT:
                nc_group.delete()
            else:
                nc_group.add(display_name)
        result["changed"] = True

    # add/remove users here
    if group_desired_state is idState.PRESENT and users_list:
        users_to_add = set()
        users_to_remove = set()
        if users_mgnt == "exact_match":
            users_to_add = set(users_list) - set(nc_group.users)
            users_to_remove = set(nc_group.users) - set(users_list)
        elif users_mgnt == "append_users":
            users_to_add = set(users_list)
        elif users_mgnt == "remove_users":
            users_to_remove = set(users_list)

        if not module.check_mode:
            try:
                for a_user in users_to_add:
                    nc_group.add_user(a_user)
                    result["added_users"] += [a_user]
                    result["changed"] = True
                for a_user in users_to_remove:
                    nc_group.remove_user(a_user)
                    result["removed_users"] += [a_user]
                    result["changed"] = True
            except IdentityNotPresent as e:
                if ignore_missing_users:
                    pass
                else:
                    e.fail_json(module)
        else:
            result["added_users"] = list(users_to_add)
            result["removed_users"] = list(users_to_remove)
            if users_to_add or users_to_remove:
                result["changed"] = True

    # finish and show result

    module.exit_json(**result)


if __name__ == "__main__":
    main()
