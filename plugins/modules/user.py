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
module: user
short_description: Manage a Nextcloud user.
author:
  - Marc Crébassa (@aalaesar)
description:
  - This module allows for the addition or removal and small edit of a user in a Nextcloud instance.
  - It also supports adding or removing users from a group.
  - The module requires elevated privileges unless it is run as the user that owns the occ tool.
options:
  state:
    description:
      - Desired state of the group.
      - Use 'present' to ensure the user exists and is enabled, 'absent' to delete it if necessary.
      - Use 'disabled' to ensure the user exists and is disabled.
    choices: ['present', 'absent', 'disabled']
    default: 'present'
    aliases: ['status']
    type: str

  id:
    description:
      - The unique identifier or name of the user.
    required: true
    aliases: ['name', 'user_id']
    type: str

  display_name:
    description:
      - The display name for the user.
    default: Null
    aliases: ['displayName']
    type: str

  email:
    description:
      - The user's email.
    default: Null
    type: str

  groups:
    description:
      - A list of groups the user must be a member of.
      - If any list is provided (even an empty one), __the module will enforce this list__.
        Adding the user to all groups in the list and removing it from any group not specified in it.
      - To manage groups more dynamically, use the 'nextcloud.admin.group' module instead.
    default: Null
    elements: str
    type: list

  ignore_missing_groups:
    description:
      - Whether to ignore errors when specified groups are not found.
      - If `True`, the module will raise an Ansible warning for each element in `groups` that doesn't exist in the Nextcloud server.
      - If `False`, the module will fail at the first absent group encountered instead.
    default: False
    type: bool

  reset_password:
    description:
      - Trigger a password reset for the user.
    default: False
    type: bool

  password:
    description:
      - Specify a password.
      - Used only during user creation or password reset.
    default: Null
    type: str

extends_documentation_fragment:
  - nextcloud.admin.occ_common_options
requirements:
  - python >= 3.12
"""

EXAMPLES = r"""
- name: Ensure user is present with display name
  nextcloud.admin.user:
    nextcloud_path: /var/www/nextcloud
    id: "alice"
    display_name: "Alice Smith"
    state: present

- name: Ensure user bob does no exist.
  nextcloud.admin.user:
    nextcloud_path: /var/www/nextcloud
    id: "bob"
    state: "absent"

- name: Ensure the user is present and member of some groups.
  nextcloud.admin.user:
    nextcloud_path: /var/www/nextcloud
    id: "alice"
    groups:
      - "project_team"
      - "normal_users"
    state: "present"

- name: Ensure the user is present but disabled and member of some groups.
  nextcloud.admin.user:
    nextcloud_path: /var/www/nextcloud
    id: "alice"
    groups:
      - "dev_team"
    state: "disabled"

- name: Reset the user password.
  nextcloud.admin.user:
    nextcloud_path: /var/www/nextcloud
    id: "alice"
    reset_password: True

- name: Change the user password
  nextcloud.admin.user:
    nextcloud_path: /var/www/nextcloud
    id: "alice"
    reset_password: True
    password: "new_password"
  no_log: True

"""

RETURN = r"""
changed:
  description: Indicates whether any changes were made to the user.
  returned: always
  type: bool
"""


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools import (
    extend_nc_tools_args_spec,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.identities import (
    idState,
    Group,
    User,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    OccExceptions,
)

module_args_spec = dict(
    state=dict(
        type="str",
        required=False,
        choices=["present", "absent", "disabled"],
        aliases=["status"],
        default="present",
    ),
    id=dict(
        type="str",
        aliases=["name", "user_id"],
        required=True,
    ),
    display_name=dict(
        type="str",
        required=False,
        aliases=["displayName"],
        default=None,
    ),
    email=dict(
        type="str",
        required=False,
        default=None,
    ),
    password=dict(
        type="str",
        required=False,
        default=None,
        no_log=True,
    ),
    reset_password=dict(type="bool", required=False, default=False, no_log=False),
    groups=dict(
        type="list",
        required=False,
        default=None,
        elements="str",
    ),
    ignore_missing_groups=dict(
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
    )

    user_added = False

    user_id = module.params.get("id")
    nc_user = User(module=module, ident=user_id)
    desired_state = idState[module.params.get("state").upper()]
    user_groups = module.params.get("groups")
    if isinstance(user_groups, str):
        user_groups = [user_groups]
    display_name = module.params.get("display_name")
    email = module.params.get("email")
    password = module.params.get("password")
    reset_password = module.params.get("reset_password")
    ignore_missing_groups = module.params.get("ignore_missing_groups")

    if nc_user.state is not desired_state:
        if not module.check_mode:
            if desired_state is idState.ABSENT:
                # delete the user
                nc_user.delete()
            elif desired_state is idState.DISABLED:
                if nc_user.state is idState.ABSENT:
                    nc_user.add(
                        password is None, password, display_name, user_groups, email
                    )
                    user_added = True
                # disable the user
                nc_user.disable()
            elif desired_state is idState.PRESENT:
                if nc_user.state is idState.DISABLED:
                    # enable the user
                    nc_user.enable()
                else:
                    # create the user
                    nc_user.add(
                        password is None, password, display_name, user_groups, email
                    )
                    user_added = True
        result["changed"] = True

    # At this point if the user was created or deleted then the module must exit
    # as a created user is supposed to match the requested state and
    # a deleted user cannot be managed further.
    if user_added or (
        desired_state is idState.ABSENT and nc_user.state is idState.ABSENT
    ):
        module.exit_json(**result)

    # user management part

    # reset password for the user
    if reset_password:
        if not module.check_mode:
            nc_user.reset_password(password)
        result["changed"] = True

    # update display name or email of the user
    if display_name and nc_user.infos.get("display_name", None) != display_name:
        try:
            if not module.check_mode:
                nc_user.edit_settings("display_name", display_name)
                result["changed"] = True
        except OccExceptions as e:
            e.fail_json(module)
    # module.fail_json(msg='message', infos = nc_user.infos)
    if email and nc_user.infos.get("email", None) != email:
        try:
            if not module.check_mode:
                nc_user.edit_settings("email", email)
            result["changed"] = True
        except OccExceptions as e:
            e.fail_json(module)

    # update groups of the user
    if user_groups is not None:
        try:
            if nc_user.groups != user_groups:
                groups_to_add = set(user_groups) - set(nc_user.groups)
                groups_to_remove = set(nc_user.groups) - set(user_groups)
                for group in groups_to_add:
                    nc_group = Group(module, group)
                    if nc_group.state is idState.ABSENT:
                        message = f"Cannot add user {user_id} to absent group {group}."
                        if ignore_missing_groups:
                            module.warn(message)
                        else:
                            module.fail_json(message)
                    else:
                        if not module.check_mode:
                            nc_group.add_user(user_id)
                        result["changed"] = True

                for group in groups_to_remove:
                    nc_group = Group(module, group)
                    if nc_group.state is idState.PRESENT:
                        if not module.check_mode:
                            nc_group.remove_user(user_id)
                        result["changed"] = True
        except TypeError as e:
            module.fail_json(msg="The groups argument must be a list", **e.__dict__)
        except OccExceptions as e:
            e.fail_json(msg=e.msg, **e.__dict__)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
