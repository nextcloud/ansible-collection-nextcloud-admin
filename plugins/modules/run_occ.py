#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Marc Crébassa <aalaesar@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
