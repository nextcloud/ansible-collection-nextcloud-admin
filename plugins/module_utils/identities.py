#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Marc Crébassa <aalaesar@gmail.com>
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

from __future__ import annotations
import json
from enum import Enum
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    OccExceptions,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools import run_occ  # type: ignore


class idState(Enum):
    PRESENT = "present"
    DISABLED = "disabled"
    ABSENT = "absent"


class NCIdentity:
    def __init__(self, module, domain, ident: str):
        self.ident = ident
        self.module = module
        self.domain = domain
        try:
            stdout = run_occ(
                self.module, [f"{self.domain}:info", "--output=json", self.ident]
            )[1]
            self.infos = json.loads(stdout)
            if self.infos["enabled"]:
                self.state = idState.PRESENT
            else:
                self.state = idState.DISABLED
        except KeyError:
            self.state = idState.PRESENT
        except OccExceptions as e:
            if "not found" in e.stdout or "does not exist" in e.stdout:
                self.state = idState.ABSENT
            else:
                raise e

    def __take_action__(self, action: str, *args, **kwargs):
        command = [f"{self.domain}:{action}", "--no-interaction"] + list(args)
        rc, stdout, stderr = run_occ(self.module, command + [self.ident], **kwargs)[0:3]
        return rc, stdout, stderr

    def add(self):
        self.__take_action__("add")
        self.state = idState.PRESENT

    def delete(self):
        self.__take_action__("delete")
        self.state = idState.ABSENT


class Group(NCIdentity):
    def __init__(self, module, ident: str):
        super().__init__(module, "group", ident)

    def __user_mgnt__(self, action: str, user_id: str):
        command = [f"group:{action}", "--no-interaction"]
        run_occ(self.module, command + [self.ident, user_id])[0:3]

    def add(self, display_name: str | None = None):
        if display_name:
            self.__take_action__("add", f"--display-name='{display_name}'")
        else:
            self.__take_action__("add")
        self.state = idState.PRESENT

    def add_user(self, user_id: str):
        self.__user_mgnt__("adduser", user_id)

    def remove_user(self, user_id: str):
        self.__user_mgnt__("removeuser", user_id)


class User(NCIdentity):
    def __init__(self, module, ident: str):
        super().__init__(module, "user", ident)

    def add(
        self,
        password: str | None = None,
        display_name: str | None = None,
        groups: list[str] | None = None,
        email: str | None = None,
        generate_password: bool = False,
    ):
        command = ["user:add", "--no-interaction"]
        env = {}

        if generate_password:
            command.append("--generate-password")
        elif password:
            command.append("--password-from-env")
            env["NC_PASS"] = password
        else:
            raise ValueError("Password required unless using generate-password")

        if display_name:
            command += ["--display-name", display_name]
        if email:
            command += ["--email", email]
        for group in groups or []:
            command += ["--group", group]

        rc, stdout, stderr = run_occ(
            self.module, command + [self.user_id], environ_update=env
        )[0:3]

        if display_name:
            self.infos["display_name"] = display_name
        if email:
            self.infos["email"] = email
        if groups:
            self.infos["groups"] = groups
        self.state = idState.PRESENT

    def disable(self):
        self.__take_action__("disable")
        self.state = idState.DISABLED

    def enable(self):
        self.__take_action__("enable")
        self.state = idState.PRESENT
