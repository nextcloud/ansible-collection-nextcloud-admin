from ansible_collections.nextcloud.admin.plugins.module_utils.occ import (
    convert_string,
    run_occ,
)
import unittest
from unittest.mock import Mock, patch


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

    @patch("os.stat")
    @patch("os.getuid")
    @patch("os.setgid")
    @patch("os.setuid")
    def test_run_occ_success(self, mock_setuid, mock_setgid, mock_getuid, mock_stat):
        # Setup mocks
        mock_module = Mock()
        mock_module.params = {
            "nextcloud_path": "/path/to/nextcloud",
            "php_runtime": "php",
        }
        mock_stat.return_value.st_uid = 1000
        mock_stat.return_value.st_gid = 1000
        mock_getuid.return_value = 1001
        mock_module.run_command.return_value = (0, "Success", "")

        # Call the function
        returnCode, stdOut, stdErr, maintenanceMode = run_occ(mock_module, "status")

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
        mock_module = Mock()
        mock_module.params = {
            "nextcloud_path": "/path/to/nextcloud",
            "php_runtime": "php",
        }
        mock_stat.return_value.st_uid = 1000
        mock_stat.return_value.st_gid = 1000
        mock_getuid.return_value = 1000
        mock_module.run_command.return_value = (
            1,
            "",
            "Nextcloud is in maintenance mode",
        )

        # Call the function
        returnCode, stdOut, stdErr, maintenanceMode = run_occ(mock_module, "status")

        # Assertions
        mock_module.warn.assert_called_once_with("Nextcloud is in maintenance mode")
        self.assertEqual(returnCode, 1)
        self.assertEqual(stdOut, "")
        self.assertIn("maintenance mode", stdErr)
        self.assertTrue(maintenanceMode)

    @patch("os.stat")
    @patch("os.getuid")
    def test_run_occ_not_installed(self, mock_getuid, mock_stat):
        # Setup mocks
        mock_module = Mock()
        mock_module.params = {
            "nextcloud_path": "/path/to/nextcloud",
            "php_runtime": "php",
        }
        mock_stat.return_value.st_uid = 1000
        mock_stat.return_value.st_gid = 1000
        mock_getuid.return_value = 1000
        mock_module.run_command.return_value = (1, "", "Nextcloud is not installed")

        returnCode, stdOut, stdErr, maintenanceMode = run_occ(mock_module, "status")

        # Check if the warning was issued
        mock_module.warn.assert_called_once_with("Nextcloud is not installed")
        mock_module.fail_json.assert_called_once_with(
            msg="Failure when executing occ command. Exited 1.\nstdout: \nstderr: Nextcloud is not installed",
            stdout=stdOut,
            stderr=stdErr,
            command="status",
        )

        # Verify the return values
        self.assertEqual(returnCode, 1)
        self.assertEqual(stdOut, "")
        self.assertIn("not installed", stdErr)
        self.assertFalse(maintenanceMode)

    @patch("os.stat")
    @patch("os.getuid")
    def test_run_occ_error_handling(self, mock_getuid, mock_stat):
        # Setup mocks
        mock_module = Mock()
        mock_module.params = {
            "nextcloud_path": "/path/to/nextcloud",
            "php_runtime": "php",
        }
        mock_stat.return_value.st_uid = 1000
        mock_stat.return_value.st_gid = 1000
        mock_getuid.return_value = 1000
        mock_module.run_command.return_value = (
            1,
            "",
            "Some package is not installed\nAdditional info",
        )

        returnCode, stdOut, stdErr, maintenanceMode = run_occ(mock_module, "status")

        # Check if the error was issued
        mock_module.fail_json.assert_called_once_with(
            msg="Failure when executing occ command. Exited 1.\nstdout: \nstderr: Some package is not installed\nAdditional info",
            stdout=stdOut,
            stderr=stdErr,
            command="status",
        )

        # Verify the return values
        self.assertEqual(returnCode, 1)
        self.assertEqual(stdOut, "")
        self.assertIn("Some package", stdErr)
        self.assertFalse(maintenanceMode)


if __name__ == "__main__":
    unittest.main()
