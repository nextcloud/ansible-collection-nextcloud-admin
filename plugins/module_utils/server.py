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
    installed: bool
    version: str
    versionstring: str
    edition: None | str
    maintenance: bool
    needsDbUpgrade: bool
    productname: str
    extendedSupport: bool

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

    def set_maintenance(self, enabled: bool) -> None:
        if self.maintenance == enabled:
            return
        command = [
            "maintenance:mode",
            "--on" if enabled else "--off",
            "--no-interaction",
            "--no-warnings",
        ]
        self.occ(command)
        self.maintenance = enabled

    def install(self, **kwargs: str | int | bool) -> None:
        """
        Installs Nextcloud with the specified parameters.

        This method performs the initial installation of Nextcloud by configuring
        the database, administrator accounts and the data directory.

        Args:
            **kwargs: Arguments that can be passed to the install command.
                These include:
                - database_type (str, optional): Database type (e.g. 'mysql', 'pgsql'). Defaults to None.
                - database_name (str, optional): Name of the database. Defaults to None.
                - database_host (str, optional): Database host. Defaults to None.
                - database_port (int, optional): Database port. Defaults to None.
                - database_user (str, optional): Database username. Defaults to None.
                - database_pass (str, optional): Database password. Defaults to None.
                - database_table_space (str, optional): Database table space (oci only). Defaults to None.
                - admin_user (str, optional): Administrator username. Defaults to None.
                - admin_pass (str, optional): Administrator password. Defaults to None.
                - admin_email (str, optional): Administrator email address. Defaults to None.
                - data_dir (str): Path to Nextcloud data directory.
                The following arguments may be available depending on the version of Nextcloud:
                - disable_admin_user (bool): Disable the creation of an admin user. Defaults to False.
                - database_ssl_mode (str): Encryption mode for the database connection (pgsql only).
                - database_ssl_ca (str): Path to CA certificate (mysql and pgsql only).
                - database_ssl_cert (str): Path to client certificate (mysql and pgsql only).
                - database_ssl_key (str): Path to private key of client certificate (mysql and pgsql only).
                - database_ssl_crl (str): Path to certificate revocation list (pgsql only).
                - database_ssl_no_verify (bool): Do not verify server certificate (mysql only). Defaults to False.
                - password_salt (str): Password salt, at least 32 characters.
                - server_secret (str): Server secret, at least 48 characters.

        Returns:
            None

        Raises:
            RuntimeError: If Nextcloud is already installed.

        Note:
            This method can only be called if Nextcloud is not yet installed.
            The kwargs parameters are version-dependent and may not be available
            in all versions of Nextcloud.

        Examples:
            >>> server.install(
            ...     database_type="mysql",
            ...     database_name="nextcloud",
            ...     database_user="nc_user",
            ...     database_pass="password",
            ...     admin_user="admin",
            ...     admin_pass="admin_password",
            ...     data_dir="/var/www/nextcloud/data"
            ... )
        """

        if self.installed:
            raise RuntimeError("Nextcloud is already installed")

        occ_args = ["--no-interaction", "--no-warnings"]

        for bool_param in ("disable_admin_user", "database_ssl_no_verify"):
            param_value = kwargs.pop(bool_param, False)
            if param_value:
                occ_args.append(f"--{bool_param.replace('_', '-')}")

        occ_args.extend(
            arg
            for k, v in kwargs.items()
            if v is not False
            for arg in (
                [f"--{k.replace('_', '-')}"]
                if v is True
                else [f"--{k.replace('_', '-')}", str(v)]
            )
        )
        self.occ(["maintenance:install"] + occ_args)
