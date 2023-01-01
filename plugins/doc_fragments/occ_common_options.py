#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Marc Crébassa <aalaesar@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

class ModuleDocFragment(object):
    # Standard documentation
    DOCUMENTATION = r'''
options:
  nextcloud_path:
    description:
      - Specify the nextcloud instance's location in the host.
      - If not given, the module can't use the occ tool.
    type: str
    aliases:
      - path
      - nc_path
      - nc_dir
  php_runtime:
    description:
      - Specify the php runtime used to run the occ tool.
      - Can be an absolute or relative path if the runtime is available in the PATH.
    type: str
    default: php
    aliases:
      - php
'''
