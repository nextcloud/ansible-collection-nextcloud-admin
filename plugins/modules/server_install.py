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
module: server_install
short_description: Run the server installation routine with the provided options
description:
  - Performs the initial installation of Nextcloud.
  - This module is idempotent based on the installation state.
  - If Nextcloud is already installed, no action is performed
    and the module reports C(changed=False).
  - Installation parameters are only applied during the initial
    installation. Subsequent changes to these parameters are
    not managed by this module.
notes:
  - This module does not update an existing Nextcloud installation.
  - Administrator credentials and database configuration must
    be managed separately after installation.
  - C(options) is marked as C(no_log) to prevent sensitive
    credentials from appearing in Ansible logs.
options:
  options:
    description:
      - Dictionary of options passed to the OCC C(maintenance:install) command.
      - Option names must use underscores (C(_)) instead of hyphens (C(-)),
        following Python keyword argument conventions.
      - Flag options are represented as C(True)/C(False) values.
      - Supported options depend on the installed Nextcloud version.
      - Option validation is delegated to OCC.
      - See the examples for common installation options.
    type: dict
    default: {}
  redact_occ_command:
    description:
      - Redact the content of the occ command in error logs.
      - Disabling redaction may expose sensitive credentials
        in error output.
    type: bool
    default: True
extends_documentation_fragment:
  - nextcloud.admin.occ_common_options
author:
  - Marc Crébassa (@aalaesar)
"""

EXAMPLES = r"""
- name: Install Nextcloud for tests with sqlite and no admin user
  nextcloud.admin.server_install:
    options:
      database_type: sqlite
      disable_admin_user: True

- name: Install Nextcloud with a PostgreSQL database
  nextcloud.admin.server_install:
    options:
      database_type: pgsql
      database_host: localhost
      database_name: nextcloud
      database_user: nextcloud
      database_pass: "{{ db_password }}"
      admin_user: admin
      admin_pass: "{{ admin_password }}"
      data_dir: /var/www/nextcloud/data
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
    options=dict(type="dict", default={}, no_log=True),
    redact_occ_command=dict(type="bool", default=True),
)


def main():
    global module
    module = AnsibleModule(
        argument_spec=extend_nc_tools_args_spec(module_args_spec),
        supports_check_mode=True,
    )
    install_options = module.params["options"]
    result = dict(changed=False)
    try:
        server = NCServer(module)
    except NextcloudException as e:
        e.fail_json(module, **result)
        return
    if not server.installed:
        if not module.check_mode:
            try:
                server.install(**install_options)
            except NextcloudException as e:
                if module.params["redact_occ_command"] and hasattr(e, "occ_cmd"):
                    e.occ_cmd = [  # pyright: ignore[reportAttributeAccessIssue]
                        "<redacted>"
                    ]
                e.fail_json(module)
                return
        if module._diff:
            result["diff"] = dict(  # pyright: ignore[reportArgumentType]
                before="Not installed.\n", after="Installed. "
            )
        result["changed"] = True

    module.exit_json(**result)


if __name__ == "__main__":
    main()
