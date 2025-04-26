#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Marc Crébassa <aalaesar@gmail.com>

import copy
import os
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect
        new_module_args = copy.deepcopy(self._task.args)
        new_module_args["nextcloud_path"] = self._task.args.get(
            "nextcloud_path", os.getenv("NEXTCLOUD_PATH")
        )
        if not new_module_args["nextcloud_path"]:
            del new_module_args["nextcloud_path"]

        return self._execute_module(
            module_name=self._task.action,
            module_args=new_module_args,
            task_vars=task_vars,
        )
