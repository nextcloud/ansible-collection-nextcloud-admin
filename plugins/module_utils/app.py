#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Marc Crébassa <aalaesar@gmail.com>
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

import json
from typing import Union
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    OccExceptions,
    AppExceptions,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools import run_occ  # type: ignore


class app:
    _update_version_available = "unchecked"
    _path = None

    def __init__(self, module, app_name: str):
        self.module = module
        self.app_name = app_name
        self.all_shipped_apps = json.loads(
            run_occ(module, ["app:list", "--output=json", "--shipped=true"])[1]
        )
        self.all_present_apps = json.loads(
            run_occ(module, ["app:list", "--output=json"])[1]
        )
        if app_name in self.all_present_apps["enabled"].keys():
            self.state = "present"
            self.version = self.all_present_apps["enabled"][app_name]
        elif app_name in self.all_present_apps["disabled"].keys():
            self.state = "disabled"
            self.version = self.all_present_apps["disabled"][app_name].split()[0]
        else:
            self.state = "absent"
            self.version = None
        self.shipped = app_name in [
            s
            for a in self.all_shipped_apps.keys()
            for s in self.all_shipped_apps[a].keys()
        ]

    @property
    def update_version_available(self) -> Union[str, None]:
        if self._update_version_available == "unchecked":
            _check_app_update = run_occ(
                self.module, ["app:update", "--showonly", self.app_name]
            )[1]
            if _check_app_update != "":
                result = _check_app_update.split()[-1]
            else:
                result = None
            self._update_version_available = result
        return self._update_version_available

    @property
    def update_available(self) -> bool:
        return isinstance(self.update_version_available, str)

    @property
    def path(self) -> str:
        if not self._path:
            result = run_occ(self.module, ["app:getpath", self.app_name])[1].strip()
        self._path = result
        return self._path

    def infos(self):
        result = dict(
            name=self.app_name,
            state=self.state,
            is_shipped=self.shipped,
        )
        if self.state != "absent":
            result.update(update_available=self.update_available)
            result.update(version=self.version)
            result.update(version_available=self.update_version_available)
            result.update(app_path=self.path)
        return result

    def install(self, enable: bool = True) -> tuple:
        occ_args = ["app:install", self.app_name]
        if not enable:
            occ_args.insert(1, "--keep-disabled")
        try:
            action_stdout = run_occ(self.module, occ_args)[1].splitlines()
        except OccExceptions as e:
            raise AppExceptions(
                msg=f"Error during {self.app_name} installation.",
                app_name=self.app_name,
                **e.__dict__,
            )

        version = action_stdout[0].split()[1]
        actions_taken = [a.split()[-1] for a in action_stdout]

        return version, actions_taken

    def remove(self) -> tuple:
        occ_args = ["app:remove", self.app_name]
        try:
            action_stdout = run_occ(self.module, command=occ_args)[1].splitlines()
        except OccExceptions as e:
            raise AppExceptions(
                msg=f"Error while removing {self.app_name}.",
                app_name=self.app_name,
                **e.__dict__,
            )

        removed_version = action_stdout[-1].split()[1]
        actions_taken = [a.split()[-1] for a in action_stdout]
        return (actions_taken, removed_version)

    def toggle(self) -> str:
        if self.state == "absent":
            raise AssertionError("Cannot enable/disable an absent application")
        if self.state == "disabled":
            new_state = "enable"
        else:
            new_state = "disable"
        try:
            action_stdout = run_occ(self.module, [f"app:{new_state}", self.app_name])[1]
            actions_taken = action_stdout.splitlines()[0].split()[-1]
            return actions_taken
        except OccExceptions as e:
            raise AppExceptions(
                msg=f"Error while trying to {new_state} {self.app_name}.",
                app_name=self.app_name,
                **e.__dict__,
            )

    def update(self) -> str:
        try:
            run_occ(self.module, ["app:update", self.app_name])
        except OccExceptions as e:
            raise AppExceptions(
                msg=f"Error while updating {self.app_name}.",
                app_name=self.app_name,
                **e.__dict__,
            )
        return self.update_version_available
