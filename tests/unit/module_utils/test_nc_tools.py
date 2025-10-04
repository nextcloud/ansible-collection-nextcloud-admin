from ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools import (
    convert_string,
    execute_occ_command,
    run_occ,
)
import ansible_collections.nextcloud.admin.plugins.module_utils.exceptions as occ_exceptions
import unittest
from unittest.mock import MagicMock, patch


class TestConvertString(unittest.TestCase):

    def test_basic_conversion(self):
        self.assertEqual(convert_string("hello world"), ["hello", "world"])

    def test_quotes_handling(self):
        self.assertEqual(convert_string('"hello" world'), ["hello", "world"])
        self.assertEqual(convert_string("'hello' world"), ["hello", "world"])

    def test_mixed_quotes(self):
        self.assertEqual(convert_string('"hello" world'), ["hello", "world"])
        self.assertEqual(convert_string("hello 'world'"), ["hello", "world"])

    def test_no_whitespace(self):
        self.assertEqual(convert_string("helloworld"), ["helloworld"])

    def test_empty_string(self):
        self.assertEqual(convert_string(""), [])

    def test_block_of_words(self):
        self.assertEqual(convert_string('"a block a words"'), ['"a block a words"'])

    def test_mixed_blocks(self):
        self.assertEqual(
            convert_string('a command with a "block of words"'),
            ["a", "command", "with", "a", '"block of words"'],
        )
        self.assertEqual(
            convert_string("a command with a 'block of words'"),
            ["a", "command", "with", "a", "'block of words'"],
        )

    def test_backslash_behaviour(self):
        self.assertEqual(
            convert_string(r'some "\special\parameter\separator"'),
            ["some", r"\special\parameter\separator"],
        )
        self.assertEqual(
            convert_string("some \\special\\parameter\\separator"),
            ["some", r"\special\parameter\separator"],
        )


class TestExecuteOccCommand(unittest.TestCase):
    def setUp(self):
        self.mock_conn = MagicMock()
        self.module = MagicMock()
        self.mock_stat = patch("os.stat").start()
        self.mock_getuid = patch("os.getuid").start()
        self.mock_getgid = patch("os.getgid").start()
        self.mock_setuid = patch("os.setuid").start()
        self.mock_setgid = patch("os.setgid").start()
        self.mock_stat.return_value.st_uid = 1234
        self.mock_stat.return_value.st_gid = 1234
        self.mock_getuid.return_value = 1234
        self.mock_getgid.return_value = 1234
        self.addCleanup(patch.stopall)
        self.module.run_command.return_value = (0, "output", "")

    def test_execute_occ_command_success(self):
        execute_occ_command(
            self.mock_conn, self.module, "/path/to/php", ["/path/to/occ", "command"]
        )

        self.mock_conn.send.assert_called_once_with(
            {"rc": 0, "stdout": "output", "stderr": ""}
        )

    def test_change_uid_execute_occ_command_success(self):
        self.mock_getuid.return_value = 0
        self.mock_getgid.return_value = 0

        execute_occ_command(
            self.mock_conn, self.module, "/path/to/php", ["/path/to/occ", "command"]
        )

        self.mock_conn.send.assert_called_once_with(
            {"rc": 0, "stdout": "output", "stderr": ""}
        )
        self.mock_setuid.assert_called_with(1234)
        self.mock_setgid.assert_called_with(1234)

    def test_occ_command_FileNotFoundError(self):
        self.mock_stat.side_effect = FileNotFoundError

        execute_occ_command(
            self.mock_conn, self.module, "/path/to/php", ["/path/to/occ", "command"]
        )

        self.mock_conn.send.assert_called_once_with(
            {"exception": "OccFileNotFoundException"}
        )

    def test_occ_command_PermissionError(self):
        self.mock_getuid.return_value = 0
        self.mock_getgid.return_value = 0
        self.mock_setuid.side_effect = PermissionError

        execute_occ_command(
            self.mock_conn, self.module, "/path/to/php", ["/path/to/occ", "command"]
        )

        self.mock_conn.send.assert_called_once_with(
            {
                "exception": "OccAuthenticationException",
                "msg": "Insufficient permissions to switch to user id 1234.",
            }
        )

    def test_occ_command_AnyError(self):
        self.mock_getuid.side_effect = Exception("TKIAL")

        execute_occ_command(
            self.mock_conn, self.module, "/path/to/php", ["/path/to/occ", "command"]
        )

        self.mock_conn.send.assert_called_once_with({"exception": "TKIAL"})


class TestRunOcc(unittest.TestCase):

    def setUp(self):
        # Mock the module object with necessary parameters
        self.module = MagicMock()
        self.module.params = {
            "nextcloud_path": "/path/to/nextcloud",
            "php_runtime": "/usr/bin/php",
        }

        self.mock_process = patch(
            "ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools.Process"
        ).start()
        self.mock_instance = self.mock_process.return_value
        self.mock_instance.start.return_value = None
        self.mock_instance.join.return_value = None

        self.mock_pipe_parent, self.mock_pipe_child = MagicMock(), MagicMock()
        patcher_pipe = patch(
            "ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools.Pipe",
            return_value=(self.mock_pipe_parent, self.mock_pipe_child),
        )
        patcher_pipe.start()

        self.mock_pipe_parent.recv.return_value = {
            "rc": 0,
            "stdout": "Success",
            "stderr": "",
        }

        self.addCleanup(patch.stopall)

    def test_run_occ_success(self):

        # Call the function
        returnCode, stdOut, stdErr, maintenanceMode = run_occ(self.module, "status")

        # Assertions
        self.assertEqual(returnCode, 0)
        self.assertEqual(stdOut, "Success")
        self.assertEqual(stdErr, "")
        self.assertFalse(maintenanceMode)

    def test_run_occ_maintenance_mode(self):
        # Setup mocks
        self.mock_pipe_parent.recv.return_value = {
            "rc": 0,
            "stdout": "",
            "stderr": "Nextcloud is in maintenance mode, no apps are loaded.",
        }

        # Call the function
        returnCode, stdOut, stdErr, maintenanceMode = run_occ(self.module, "status")

        # Assertions
        self.module.warn.assert_called_once_with(
            "Nextcloud is in maintenance mode, no apps are loaded."
        )
        self.assertEqual(returnCode, 0)
        self.assertEqual(stdOut, "")
        self.assertIn("maintenance mode", stdErr)
        self.assertTrue(maintenanceMode)

    def test_file_not_found_exception(self):
        # Simulate FileNotFoundError when accessing the occ file
        self.mock_pipe_parent.recv.return_value = {
            "exception": "OccFileNotFoundException",
            "msg": "",
        }

        with self.assertRaises(occ_exceptions.OccFileNotFoundException):
            run_occ(self.module, "status")

    def test_authentication_exception(self):
        # Simulate PermissionError when trying to change user
        self.mock_pipe_parent.recv.return_value = {
            "exception": "OccAuthenticationException",
            "msg": "",
        }

        with self.assertRaises(occ_exceptions.OccAuthenticationException):
            run_occ(self.module, "status")

    def test_no_commands_defined_exception(self):
        # simulate command execution error
        self.mock_pipe_parent.recv.return_value = {
            "rc": 1,
            "stdout": "",
            "stderr": "Command 'foo' is not defined.",
        }

        with self.assertRaises(occ_exceptions.OccNoCommandsDefined):
            run_occ(self.module, "foo")

    def test_not_enough_arguments_exception(self):
        # simulate command execution error
        self.mock_pipe_parent.recv.return_value = {
            "rc": 1,
            "stdout": "",
            "stderr": 'Not enough arguments (missing: "bar").',
        }
        with self.assertRaises(occ_exceptions.OccNotEnoughArguments):
            run_occ(self.module, "foo")

    def test_option_not_defined_exception(self):
        self.mock_pipe_parent.recv.return_value = {
            "rc": 1,
            "stdout": "",
            "stderr": "The option '--baz' does not exist.",
        }

        with self.assertRaises(occ_exceptions.OccOptionNotDefined):
            run_occ(self.module, "foo --baz")

    def test_option_requires_value_exception(self):
        self.mock_pipe_parent.recv.return_value = {
            "rc": 1,
            "stdout": "",
            "stderr": "The option '--baz' requires a value.",
        }

        with self.assertRaises(occ_exceptions.OccOptionRequiresValue):
            run_occ(self.module, "foo --baz")

    def test_empty_msg_exception(self):
        self.mock_pipe_parent.recv.return_value = {"rc": 1, "stdout": "", "stderr": ""}

        with self.assertRaises(occ_exceptions.OccExceptions):
            run_occ(self.module, "foo --baz")


if __name__ == "__main__":
    unittest.main()
