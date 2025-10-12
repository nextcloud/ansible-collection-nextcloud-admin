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

# DOCUMENTATION = r"""

# module: group_list

# short_description: List configured groups on the server with optional group infos.

# author:
#   - "Marc Crébassa (@aalaesar)"

# description:
#   - Return the list of groups present in the server instance
#   - Optionally recovery infos of one or more group
#   - This module requires to be run with advanced privileges
#     unless it is run as the group that own the occ tool.

# extends_documentation_fragment:
#   - nextcloud.admin.occ_common_options

# options:
#   infos:
#     description:
#       - Weither to fetch group infos or not
#     aliases: ['show_details']
#     type: bool

#   limit:
#     description:
#       - Number of groups to retrieve
#     required: false
#     type: int
#     default: 500

#   offset:
#     description:
#       - Offset for retrieving groups
#     required: false
#     type: int
#     default: 0

# requirements:
#   - "python >=3.12"
# """

DOCUMENTATION = r"""
---
module: group_list
short_description: List configured groups on the server with optional group infos.
author:
  - Marc Crébassa (@aalaesar)
description:
  - Return the list of groups present in the server instance.
  - Optionally retrieve more infos
  - This module requires elevated privileges unless it is run as the group that owns the occ tool.
extends_documentation_fragment:
  - nextcloud.admin.occ_common_options
options:
  infos:
    description:
      - Whether to fetch group infos or not.
    aliases: [show_details]
    type: bool
    default: False
  limit:
    description:
      - Number of groups to retrieve.
    required: false
    type: int
    default: 500
  offset:
    description:
      - Offset for retrieving groups.
    required: false
    type: int
    default: 0
requirements:
  - python >= 3.12
"""

EXAMPLES = r"""
- name: get the list of configured groups
  nextcloud.admin.group_list:
    nextcloud_path: /var/lib/www/nextcloud
  register: nc_groups

- name: get infos of all groups
  nextcloud.admin.group_list:
    infos: true
    nextcloud_path: /var/lib/www/nextcloud
"""

RETURN = r"""
groups:
  description:
    - Dictionary of groups found in the Nextcloud instance.
    - The structure depends on the value of the C(infos) parameter.
  returned: always
  type: dict
  contains:
    <group_id>:
      description:
        - If C(infos) is false, each key is a group_id and the value the list of members.
        - If C(infos) is true, each key is a group_id and the value is a dictionary containing
          detailed group information (e.g. displayNames, users, backend, etc.).
      type: raw
  sample:
    simple:
      admin: ["admin"]
      users: ["bob", "alice"]
    detailed:
      admin:
        displayName: "admin"
        backends: ["Database"]
        users: ["admin"]
      users:
        displayname: "Normal users"
        backends: ["Database"]
        users: ["bob", "alice"]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools import (
    run_occ,
    extend_nc_tools_args_spec,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    OccExceptions,
)
import json

module_args_spec = dict(
    infos=dict(
        type="bool",
        required=False,
        aliases=["show_details"],
        default=False,
    ),
    limit=dict(
        type="int",
        required=False,
        default=500,
    ),
    offset=dict(
        type="int",
        required=False,
        default=0,
    ),
)


def main():
    global module
    module = AnsibleModule(
        argument_spec=extend_nc_tools_args_spec(module_args_spec),
        supports_check_mode=True,
    )
    limit = module.params.get("limit", 500)
    offset = module.params.get("offset", 0)
    get_infos = module.params.get("infos")

    occ_command = list(
        filter(
            None,
            [
                "group:list",
                "--output=json",
                f"--offset={offset}",
                f"--limit={limit}",
                "--info" if get_infos else None,
            ],
        )
    )

    try:
        stdout = run_occ(module, occ_command)[1]
        groups = json.loads(stdout)

    except OccExceptions as e:
        e.fail_json(module)
    except json.JSONDecodeError:
        module.fail_json(msg="Unable to understand the server answer.", stdout=stdout)

    module.exit_json(
        changed=False,
        groups=groups,
    )


if __name__ == "__main__":
    main()
