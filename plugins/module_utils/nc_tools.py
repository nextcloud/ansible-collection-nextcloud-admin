#!/usr/bin/env python
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

from __future__ import annotations
import os
import json
import copy
from multiprocessing import Process, Pipe
from textwrap import dedent
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    OccExceptions,
    OccAuthenticationException,
    OccFileNotFoundException,
    OccNoCommandsDefined,
    OccNotEnoughArguments,
    OccOptionRequiresValue,
    OccOptionNotDefined,
    PhpInlineExceptions,
    PhpScriptException,
    PhpResultJsonException,
)
from shlex import shlex
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from ansible.module_utils.basic import AnsibleModule


NC_TOOLS_ARGS_SPEC = dict(
    nextcloud_path=dict(
        type="str", required=True, aliases=["path", "nc_path", "nc_dir"]
    ),
    php_runtime=dict(type="str", required=False, default="php", aliases=["php"]),
)


def extend_nc_tools_args_spec(some_module_spec):
    arg_spec = copy.deepcopy(NC_TOOLS_ARGS_SPEC)
    arg_spec.update(some_module_spec)
    return arg_spec


def convert_string(command: str) -> list[str]:
    command_lex = shlex(instream=command, posix=False)
    command_lex.whitespace_split = True
    command_lex.commenters = ""
    command_lex.escape = ""
    command_lex.quotes = "\"'"
    return [token.strip("\"'") for token in command_lex]


def execute_occ_command(
    conn, module: AnsibleModule, php_exec: str, command: list[str], **kwargs
) -> None:
    """
    Execute a given occ command using the PHP interpreter and handle user permissions.

    This function attempts to runs occ through the PHP interpreter with
    the appropriate user permissions. It checks if the current user has the same
    UID as the owner of the occ file, switches to that user if necessary,
    and runs the command. The output of the command execution along with any
    errors are sent back via the provided connection object.

    Parameters:
    - conn (multiprocessing.connection.Connection): The connection object used for communication.
    - module (AnsibleModule): An object providing methods for running commands.
    - php_exec (str): The path to the PHP executable.
    - command (list): A list where the first element is 'occ' with its full path.

    Raises:
    - OccFileNotFoundException: If the command file does not exist.
    - OccAuthenticationException: If there are insufficient permissions to switch the user.

    Returns:
    None: This function does not return anything. It sends the results or exceptions through the conn object.
    """

    try:
        cli_stats = os.stat(command[0])
        if os.getuid() != cli_stats.st_uid:
            os.setgid(cli_stats.st_gid)
            os.setuid(cli_stats.st_uid)

        rc, stdout, stderr = module.run_command([php_exec] + command, **kwargs)
        conn.send({"rc": rc, "stdout": stdout, "stderr": stderr})
    except FileNotFoundError:
        conn.send({"exception": "OccFileNotFoundException"})
    except PermissionError:
        conn.send(
            {
                "exception": "OccAuthenticationException",
                "msg": f"Insufficient permissions to switch to user id {cli_stats.st_uid}.",  # pyright: ignore[reportPossiblyUnboundVariable]
            }
        )
    except Exception as e:
        conn.send({"exception": str(e)})
    finally:
        conn.close()


def run_occ(
    module: AnsibleModule, command: str | list[str], **kwargs
) -> tuple[int, str, str, bool]:
    cli_full_path: str = module.params.get("nextcloud_path") + "/occ"
    php_exec: str = module.params.get("php_runtime")
    if isinstance(command, list):
        full_command = [cli_full_path, "--no-ansi", "--no-interaction"] + command
    elif isinstance(command, str):
        full_command = [
            cli_full_path,
            "--no-ansi",
            "--no-interaction",
        ] + convert_string(command)

    # execute the occ command in a child process to keep current privileges
    module_conn, occ_conn = Pipe()
    p = Process(
        target=execute_occ_command,
        args=(occ_conn, module, php_exec, full_command),
        kwargs=kwargs,
    )
    p.start()
    result: dict[str, Any] = module_conn.recv()
    p.join()

    # check if the child process has sent an exception.
    if "exception" in result:
        exception_type = cast(str, result["exception"])
        # raise the proper exception.
        if exception_type == "OccFileNotFoundException":
            raise OccFileNotFoundException(full_command)
        elif exception_type == "OccAuthenticationException":
            raise OccAuthenticationException(full_command, **result)
        else:
            raise OccExceptions(f"An unknown error occurred: {exception_type}")

    if "is in maintenance mode" in result["stderr"]:
        module.warn(" ".join(result["stderr"].splitlines()[0:1]))
        maintenanceMode = True
    else:
        maintenanceMode = False

    if "is not installed" in result["stderr"]:
        module.warn(result["stderr"].splitlines()[0])

    output = result["stderr"] or result["stdout"]
    if result["rc"] != 0 and output:
        error_msg = convert_string(output.strip().splitlines()[0])
        if all(x in error_msg for x in ["Command", "is", "not", "defined."]):
            raise OccNoCommandsDefined(full_command, **result)
        elif all(x in error_msg for x in ["Not", "enough", "arguments"]):
            raise OccNotEnoughArguments(full_command, **result)
        elif all(x in error_msg for x in ["option", "does", "not", "exist."]):
            raise OccOptionNotDefined(full_command, **result)
        elif all(x in error_msg for x in ["option", "requires", "value."]):
            raise OccOptionRequiresValue(full_command, **result)
        else:
            raise OccExceptions(full_command, **result)
    elif result["rc"] != 0:
        raise OccExceptions(full_command, **result)

    return (
        cast(int, result["rc"]),
        cast(str, result["stdout"]),
        cast(str, result["stderr"]),
        maintenanceMode,
    )


def run_php_inline(module: AnsibleModule, php_code: str) -> dict[str, Any]:
    """
    Interface with Nextcloud server through ad-hoc php scripts.
    The script must define the var $result that will be exported into a python dict
    """
    if isinstance(php_code, list):
        php_code = "\n".join(php_code)
    elif isinstance(php_code, str):
        php_code = dedent(php_code).strip()
    else:
        raise Exception("php_code must be a list or a string")

    full_code = f"""
    require_once 'lib/base.php';
    {php_code}
    if (!isset($result)) {{
        $result = null;
    }}
    echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    """
    rc, stdout, stderr = module.run_command(
        [module.params.get("php_runtime"), "-r", full_code],
        cwd=module.params.get("nextcloud_path"),
    )
    if rc != 0:
        raise PhpScriptException(
            msg="Failed to run the given php script.",
            stderr=stderr,
            stdout=stdout,
            rc=rc,
            php_script=full_code,
        )

    stdout = stdout.strip()
    try:
        result: dict[str, Any] = (
            json.loads(stdout) if stdout and stdout != "null" else {}
        )
        return result
    except json.JSONDecodeError as e:
        raise PhpResultJsonException(
            msg="Failed to decode JSON from php script stdout",
            stderr=stderr,
            stdout=stdout,
            rc=rc,
            JSONDecodeError=str(e),
        )
    except Exception:
        raise PhpInlineExceptions(stderr=stderr, stdout=stdout, rc=rc)
