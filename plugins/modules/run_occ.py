#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Marc Crébassa <@aalaesar>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
  - Because occ requires to be run as its owner,
    this module can requires to be run with privileges to be able to switch user,
    unless `become_user` is used to run the task directly as the proper user.
  - Don't support check mode.
  - Always returns state as 'changed'.

extends_documentation_fragment:
  - aalaesar.nextcloud.occ_common_options

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
  aalaesar.nextcloud.run_occ:
    command: status --output=json
    nextcloud_path: /var/lib/www/nextcloud
  changed_when: false
  register: nc_status

- name: install an application
  aalaesar.nextcloud.run_occ:
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

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.aalaesar.nextcloud.plugins.module_utils.occ import run_occ

def args_spec():
  args=dict(
    path=dict(
      type='str',
      required=True,
    ),
    command=dict(
      type='str',
      required=True,
    ),
    php=dict(
      type='str',
      required=False,
      default='php',
    ),
  )
  return args

def main():
  global module

  module = AnsibleModule(
    argument_spec=args_spec(),
    supports_check_mode=False,
  )
  command = module.params.get('command')
  returnCode, stdOut, stdErr = run_occ(module, command)
  result=dict(
    command=command,
    rc = returnCode,
    stdout = stdOut,
    stderr = stdErr,
  )
  if returnCode != 0:
    module.fail_json(
      msg="Failure when executing occ command. Exited {0}.\nstdout: {1}\nstderr: {2}".format(
          returnCode, stdOut, stdErr
      ),
        **result,
    )
  else:
    module.exit_json(
      changed = True,
      **result,
    )

if __name__ == "__main__":
  main()
