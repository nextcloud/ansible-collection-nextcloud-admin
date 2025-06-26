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


class NextcloudException(Exception):
    """
    Base class for all Nextcloud-related exceptions

    Attributes:
        msg (str): Human-readable message describing the error.
        rc (int, optional): Return code of the command that caused the exception, if applicable.
        stdout (str, optional): Standard output from the command.
        stderr (str, optional): Standard error output from the command.
    """

    def __init__(self, msg="", rc=None, stdout=None, stderr=None, **kwargs):
        super().__init__(msg)
        self.rc = rc
        self.stdout = stdout
        self.stderr = stderr
        for key, value in kwargs.items():
            setattr(self, key, value)

    def fail_json(self, module, **result):
        """
        Fail the Ansible module with relevant debug information.

        Args:
            module: The AnsibleModule instance.
            result: Any extra result data to include.
        """
        module.fail_json(
            msg=str(self),
            exception_class=type(self).__name__,
            **result,
            **self.__dict__,
        )


class OccExceptions(NextcloudException):
    """
    Exception raised for errors related to occ command execution.

    Attributes:
        occ_cmd (str): The occ command that triggered the error.
    """

    def __init__(self, occ_cmd=None, **kwargs):
        if "msg" not in kwargs:
            kwargs["msg"] = "Failure when executing provided occ command."
        super().__init__(**kwargs)
        if occ_cmd:
            self.occ_cmd = occ_cmd


class OccFileNotFoundException(OccExceptions):
    """Raised when the occ command file is not found."""

    pass


class OccNoCommandsDefined(OccExceptions):
    """Raised when the command passed to occ is not defined in the Nextcloud instance."""

    pass


class OccOptionNotDefined(OccExceptions):
    """Raised when an invalid option is passed to an occ command."""

    pass


class OccNotEnoughArguments(OccExceptions):
    """Raised when not enough arguments are supplied to an occ command."""

    pass


class OccOptionRequiresValue(OccExceptions):
    """Raised when an option passed to occ requires a value but none was provided."""

    pass


class OccAuthenticationException(OccExceptions):
    """Raised when authentication fails during occ command execution."""

    pass


class PhpInlineExceptions(NextcloudException):
    """Base exception for php run in the nextcloud server."""

    pass


class PhpScriptException(PhpInlineExceptions):
    """Raised when a php script return an error."""

    pass


class PhpResultJsonException(PhpInlineExceptions):
    """Exception raised for php script results failing python's json deserialization."""

    pass


class AppExceptions(NextcloudException):
    """
    Base exception for app-related errors in Nextcloud.

    Attributes:
        app_name (str): The name of the app that triggered the error.
    """

    def __init__(self, **kwargs):
        if "app_name" not in kwargs:
            raise KeyError("Missing required 'app_name' for AppExceptions")
        app_name = kwargs["app_name"]
        if "msg" not in kwargs:
            if "dft_msg" in kwargs:
                base_msg = kwargs.pop("dft_msg")
                err_full_msg = f"{base_msg} for app '{app_name}'"
            else:
                err_full_msg = f"Unexpected error for app '{app_name}'"
            super().__init__(msg=err_full_msg, **kwargs)
        else:
            super().__init__(**kwargs)


class AppPSR4InfosUnavailable(AppExceptions):
    """Raised when an app does not expose proper PSR4 Infos"""

    def __init__(self, **kwargs):
        super().__init__(dft_msg="PSR-4 infos not available", **kwargs)


class AppPSR4InfosNotReadable(AppExceptions):
    """Raised when an app's getForm() method returns invalid JSON."""

    def __init__(self, **kwargs):
        super().__init__(dft_msg="PSR-4 infos are invalid JSON", **kwargs)
