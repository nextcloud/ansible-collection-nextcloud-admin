#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Marc Crébassa <aalaesar@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

OCC_ARGS_SPEC = dict(
  nextcloud_path = dict(
    type = "str",
    required = True,
    aliases = ["path", "nc_path", "nc_dir"]
  ),
  php_runtime=dict(
    type="str",
    required = False,
    default = "php",
    aliases = ["php"]
  ),
)
