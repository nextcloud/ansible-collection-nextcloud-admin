#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Marc Crébassa <aalaesar@gmail.com>
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

module: run_occ

short_description: Run the occ command line tool with given arguments

author:
  - "Marc Crébassa (@aalaesar)"

description:
  - Run admin commands on a Nextcloud instance using the OCC command line tool.
  - Pass only arguments understood by the occ tool.
  - Check https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/occ_command.html
    for more details about the available commands.
  - Don't support check mode.
  - Always returns state as 'changed'.
  - This module requires to be run with advanced privileges
    unless it is run as the user that own the occ tool.

extends_documentation_fragment:
  - nextcloud.admin.occ_common_options

options:
  command:
    description:
      - The string passed directly to the occ command line.
      - Shell variable expansion is not available.
      - Shell pipelining is not supported.
    type: str
    aliases:
      - args

requirements:
  - "python >=3.6"
"""

EXAMPLES = r"""
- name: get nextcloud basic info status
  nextcloud.admin.run_occ:
    command: status --output=json
    nextcloud_path: /var/lib/www/nextcloud
  changed_when: false
  register: nc_status

- name: install an application
  nextcloud.admin.run_occ:
    command: app:install notes
    nextcloud_path: /var/lib/www/nextcloud
"""
RETURN = r"""
command:
  description: The complete line of arguments given to the occ tool.
  returned: always
  type: string
rc:
  description: The return code given by the occ tool.
  returned: always
  type: int
stdout:
  description: The complete normal return of the occ tool in one string. All new lines will be replaced by \\n.
  returned: always
  type: str
stdout_lines:
  description: The complete normal return of the occ tool. Each line is a element of a list.
  returned: always
  type: list
  elements: str
stderr:
  description: The complete error return of the occ tool in one string. All new lines will be replaced by \\n.
  returned: always
  type: str
stderr_lines:
  description: The complete error return of the occ tool. Each line is a element of a list.
  returned: always
  type: list
  elements: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools import (
    run_occ,
    extend_nc_tools_args_spec,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    OccExceptions,
)

module_args_spec = dict(
    command=dict(
        type="str",
        required=True,
    ),
)


def main():
    global module

    module = AnsibleModule(
        argument_spec=extend_nc_tools_args_spec(module_args_spec),
        supports_check_mode=False,
    )
    command = module.params.get("command")
    result = dict(command=command)
    try:
        returnCode, stdOut, stdErr = run_occ(module, command)[0:3]
        result.update(
            dict(
                rc=returnCode,
                stdout=stdOut,
                stderr=stdErr,
            )
        )
    except OccExceptions as e:
        module.fail_json(
            msg=str(e),
            exception_class=type(e).__name__,
            **result,
            rc=e.rc,
            stdout=e.stdout,
            stderr=e.stderr,
        )
    module.exit_json(
        changed=True,
        **result,
    )


if __name__ == "__main__":
    main()
