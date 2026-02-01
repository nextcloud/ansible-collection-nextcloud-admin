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
    IdentityNotPresent,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools import run_occ  # type: ignore


class idState(Enum):
    """
    Enumeration representing the state of a NextCloud identity.
    """

    PRESENT = "present"
    DISABLED = "disabled"
    ABSENT = "absent"


class NCIdentity:
    """
    Base class for managing NextCloud identities such as users and groups.

    Attributes:
        ident (str): The identifier for the identity.
        module: The Ansible module instance.
        namespace (str): The NextCloud namespace for the identity.
        infos (dict): A dictionary holding information about the identity.
        state (idState): The current state of the identity.
    """

    def __init__(self, module, namespace, ident: str):
        """
        Initialize a new NextCloud identity instance.

        Args:
            module: The Ansible module instance.
            namespace (str): The NextCloud namespace for the identity.
            ident (str): The identifier for the identity.

        Raises:
            OccExceptions: If an error occurs while fetching information from NextCloud.
        """
        self.ident = ident
        self.module = module
        self.namespace = namespace
        try:
            stdout = run_occ(
                self.module, [f"{self.namespace}:info", "--output=json", self.ident]
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
                self.infos = {}
            else:
                raise e

    def __take_action__(self, action: str, *args, **kwargs):
        """
        Internal method to execute a NextCloud OCC command with the given action.

        Args:
            action (str): The action to perform on the identity.
            *args: Additional positional arguments for the OCC command.
            **kwargs: Additional keyword arguments for the OCC command.
        """
        command = [f"{self.namespace}:{action}", "--no-interaction"] + list(args)
        run_occ(self.module, command + [self.ident], **kwargs)[0:3]

    def add(self):
        """
        Add the identity to NextCloud.
        """
        self.__take_action__("add")
        self.state = idState.PRESENT

    def delete(self):
        """
        Delete the identity from NextCloud.
        """
        self.__take_action__("delete")
        self.state = idState.ABSENT


class Group(NCIdentity):
    """
    Class for managing NextCloud groups.

    Inherits from NCIdentity.
    """

    __users__ = None

    def __init__(self, module, ident: str):
        """
        Initialize a new NextCloud group instance.

        Args:
            module: The Ansible module instance.
            ident (str): The identifier for the group.
        """
        super().__init__(module, "group", ident)
        if self.state is idState.PRESENT:
            self.__users__ = self.__get_users__()

    def __get_users__(self):
        stdout = run_occ(
            self.module, ["group:list", self.ident, "--output", "json_pretty"]
        )[1]
        return json.loads(stdout)[self.ident]

    @property
    def users(self):
        if self.__users__ is None:
            self.__users__ = self.__get_users__()
        return self.__users__

    def __user_mgnt__(self, action: str, user_id: str):
        """
        Internal method to manage group membership in NextCloud.

        Args:
            action (str): The action to perform (adduser or removeuser).
            user_id (str): The user identifier to add or remove from the group.
        """
        command = [f"group:{action}", "--no-interaction"]
        try:
            run_occ(self.module, command + [self.ident, user_id])
        except OccExceptions as e:
            if "not found" in e.stdout or "does not exist" in e.stdout:
                raise IdentityNotPresent("user", user_id, **e.__dict__)
            else:
                raise e

    def add(self, display_name: str | None = None):
        """
        Add the group to NextCloud, optionally with a display name.

        Args:
            display_name (str | None): The display name for the group.
        """
        if display_name:
            self.__take_action__("add", f"--display-name='{display_name}'")
        else:
            self.__take_action__("add")
        self.state = idState.PRESENT
        self.__users__ = []

    def add_user(self, user_id: str):
        """
        Add a user to the group.

        Args:
            user_id (str): The user identifier to add to the group.
        """
        self.__user_mgnt__("adduser", user_id)
        self.__users__ += [user_id]

    def remove_user(self, user_id: str):
        """
        Remove a user from the group.

        Args:
            user_id (str): The user identifier to remove from the group.
        """
        self.__user_mgnt__("removeuser", user_id)
        self.__users__.remove(user_id)


class User(NCIdentity):
    """
    Class for managing NextCloud users.

    Inherits from NCIdentity.
    """

    def __init__(self, module, ident: str):
        """
        Initialize a new NextCloud user instance.

        Args:
            module: The Ansible module instance.
            ident (str): The identifier for the user.
        """
        super().__init__(module, "user", ident)

    @property
    def groups(self):
        return self.infos.get("groups", [])

    def add(
        self,
        generate_password: bool = False,
        password: str | None = None,
        display_name: str | None = None,
        groups: list[str] | None = None,
        email: str | None = None,
    ):
        """
        Add the user to NextCloud with specified attributes.

        Args:
            password (str | None): The password for the user.
            display_name (str | None): The display name for the user.
            groups (list[str] | None): A list of groups to which the user will be added.
            email (str | None): The email address for the user.
            generate_password (bool): Whether to generate a password for the user.

        Raises:
            ValueError: If neither a password is provided nor password generation is requested.
        """
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
            self.module, command + [self.ident], environ_update=env
        )[0:3]

        if display_name:
            self.infos["display_name"] = display_name
        if email:
            self.infos["email"] = email
        if groups:
            self.infos["groups"] = groups
        self.state = idState.PRESENT

    def disable(self):
        """
        Disable the user account in NextCloud.
        """
        self.__take_action__("disable")
        self.state = idState.DISABLED

    def enable(self):
        """
        Enable the user account in NextCloud.
        """
        self.__take_action__("enable")
        self.state = idState.PRESENT

    def reset_password(self, password: str | None = None):
        """
        Reset the password for the user.

        Args:
            password (str|None): The new password for the user. If not provided, the user will have to login to change its password.
        """
        args = ["resetpassword"]
        env = {}
        if password:
            args += ["--password-from-env"]
            env = dict(NC_PASS=password)
        self.__take_action__(*args, environ_update=env)

    def edit_settings(
        self,
        key: str,
        value: str | None = None,
        error_if_not_exists: bool = False,
        update_only: bool = False,
    ):
        """
        Edit settings for the user.

        Args:
            key (str): The setting key to modify.
            value (str | None): The new value for the setting. If None, the setting is deleted.
            error_if_not_exists (bool): Whether to throw an error if the setting does not exist.
            update_only (bool): Whether to only update the setting if it already exists.
        """
        command = ["user:setting"]
        if error_if_not_exists:
            command += ["--error-if-not-exists"]
        if update_only:
            command += ["--update-only"]
        if value is None:
            command += ["--delete", self.ident, "settings", key]
        else:
            command += [self.ident, "settings", key, value]
        run_occ(self.module, command)
