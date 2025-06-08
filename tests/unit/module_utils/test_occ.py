from ansible_collections.nextcloud.admin.plugins.module_utils.occ import (
    convert_string,
    run_occ,
)
import ansible_collections.nextcloud.admin.plugins.module_utils.occ_exceptions as occ_exceptions
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


class TestRunOcc(unittest.TestCase):

    def setUp(self):
        # Mock the module object with necessary parameters
        self.module = MagicMock()
        self.module.params = {
            "nextcloud_path": "/path/to/nextcloud",
            "php_runtime": "/usr/bin/php",
        }

    @patch("os.stat")
    @patch("os.getuid")
    @patch("os.setgid")
    @patch("os.setuid")
    def test_run_occ_success(self, mock_setuid, mock_setgid, mock_getuid, mock_stat):
        # Setup mocks
        mock_stat.return_value.st_uid = 1000
        mock_stat.return_value.st_gid = 1000
        mock_getuid.return_value = 1001
        self.module.run_command.return_value = (0, "Success", "")

        # Call the function
        returnCode, stdOut, stdErr, maintenanceMode = run_occ(self.module, "status")

        # Assertions
        self.assertEqual(returnCode, 0)
        self.assertEqual(stdOut, "Success")
        self.assertEqual(stdErr, "")
        self.assertFalse(maintenanceMode)
        mock_setgid.assert_called_once_with(1000)
        mock_setuid.assert_called_once_with(1000)

    @patch("os.stat")
    @patch("os.getuid")
    def test_run_occ_maintenance_mode(self, mock_getuid, mock_stat):
        # Setup mocks
        mock_stat.return_value.st_uid = 1000
        mock_stat.return_value.st_gid = 1000
        mock_getuid.return_value = 1000
        self.module.run_command.return_value = (
            0,
            "",
            "Nextcloud is in maintenance mode, no apps are loaded.",
        )

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

    @patch("os.stat")
    @patch("os.getuid", return_value=1000)
    def test_file_not_found_exception(self, mock_getuid, mock_stat):
        # Simulate FileNotFoundError when accessing the occ file
        mock_stat.side_effect = FileNotFoundError

        with self.assertRaises(occ_exceptions.OccFileNotFoundException):
            run_occ(self.module, "status")

    @patch("os.stat")
    @patch("os.setuid")
    @patch("os.setgid")
    @patch("os.getuid", return_value=1000)
    def test_authentication_exception(
        self, mock_getuid, mock_setgid, mock_setuid, mock_stat
    ):
        # Simulate PermissionError when trying to change user
        mock_stat.return_value.st_uid = 2000
        mock_stat.return_value.st_gid = 2000
        mock_setuid.side_effect = PermissionError

        with self.assertRaises(occ_exceptions.OccAuthenticationException):
            run_occ(self.module, "status")

    @patch("os.stat")
    @patch("os.setuid")
    @patch("os.setgid")
    @patch("os.getuid", return_value=1000)
    def test_no_commands_defined_exception(
        self, mock_getuid, mock_setgid, mock_setuid, mock_stat
    ):
        # Mock successful stat call and simulate command execution error
        mock_stat.return_value.st_uid = 1000
        mock_stat.return_value.st_gid = 1000
        self.module.run_command.return_value = (1, "", "Command 'foo' is not defined.")

        with self.assertRaises(occ_exceptions.OccNoCommandsDefined):
            run_occ(self.module, "foo")

    @patch("os.stat")
    @patch("os.setuid")
    @patch("os.setgid")
    @patch("os.getuid", return_value=1000)
    def test_not_enough_arguments_exception(
        self, mock_getuid, mock_setgid, mock_setuid, mock_stat
    ):
        # Mock successful stat call and simulate command execution error
        mock_stat.return_value.st_uid = 1000
        mock_stat.return_value.st_gid = 1000
        self.module.run_command.return_value = (
            1,
            "",
            'Not enough arguments (missing: "bar").',
        )

        with self.assertRaises(occ_exceptions.OccNotEnoughArguments):
            run_occ(self.module, "foo")

    @patch("os.stat")
    @patch("os.setuid")
    @patch("os.setgid")
    @patch("os.getuid", return_value=1000)
    def test_option_not_defined_exception(
        self, mock_getuid, mock_setgid, mock_setuid, mock_stat
    ):
        # Mock successful stat call and simulate command execution error
        mock_stat.return_value.st_uid = 1000
        mock_stat.return_value.st_gid = 1000
        self.module.run_command.return_value = (
            1,
            "",
            "The option '--baz' does not exist.",
        )

        with self.assertRaises(occ_exceptions.OccOptionNotDefined):
            run_occ(self.module, "foo --baz")

    @patch("os.stat")
    @patch("os.setuid")
    @patch("os.setgid")
    @patch("os.getuid", return_value=1000)
    def test_option_requires_value_exception(
        self, mock_getuid, mock_setgid, mock_setuid, mock_stat
    ):
        # Mock successful stat call and simulate command execution error
        mock_stat.return_value.st_uid = 1000
        mock_stat.return_value.st_gid = 1000
        self.module.run_command.return_value = (
            1,
            "",
            "The option '--baz' requires a value.",
        )

        with self.assertRaises(occ_exceptions.OccOptionRequiresValue):
            run_occ(self.module, "foo --baz")

    @patch("os.stat")
    @patch("os.setuid")
    @patch("os.setgid")
    @patch("os.getuid", return_value=1000)
    def test_empty_msg_exception(
        self, mock_getuid, mock_setgid, mock_setuid, mock_stat
    ):
        # Mock successful stat call and simulate command execution error
        mock_stat.return_value.st_uid = 1000
        mock_stat.return_value.st_gid = 1000
        self.module.run_command.return_value = (
            1,
            "",
            "",
        )

        with self.assertRaises(occ_exceptions.OccExceptions):
            run_occ(self.module, "foo --baz")


if __name__ == "__main__":
    unittest.main()
