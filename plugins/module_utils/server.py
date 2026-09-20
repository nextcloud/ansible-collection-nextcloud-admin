#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Marc Crébassa <aalaesar@gmail.com>
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
from typing import cast, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ansible.module_utils.basic import AnsibleModule

import json

from ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools import run_occ
from ansible_collections.nextcloud.admin.plugins.module_utils.app import NCApp
from ansible_collections.nextcloud.admin.plugins.module_utils.identities import (
    NCGroup,
    NCUser,
)


class NCServer:

    def __init__(self, module: AnsibleModule) -> None:

        self._occ_commands: dict[str, list[str]] = {}
        self._setupChecks: dict[str, dict[str, list[dict[str, str | None]]]] = {}
        self._apps: dict[str, dict[str, dict[str, str]]] = {
            "shipped": {},
            "external": {},
        }
        self.module = module
        status: dict[str, str] = json.loads(
            run_occ(
                self.module, command=["status", "--output", "json", "--no-warnings"]
            )[1]
        )
        for key, value in status.items():
            setattr(self, key, value)

    def occ(self, command: str | list[str], **kwargs) -> tuple[int, str, str, bool]:
        return run_occ(self.module, command=command, **kwargs)

    def _get_occ_commands(self) -> dict[str, list[str]]:
        command_list: list[dict[str, Any]] = json.loads(
            self.occ(command=["list", "--format=json", "--no-warnings"])[1]
        ).get("namespaces")
        result = {
            cast(str, item["id"]): cast(list[str], item["commands"])
            for item in command_list
        }
        return result

    def _get_apps(self, shipped: bool = True) -> None:
        command_args = ["app:list", "--output=json", "--no-warning"]
        if shipped:
            command_args.append("--shipped")
        result: dict[str, dict[str, str]] = json.loads(
            self.occ(command=command_args)[1]
        )
        if shipped:
            self._apps["shipped"] = result
        else:
            self._apps["external"] = result

    def run_SetupChecks(self) -> None:
        setup_checks_report: dict[str, dict[str, dict[str, str | None]]] = json.loads(
            self.occ(command=["setupchecks", "--output=json", "--no-warning"])[1]
        )
        result: dict[str, dict[str, list[dict[str, str | None]]]] = {}
        for category, checks in setup_checks_report.items():
            for fqcn, check in checks.items():
                parts = fqcn.split("\\")
                app = parts[1]
                check_id = parts[-1]

                result.setdefault(category, {}).setdefault(app, []).append(
                    {
                        "id": check_id,
                        **check,
                    }
                )
        self._setupChecks = result

    def refresh_shipped_apps(self) -> None:
        self._get_apps(shipped=True)

    def refresh_external_apps(self) -> None:
        self._get_apps(shipped=False)

    def refresh_apps(self) -> None:
        self.refresh_shipped_apps()
        self.refresh_external_apps()

    @property
    def shipped_apps(self) -> dict[str, dict[str, str]]:
        if self._apps["shipped"] == {}:
            self.refresh_shipped_apps()
        return self._apps["shipped"]

    @property
    def external_apps(self) -> dict[str, dict[str, str]]:
        if self._apps["external"] == {}:
            self.refresh_external_apps()
        return self._apps["external"]

    @property
    def apps(self) -> dict[str, dict[str, str]]:
        return {
            "enabled": self.external_apps["enabled"] | self.shipped_apps["enabled"],
            "disabled": self.external_apps["disabled"] | self.shipped_apps["disabled"],
        }

    @property
    def occ_commands(self) -> dict[str, list[str]]:
        if self._occ_commands == {}:
            self._occ_commands = self._get_occ_commands()
        return self._occ_commands

    @property
    def setupChecks(self) -> dict[str, dict[str, list[dict[str, str | None]]]]:
        if self._setupChecks == {}:
            self.run_SetupChecks()
        return self._setupChecks

    def app(self, name: str) -> NCApp:
        return NCApp(self, app_name=name)

    def group(self, name: str) -> NCGroup:
        return NCGroup(self, ident=name)

    def user(self, name: str) -> NCUser:
        return NCUser(self, ident=name)
