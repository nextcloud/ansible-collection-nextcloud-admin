from unittest import TestCase
from unittest.mock import patch, MagicMock
from ansible_collections.nextcloud.admin.plugins.modules import server_install
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    OccExceptions,
    PhpScriptException,
)
from ansible.module_utils import basic


class TestServerInstall(TestCase):

    def setUp(self):
        self.mock_module = MagicMock(spec=basic.AnsibleModule)
        self.expected_result = {"changed": False}
        self.module_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.server_install.AnsibleModule"
        )
        self.mock_module_class = self.module_patcher.start()
        self.mock_module.check_mode = False
        self.mock_module._diff = False
        self.mock_module_class.return_value = self.mock_module
        self.mock_module.params = {
            "options": {"database_type": "sqlite", "disable_admin_user": True},
            "redact_occ_command": True,
        }
        self.server_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.server_install.NCServer"
        )
        self.mock_server_class = self.server_patcher.start()
        self.mock_server = self.mock_server_class.return_value
        self.mock_server.installed = False

    def tearDown(self):
        self.module_patcher.stop()
        self.server_patcher.stop()

    def test_server_already_installed(self):
        self.mock_server.installed = True
        server_install.main()
        self.mock_server.install.assert_not_called()
        self.mock_module.exit_json.assert_called_once_with(**self.expected_result)

    def test_server_install(self):
        expected_result = dict(**self.expected_result)
        expected_result["changed"] = True
        server_install.main()
        self.mock_server.install.assert_called_once_with(
            database_type="sqlite", disable_admin_user=True
        )
        self.mock_module.exit_json.assert_called_once_with(**expected_result)

    def test_server_install_default_options(self):
        self.mock_module.params = {"options": {}, "redact_occ_command": True}
        server_install.main()
        self.mock_server.install.assert_called_once_with()

    def test_server_install_check_mode(self):
        self.mock_module.check_mode = True
        expected_result = dict(**self.expected_result)
        expected_result["changed"] = True
        server_install.main()
        self.mock_server.install.assert_not_called()
        self.mock_module.exit_json.assert_called_once_with(**expected_result)

    def test_server_install_diff(self):
        self.mock_module._diff = True
        expected_result = {
            "changed": True,
            "diff": {"before": "Not installed.\n", "after": "Installed. "},
        }
        server_install.main()
        self.mock_module.exit_json.assert_called_once_with(**expected_result)

    def test_server_init_exception(self):
        self.mock_server_class.side_effect = OccExceptions(msg="status failed")
        server_install.main()
        self.mock_server.install.assert_not_called()
        self.mock_module.fail_json.assert_called_once()
        self.mock_module.exit_json.assert_not_called()

    def test_server_install_exception_redacted(self):
        self.mock_server.install.side_effect = OccExceptions(
            occ_cmd=["maintenance:install", "--database-pass", "secret"],
            stderr="install failed",
        )
        server_install.main()
        self.mock_module.fail_json.assert_called_once()
        kwargs = self.mock_module.fail_json.call_args.kwargs
        self.assertEqual(kwargs["occ_cmd"], ["<redacted>"])
        self.assertNotIn("secret", str(kwargs))
        self.mock_module.exit_json.assert_not_called()

    def test_server_install_exception_not_redacted(self):
        self.mock_module.params["redact_occ_command"] = False
        occ_cmd = ["maintenance:install", "--database-pass", "secret"]
        self.mock_server.install.side_effect = OccExceptions(
            occ_cmd=occ_cmd, stderr="install failed"
        )
        server_install.main()
        kwargs = self.mock_module.fail_json.call_args.kwargs
        self.assertEqual(kwargs["occ_cmd"], occ_cmd)

    def test_server_install_exception_without_occ_cmd(self):
        self.mock_server.install.side_effect = PhpScriptException(
            msg="php failed", stderr="boom", stdout="", rc=1, php_script="<?php"
        )
        server_install.main()
        self.mock_module.fail_json.assert_called_once()
        self.assertNotIn("occ_cmd", self.mock_module.fail_json.call_args.kwargs)
        self.mock_module.exit_json.assert_not_called()
