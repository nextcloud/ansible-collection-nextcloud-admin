from unittest import TestCase
from unittest.mock import patch, MagicMock
from ansible_collections.nextcloud.admin.plugins.module_utils import app
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    OccExceptions,
    AppExceptions,
)
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

    def test_get_facts_absent_app(self):
        app_instance = self._init_app(present=False)
        facts = app_instance.get_facts()
        self.assertEqual(facts, {"state": "absent", "is_shipped": False})

    def test_get_facts_present_app(self):
        self.mock_run_occ.side_effect = [
            (0, f"{self.app_name} new version available: 1.1.0"),
            (0, "/var/www/nextcloud/apps/test_app"),
        ]
        expected_facts = dict(
            state="present",
            version=self.app_version,
            is_shipped=False,
            update_available=True,
            version_available="1.1.0",
            app_path="/var/www/nextcloud/apps/test_app",
        )
        facts = self.app_instance.get_facts()
        self.assertEqual(facts, expected_facts)

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

    def test_install_enabled_with_success(self):
        self.mock_run_occ.side_effect = [
            (
                0,
                f"{self.app_name} 1.0.0 installed\n{self.app_name} enabled\nmisc message",
            )
        ]
        actions_taken, misc_msg = self.app_instance.install()
        self.mock_run_occ.assert_called_with(
            self.mock_ansible_module, ["app:install", self.app_name]
        )
        self.assertEqual(self.app_instance.version, "1.0.0")
        self.assertEqual(self.app_instance.state, "present")
        self.assertEqual(actions_taken, ["installed", "enabled"])
        self.assertEqual(misc_msg, ["misc message"])

    def test_install_disabled_with_success(self):
        self.mock_run_occ.side_effect = [
            (0, f"{self.app_name} 1.0.0 installed\nmisc message")
        ]
        actions_taken, misc_msg = self.app_instance.install(enable=False)
        self.mock_run_occ.assert_called_with(
            self.mock_ansible_module, ["app:install", "--keep-disabled", self.app_name]
        )
        self.assertEqual(self.app_instance.version, "1.0.0")
        self.assertEqual(self.app_instance.state, "disabled")
        self.assertEqual(actions_taken, ["installed"])
        self.assertEqual(misc_msg, ["misc message"])

    def test_install_with_failure(self):
        execute_occ_command = [
            f"{self.mock_ansible_module.params['nextcloud_path']}",
            f"{self.mock_ansible_module.params['nextcloud_path']}/occ",
            "app:install",
            self.app_name,
        ]
        execute_occ_result = dict(
            rc=1, stdout=f"{self.app_name} already installed", stderr=""
        )
        self.mock_run_occ.side_effect = [
            OccExceptions(execute_occ_command, **execute_occ_result)
        ]
        with self.assertRaises(AppExceptions):
            actions_taken, misc_msg = self.app_instance.install()

    def test_remove_with_success(self):
        self.mock_run_occ.side_effect = [
            (
                0,
                f"misc message\n{self.app_name} disabled\n{self.app_name} 1.0.0 removed\n",
            )
        ]
        actions_taken, misc_msg = self.app_instance.remove()
        self.mock_run_occ.assert_called_with(
            self.mock_ansible_module, command=["app:remove", self.app_name]
        )
        self.assertEqual(self.app_instance.version, None)
        self.assertEqual(self.app_instance.state, "absent")
        self.assertEqual(actions_taken, ["disabled", "removed"])
        self.assertEqual(misc_msg, ["misc message"])

    def test_remove_with_failure(self):
        execute_occ_command = [
            f"{self.mock_ansible_module.params['nextcloud_path']}",
            f"{self.mock_ansible_module.params['nextcloud_path']}/occ",
            "app:remove",
            self.app_name,
        ]
        execute_occ_result = dict(
            rc=1, stdout=f"{self.app_name} is not enabled", stderr=""
        )
        self.mock_run_occ.side_effect = [
            OccExceptions(execute_occ_command, **execute_occ_result)
        ]
        with self.assertRaises(AppExceptions):
            actions_taken, misc_msg = self.app_instance.install()

    def test_toggle_from_enabled(self):
        self.app_instance.state = "present"
        self.mock_run_occ.side_effect = [
            (0, f"misc message\n{self.app_name} 1.0.0 disabled\n")
        ]
        actions_taken, misc_msg = self.app_instance.toggle()
        self.mock_run_occ.assert_called_with(
            self.mock_ansible_module, [f"app:disable", self.app_name]
        )
        self.assertEqual(self.app_instance.state, "disabled")
        self.assertEqual(actions_taken, ["disabled"])
        self.assertEqual(misc_msg, ["misc message"])

    def test_toggle_from_disabled(self):
        self.app_instance.state = "disabled"
        self.mock_run_occ.side_effect = [
            (0, f"{self.app_name} 1.0.0 enabled\nmisc message\n")
        ]
        actions_taken, misc_msg = self.app_instance.toggle()
        self.mock_run_occ.assert_called_with(
            self.mock_ansible_module, [f"app:enable", self.app_name]
        )
        self.assertEqual(self.app_instance.state, "present")
        self.assertEqual(actions_taken, ["enabled"])
        self.assertEqual(misc_msg, ["misc message"])

    def test_toggle_raise_exception(self):
        self.app_instance.state = "disabled"
        self.mock_run_occ.side_effect = [OccExceptions]
        with self.assertRaises(AppExceptions):
            actions_taken, misc_msg = self.app_instance.toggle()

    def test_toggle_from_absent(self):
        self.app_instance.state = "absent"
        with self.assertRaises(AssertionError):
            actions_taken, misc_msg = self.app_instance.toggle()

    def test_update(self):
        self.app_instance.version = "1.0.0"
        self.app_instance._update_version_available = "1.1.0"
        self.mock_run_occ.side_effect = [(0, "")]
        old_version, new_version = self.app_instance.update()
        self.mock_run_occ.assert_called_with(
            self.mock_ansible_module, [f"app:update", self.app_name]
        )
        self.assertEqual(old_version, "1.0.0")
        self.assertEqual(new_version, "1.1.0")

    def test_update_raise_exception(self):
        self.app_instance.version = "1.0.0"
        self.mock_run_occ.side_effect = [OccExceptions]
        with self.assertRaises(AppExceptions):
            old_version, new_version = self.app_instance.update()


if __name__ == "__main__":
    unittest.main()
