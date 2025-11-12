#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Marc Crébassa <aalaesar@gmail.com>

import copy
import os
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect
        new_module_args = copy.deepcopy(self._task.args)

        # missing occ common arguments fallback
        # argument value precedence: args > task_vars > environment
        nextcloud_path = (
            self._task.args.get("nextcloud_path")
            or task_vars.get("nextcloud_path")
            or os.getenv("NEXTCLOUD_PATH")
        )
        if nextcloud_path:
            new_module_args["nextcloud_path"] = nextcloud_path
        elif "nextcloud_path" in new_module_args:
            del new_module_args["nextcloud_path"]

        # argument value precedence: args > task_vars > environment > default
        php_runtime = (
            self._task.args.get("php_runtime")
            or task_vars.get("nextcloud_php_runtime")
            or os.getenv("NEXTCLOUD_PHP_RUNTIME")
        )
        if php_runtime:
            new_module_args["php_runtime"] = php_runtime
        elif "php_runtime" in new_module_args:
            del new_module_args["php_runtime"]

        return self._execute_module(
            module_name=self._task.action,
            module_args=new_module_args,
            task_vars=task_vars,
        )
