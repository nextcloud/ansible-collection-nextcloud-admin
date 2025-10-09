from unittest import TestCase
from unittest.mock import patch, MagicMock, ANY
from ansible_collections.nextcloud.admin.plugins.module_utils import app, exceptions
from ansible.module_utils import basic
import unittest.main
import json


class TestApp(TestCase):

    def setUp(self):
        self.app_name = "test_app"
        self.app_version = "1.0.0"
        self.mock_run_occ = MagicMock()
        self.run_occ_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.module_utils.app.run_occ",
            self.mock_run_occ,
        )
        self.run_occ_patcher.start()

        self.mock_ansible_module = MagicMock()
        self.module_patcher = patch(
            "ansible.module_utils.basic.AnsibleModule", self.mock_ansible_module
        )
        self.module_patcher.start()
        self.mock_ansible_module.params = {
            "nextcloud_path": "/path/to/nextcloud",
            "php_runtime": "/usr/bin/php",
            "id": self.app_name,
        }
        self.app_instance = self._init_app()

    def tearDown(self):
        self.run_occ_patcher.stop()
        self.module_patcher.stop()

    def _init_app(
        self, shipped: bool = False, enabled: bool = True, present: bool = True
    ):
        """
        Generate a mocked app object to make unit tests on, based on the provided parameters.

        It simulate some context within a Nextcloud server instance used by the app constructor
        by planning the mock behavior of run_occ module_util during _init_ phase.
        It prepares two lists of apps (enabled and disabled): one for shipped apps
        and another for external apps.
        The fake test_app is inserted into the proper list before combining thoses to form
        a complete representation of the app environment.

        Args:
            shipped (bool): Indicates whether the app is shipped with Nextcloud.
                            Defaults to False.
            enabled (bool): Indicates whether the app should be enabled. Defaults to True.
            present (bool): Indicates whether the app is present in the system.
                            Defaults to True.

        Returns:
            The mocked app object to test on.
        """
        # init values
        shipped_app_list = {
            "enabled": {"enabled_shipped_app": "0.5.5"},
            "disabled": {"disabled_shipped_app": "0.5.0"},
        }
        ext_app_list = {
            "enabled": {"enabled_external_app": "0.6.6"},
            "disabled": {"disabled_external_app": "0.6.0"},
        }

        status = "enabled" if enabled else "disabled"
        if present or shipped:
            if shipped:
                shipped_app_list[status][self.app_name] = self.app_version
            else:
                ext_app_list[status][self.app_name] = self.app_version
        app_list = {
            "enabled": {**shipped_app_list["enabled"], **ext_app_list["enabled"]},
            "disabled": {**shipped_app_list["disabled"], **ext_app_list["disabled"]},
        }
        self.mock_run_occ.side_effect = [
            (0, json.dumps(shipped_app_list)),
            (0, json.dumps(app_list)),
        ]
        return app.app(self.mock_ansible_module, self.app_name)

    def test_init_app_shipped_and_enabled(self):
        app_instance = self._init_app(shipped=True, enabled=True)
        self.assertEqual(app_instance.state, "present")
        self.assertEqual(app_instance.version, "1.0.0")
        self.assertTrue(app_instance.shipped)

    def test_init_app_shipped_and_disabled_(self):
        app_instance = self._init_app(shipped=True, enabled=False)
        self.assertEqual(app_instance.state, "disabled")
        self.assertEqual(app_instance.version, "1.0.0")
        self.assertTrue(app_instance.shipped)

    def test_init_app_external_and_absent(self):
        app_instance = self._init_app(present=False)
        self.assertEqual(app_instance.state, "absent")
        self.assertEqual(app_instance.version, None)
        self.assertFalse(app_instance.shipped)

    def test_init_app_external_and_disabled_(self):
        app_instance = self._init_app(enabled=False)
        self.assertEqual(app_instance.state, "disabled")
        self.assertEqual(app_instance.version, "1.0.0")
        self.assertFalse(app_instance.shipped)

    def test_init_app_external_and_enabled(self):
        app_instance = self._init_app()
        self.assertEqual(app_instance.state, "present")
        self.assertEqual(app_instance.version, "1.0.0")
        self.assertFalse(app_instance.shipped)

    def test_update_version_available(self):
        # Simulate output from the run_occ function for app:update --showonly
        self.mock_run_occ.side_effect = [
            (0, f"{self.app_name} new version available: 1.1.0")
        ]
        update_version = self.app_instance.update_version_available
        self.assertEqual(update_version, "1.1.0")
        self.assertTrue(self.app_instance.update_available)

    def test_no_update_available(self):
        # Simulate output from the run_occ function for app:update --showonly
        self.mock_run_occ.side_effect = [
            (0, f"{self.app_name} is up-to-date or no updates could be found")
        ]
        update_version = self.app_instance.update_version_available
        self.assertEqual(update_version, None)
        self.assertFalse(self.app_instance.update_available)

    def test_path(self):
        # Simulate output from the run_occ function for app:getpath
        self.mock_run_occ.side_effect = [(0, "/var/www/nextcloud/apps/test_app")]
        app_path = self.app_instance.path
        self.assertEqual(app_path, "/var/www/nextcloud/apps/test_app")

    def test_current_settings(self):
        # Simulate JSON output from the run_occ function for config:list
        app_fake_config = {
            "apps": {
                f"{self.app_name}": {"key": "value"},
            },
        }
        self.mock_run_occ.side_effect = [(0, json.dumps(app_fake_config))]
        settings = self.app_instance.current_settings
        self.assertEqual(settings, {"key": "value"})


if __name__ == "__main__":
    unittest.main()
