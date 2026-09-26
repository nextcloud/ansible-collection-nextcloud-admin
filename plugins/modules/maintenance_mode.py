#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Marc Crébassa <aalaesar@gmail.com>
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
module: maintenance_mode
short_description: Manage Nextcloud maintenance mode
description:
  - Enables or disables maintenance mode on a Nextcloud server.
  - The desired state can be specified using free-form syntax or the O(state) option.
  - Free-form syntax and O(state) cannot be used together.
  - The module is idempotent and supports check mode and diff mode.
options:
  state:
    description:
      - Desired state of Nextcloud maintenance mode.
      - C(enabled) and C(on) enable maintenance mode.
      - C(disabled) and C(off) disable maintenance mode.
    type: bool
    required: true
extends_documentation_fragment:
  - nextcloud.admin.occ_common_options
author:
  - Marc Crébassa (@aalaesar)
"""

EXAMPLES = r"""
- name: Enable maintenance mode
  nextcloud.admin.maintenance_mode: yes

- name: Enable maintenance mode
  nextcloud.admin.maintenance_mode:
    state: on

- name: Disable maintenance mode
  nextcloud.admin.maintenance_mode: no

- name: Disable maintenance mode
  nextcloud.admin.maintenance_mode:
    state: off
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools import (
    extend_nc_tools_args_spec,
)

from ansible_collections.nextcloud.admin.plugins.module_utils.server import NCServer
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    NextcloudException,
)

module_args_spec = dict(
    state=dict(
        type="bool",
        required=True,
    ),
)


def main():
    global module
    module = AnsibleModule(
        argument_spec=extend_nc_tools_args_spec(module_args_spec),
        supports_check_mode=True,
    )
    result = dict(changed=False, diff={})
    try:
        server = NCServer(module)
    except NextcloudException as e:
        e.fail_json(module)
        return

    current = server.maintenance
    desired = module.params["state"]
    if not server.installed:
        module.fail_json(
            msg="Nextcloud must be installed before maintenance mode can be managed."
        )
    if current != desired:
        if not module.check_mode:
            try:
                server.set_maintenance(desired)
            except NextcloudException as e:
                e.fail_json(module)
                return
        result["changed"] = True
        if module._diff:
            result["diff"] = {
                "before": {"maintenance": current},
                "after": {"maintenance": desired},
            }
    module.exit_json(**result)


if __name__ == "__main__":
    main()
