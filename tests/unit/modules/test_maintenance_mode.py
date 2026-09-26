from math import exp
from unittest import TestCase, result
from unittest.mock import patch, MagicMock, ANY
from ansible_collections.nextcloud.admin.plugins.modules import maintenance_mode
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    AppExceptions,
)
from ansible.module_utils import basic


class TestMaintenanceMode(TestCase):

    def setUp(self, show_settings=False):
        self.mock_module = MagicMock(spec=basic.AnsibleModule)
        self.expected_result = {"changed": False, "diff": {}}
        self.module_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.maintenance_mode.AnsibleModule"
        )
        self.mock_module_class = self.module_patcher.start()
        self.mock_module.check_mode = False
        self.mock_module._diff = False
        self.mock_module_class.return_value = self.mock_module
        self.mock_module.params = {"state": True}
        self.server_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.maintenance_mode.NCServer"
        )
        self.mock_server_class = self.server_patcher.start()
        self.mock_server = self.mock_server_class.return_value
        self.mock_server.maintenance = False
        self.mock_server.installed = True

    def tearDown(self):
        # Stop the patchers after each test
        self.module_patcher.stop()
        self.server_patcher.stop()

    def test_server_not_installed(self):
        self.mock_server.installed = False

        maintenance_mode.main()

        self.mock_module.fail_json.assert_called_once()

    def test_maintenance_mode_already_enabled(self):
        self.mock_server.maintenance = True
        maintenance_mode.main()
        self.mock_module.exit_json.assert_called_once_with(**self.expected_result)

    def test_maintenance_mode_already_disabled(self):
        self.mock_module.params = {"state": False}
        maintenance_mode.main()
        self.mock_module.exit_json.assert_called_once_with(**self.expected_result)

    def test_enable_maintenance_mode(self):
        expected_result = dict(**self.expected_result)
        expected_result["changed"] = True
        maintenance_mode.main()
        self.mock_module.exit_json.assert_called_once_with(**expected_result)

    def test_enable_maintenance_mode_check_mode(self):
        self.mock_module.check_mode = True
        self.test_enable_maintenance_mode()
        self.mock_server.set_maintenance.assert_not_called()

    def test_disable_maintenance_mode(self):
        expected_result = dict(**self.expected_result)
        expected_result["changed"] = True
        self.mock_module.params = {"state": False}
        self.mock_server.maintenance = True
        maintenance_mode.main()
        self.mock_module.exit_json.assert_called_once_with(**expected_result)

    def test_disable_maintenance_mode_check_mode(self):
        self.mock_module.check_mode = True
        self.test_disable_maintenance_mode()
        self.mock_server.set_maintenance.assert_not_called()

    def test_enable_maintenance_mode_diff(self):
        self.mock_module._diff = True
        expected_diff = {
            "before": {"maintenance_mode": False},
            "after": {"maintenance_mode": True},
        }
        expected_result = {
            "changed": True,
            "diff": expected_diff,
        }
        maintenance_mode.main()
        self.mock_module.exit_json.assert_called_once_with(**expected_result)

    def test_disable_maintenance_mode_diff(self):
        self.mock_module.params = {"state": False}
        self.mock_server.maintenance = True
        self.mock_module._diff = True
        expected_diff = {
            "before": {"maintenance_mode": True},
            "after": {"maintenance_mode": False},
        }
        expected_result = {
            "changed": True,
            "diff": expected_diff,
        }
        maintenance_mode.main()
        self.mock_module.exit_json.assert_called_once_with(**expected_result)
