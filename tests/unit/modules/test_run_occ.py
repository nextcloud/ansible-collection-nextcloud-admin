from ansible.module_utils import basic
from ansible_collections.nextcloud.admin.plugins.modules import run_occ
import unittest
from unittest.mock import patch, MagicMock


class TestRunOccModule(unittest.TestCase):

    @patch("ansible_collections.nextcloud.admin.plugins.modules.run_occ.run_occ")
    def test_successful_command_execution(self, mock_run_occ):
        # Mock the return value of run_occ
        mock_run_occ.return_value = (0, "Success", "")

        # Create a mock AnsibleModule object
        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"command": "status --output=json"}

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.run_occ.AnsibleModule",
            return_value=mock_module,
        ):
            run_occ.main()

        # Check that exit_json was called with expected values
        mock_module.exit_json.assert_called_once_with(
            changed=True,
            command="status --output=json",
            rc=0,
            stdout="Success",
            stderr="",
        )

    @patch("ansible_collections.nextcloud.admin.plugins.modules.run_occ.run_occ")
    def test_command_execution_failure(self, mock_run_occ):
        # Mock the return value of run_occ to simulate an error
        mock_run_occ.side_effect = run_occ.OccExceptions(
            "Error occurred", rc=1, stdout="", stderr="Error"
        )

        # Create a mock AnsibleModule object
        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"command": "invalid-command"}

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.run_occ.AnsibleModule",
            return_value=mock_module,
        ):
            run_occ.main()

        # Check that fail_json was called with expected values
        mock_module.fail_json.assert_called_once_with(
            msg="Error occurred",
            exception_class="OccExceptions",
            command="invalid-command",
            rc=1,
            stdout="",
            stderr="Error",
        )


if __name__ == "__main__":
    unittest.main()
