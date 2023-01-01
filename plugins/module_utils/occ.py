#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Marc Crébassa <aalaesar@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
# import json


def run_occ(module, command, ):
  cli_full_path = module.params.get('nextcloud_path') + '/occ'
  php_exec = module.params.get('php_runtime')
  cli_stats = os.stat(cli_full_path)
  
  if os.getuid() != cli_stats.st_uid:
    os.setgid(cli_stats.st_gid)
    os.setuid(cli_stats.st_uid)

  if isinstance(command, list):
    full_command = [cli_full_path] + command
  elif isinstance(command, str):
    full_command = [cli_full_path] + command.split(' ')

  returnCode, stdOut, stdErr = module.run_command([php_exec] + full_command)

  if returnCode != 0:
    module.fail_json(
      msg="Failure when executing occ command. Exited {0}.\nstdout: {1}\nstderr: {2}".format(
        returnCode, stdOut, stdErr),
      stdout=stdOut,
      stderr=stdErr,
      command=command,
      )
  return returnCode, stdOut, stdErr
