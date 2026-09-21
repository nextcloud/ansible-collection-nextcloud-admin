from unittest import TestCase
from unittest.mock import patch, MagicMock
from ansible_collections.nextcloud.admin.plugins.modules import app as app_module
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    AppExceptions,
)
from ansible.module_utils import basic


class TestAppModuleBase(TestCase):

    def setUp(self):
        self.appID = "iamapp"
        self.mock_module = MagicMock(spec=basic.AnsibleModule)
        self.module_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.AnsibleModule"
        )
        self.mock_module_class = self.module_patcher.start()
        self.mock_module_class.return_value = self.mock_module
        self.mock_module.params = {"name": self.appID}

        self.server_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.NCServer"
        )
        self.mock_server_class = self.server_patcher.start()
        self.mock_server = self.mock_server_class.return_value
        self.mock_app = self.mock_server.app.return_value
        self.mock_app.version = "1.0.0"

    def tearDown(self):
        # Stop the patchers after each test
        self.module_patcher.stop()
        self.server_patcher.stop()

    def state_present_installs_app(self):
        self.mock_module.params.update({"state": "present"})
        self.mock_app.state = "absent"
        self.mock_app.install.return_value = (["installed", "enabled"], [])
        app_module.main()

    def state_present_enable_app(self):
        self.mock_module.params.update({"state": "present"})
        self.mock_app.state = "disabled"
        self.mock_app.toggle.return_value = (["enabled"], [])
        app_module.main()

    def state_present_app_already_present(self):
        self.mock_module.params.update({"state": "present"})
        self.mock_app.state = "present"
        app_module.main()

        self.mock_app.install.assert_not_called()
        self.mock_app.toggle.assert_not_called()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=[],
            version=self.mock_app.version,
            changed=False,
        )

    def state_disabled_installs_app_without_enabling(self):
        self.mock_module.params.update({"state": "disabled"})
        self.mock_app.state = "absent"
        self.mock_app.install.return_value = (["installed"], [])
        app_module.main()

    def state_disabled_disable_app(self):
        self.mock_module.params.update({"state": "disabled"})
        self.mock_app.state = "present"
        self.mock_app.toggle.return_value = (["disabled"], [])
        app_module.main()

    def state_absent_removes_app(self):
        self.mock_module.params.update({"state": "absent"})
        self.mock_app.state = "present"
        self.mock_app.remove.return_value = (["disabled", "removed"], [])
        app_module.main()

    def state_absent_app_already_absent(self):
        self.mock_module.params.update({"state": "absent"})
        self.mock_app.state = "absent"
        app_module.main()

        self.mock_app.install.assert_not_called()
        self.mock_app.toggle.assert_not_called()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=[],
            version=self.mock_app.version,
            changed=False,
        )

    def state_updated_performs_update(self):
        new_version = "3.0.0"
        self.mock_module.params.update({"state": "updated"})
        self.mock_app.state = "present"
        self.mock_app.update_version_available = new_version
        self.mock_app.update.return_value = (self.mock_app.version, new_version)
        app_module.main()

    def state_updated_no_update_available(self):
        self.mock_module.params.update({"state": "updated"})
        self.mock_app.state = "present"
        self.mock_app.update_available = False
        app_module.main()

        self.mock_app.update.assert_not_called()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=[],
            version=self.mock_app.version,
            changed=False,
        )

    def toggle_app_exception_calls_fail_json(self):
        self.mock_module.params.update({"state": "disabled"})
        self.mock_app.state = "present"
        self.mock_app.toggle.side_effect = AppExceptions(
            msg="Failed toggle", app_name=self.appID
        )
        app_module.main()

    def install_app_exception_calls_fail_json(self):
        self.mock_module.params.update({"state": "present"})
        self.mock_app.state = "absent"
        self.mock_app.version = None
        self.mock_app.install.side_effect = AppExceptions(
            msg="Failed install", app_name=self.appID
        )
        app_module.main()

    def remove_app_exception_calls_fail_json(self):
        self.mock_module.params.update({"state": "absent"})
        self.mock_app.state = "present"
        self.mock_app.remove.side_effect = AppExceptions(
            msg="Failed remove", app_name=self.appID
        )
        app_module.main()

    def update_app_exception_calls_fail_json(self):
        self.mock_module.params.update({"state": "updated"})
        self.mock_app.state = "present"
        self.mock_app.update_available = True
        self.mock_app.update.side_effect = AppExceptions(
            msg="Failed update", app_name=self.appID
        )
        app_module.main()


class TestAppModuleNormal(TestAppModuleBase):

    def setUp(self):
        super().setUp()
        self.mock_module.check_mode = False

    def test_state_present_installs_app(self):
        self.state_present_installs_app()

        self.mock_app.install.assert_called_once()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=["installed", "enabled"],
            version=self.mock_app.version,
            changed=True,
        )

    def test_state_disabled_installs_app_without_enabling(self):
        self.state_disabled_installs_app_without_enabling()

        self.mock_app.install.assert_called_once()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=["installed"],
            version=self.mock_app.version,
            changed=True,
        )

    def test_state_present_enable_app(self):
        self.state_present_enable_app()

        self.mock_app.toggle.assert_called_once()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=["enabled"],
            version=self.mock_app.version,
            changed=True,
        )

    def test_state_disabled_disable_app(self):
        self.state_disabled_disable_app()

        self.mock_app.toggle.assert_called_once()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=["disabled"],
            version=self.mock_app.version,
            changed=True,
        )

    def test_state_absent_removes_app(self):
        self.state_absent_removes_app()

        self.mock_app.remove.assert_called_once()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=["disabled", "removed"],
            version=self.mock_app.version,
            changed=True,
        )

    def test_state_updated_performs_update(self):
        self.state_updated_performs_update()

        self.mock_app.update.assert_called_once()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=["updated"],
            version="3.0.0",
            changed=True,
        )

    def test_state_present_app_already_present(self):
        self.state_present_app_already_present()

    def test_state_absent_app_already_absent(self):
        self.state_absent_app_already_absent()

    def test_state_updated_no_update_available(self):
        self.state_updated_no_update_available()

    def test_toggle_app_exception_calls_fail_json(self):
        self.toggle_app_exception_calls_fail_json()

        self.mock_module.fail_json.assert_called_once()
        args, kwargs = self.mock_module.fail_json.call_args
        assert "Failed toggle" in kwargs["msg"]

    def test_install_app_exception_calls_fail_json(self):
        self.install_app_exception_calls_fail_json()

        self.mock_module.fail_json.assert_called_once()
        args, kwargs = self.mock_module.fail_json.call_args
        assert "Failed install" in kwargs["msg"]

    def test_remove_app_exception_calls_fail_json(self):
        self.remove_app_exception_calls_fail_json()

        self.mock_module.fail_json.assert_called_once()
        args, kwargs = self.mock_module.fail_json.call_args
        assert "Failed remove" in kwargs["msg"]

    def test_update_app_exception_calls_fail_json(self):
        self.update_app_exception_calls_fail_json()

        self.mock_module.fail_json.assert_called_once()
        args, kwargs = self.mock_module.fail_json.call_args
        assert "Failed update" in kwargs["msg"]


class TestAppModuleCheckMode(TestAppModuleBase):

    def setUp(self):
        super().setUp()
        self.mock_module.check_mode = True

    def test_state_present_installs_app(self):
        self.state_present_installs_app()

        self.mock_app.install.assert_not_called()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=["installed", "enabled"],
            version="undefined in check mode",
            changed=True,
        )

    def test_state_disabled_installs_app_without_enabling(self):
        self.state_disabled_installs_app_without_enabling()

        self.mock_app.install.assert_not_called()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=["installed"],
            version="undefined in check mode",
            changed=True,
        )

    def test_state_present_enable_app(self):
        self.state_present_enable_app()

        self.mock_app.toggle.assert_not_called()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=[
                "present"
            ],  # should be 'enabled' todo : fix the case in check mode
            version=self.mock_app.version,
            changed=True,
        )

    def test_state_disabled_disable_app(self):
        self.state_disabled_disable_app()

        self.mock_app.toggle.assert_not_called()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=["disabled"],
            version=self.mock_app.version,
            changed=True,
        )

    def test_state_absent_removes_app(self):
        self.state_absent_removes_app()

        self.mock_app.remove.assert_not_called()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=["disabled", "removed"],
            version=self.mock_app.version,
            changed=True,
        )

    def test_state_updated_performs_update(self):
        self.state_updated_performs_update()

        self.mock_app.update.assert_not_called()
        self.mock_module.exit_json.assert_called_once_with(
            actions_taken=["updated"],
            version="3.0.0",
            changed=True,
        )

    def test_state_present_app_already_present(self):
        self.state_present_app_already_present()

    def test_state_absent_app_already_absent(self):
        self.state_absent_app_already_absent()

    def test_state_updated_no_update_available(self):
        self.state_updated_no_update_available()
