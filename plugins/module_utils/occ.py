#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Marc Crébassa <aalaesar@gmail.com>
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

import os


def run_occ(
    module,
    command,
):
    cli_full_path = module.params.get("nextcloud_path") + "/occ"
    php_exec = module.params.get("php_runtime")
    cli_stats = os.stat(cli_full_path)

    if os.getuid() != cli_stats.st_uid:
        os.setgid(cli_stats.st_gid)
        os.setuid(cli_stats.st_uid)

    if isinstance(command, list):
        full_command = [cli_full_path] + command
    elif isinstance(command, str):
        full_command = [cli_full_path] + command.split(" ")

    returnCode, stdOut, stdErr = module.run_command([php_exec] + full_command)

    if returnCode != 0:
        module.fail_json(
            msg="Failure when executing occ command. Exited {0}.\nstdout: {1}\nstderr: {2}".format(
                returnCode, stdOut, stdErr
            ),
            stdout=stdOut,
            stderr=stdErr,
            command=command,
        )
    return returnCode, stdOut, stdErr
