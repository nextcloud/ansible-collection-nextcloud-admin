from unittest import TestCase
from unittest.mock import patch, MagicMock
from ansible_collections.nextcloud.admin.plugins.modules import app as app_module
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    AppExceptions,
)
from ansible.module_utils import basic


class TestAppModule(TestCase):
    @patch("ansible_collections.nextcloud.admin.plugins.modules.app.app")
    def test_state_present_installs_app(self, mock_app_class):
        mock_nc_app = MagicMock()
        mock_nc_app.state = "absent"
        mock_nc_app.install.return_value = ("1.0.0", ["installed", "enabled"])
        mock_nc_app.version = "1.0.0"
        mock_app_class.return_value = mock_nc_app

        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"name": "files", "state": "present"}
        mock_module.check_mode = False

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.AnsibleModule",
            return_value=mock_module,
        ):
            app_module.main()

        mock_module.exit_json.assert_called_once_with(
            actions_taken=["installed", "enabled"],
            version="1.0.0",
            changed=True,
        )

    @patch("ansible_collections.nextcloud.admin.plugins.modules.app.app")
    def test_state_disabled_toggles_app(self, mock_app_class):
        mock_nc_app = MagicMock()
        mock_nc_app.state = "enabled"
        mock_nc_app.toggle.return_value = "disabled"
        mock_nc_app.version = "1.0.1"
        mock_app_class.return_value = mock_nc_app

        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"name": "files", "state": "disabled"}
        mock_module.check_mode = False

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.AnsibleModule",
            return_value=mock_module,
        ):
            app_module.main()

        mock_module.exit_json.assert_called_once_with(
            actions_taken=["disabled"],
            version="1.0.1",
            changed=True,
        )

    @patch("ansible_collections.nextcloud.admin.plugins.modules.app.app")
    def test_state_absent_removes_app(self, mock_app_class):
        mock_nc_app = MagicMock()
        mock_nc_app.state = "present"
        mock_nc_app.remove.return_value = (["disabled", "removed"], "2.0.0")
        mock_nc_app.version = "2.0.0"
        mock_app_class.return_value = mock_nc_app

        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"name": "files", "state": "absent"}
        mock_module.check_mode = False

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.AnsibleModule",
            return_value=mock_module,
        ):
            app_module.main()

        mock_module.exit_json.assert_called_once_with(
            actions_taken=["disabled", "removed"],
            version="2.0.0",
            changed=True,
        )

    @patch("ansible_collections.nextcloud.admin.plugins.modules.app.app")
    def test_state_updated_performs_update(self, mock_app_class):
        mock_nc_app = MagicMock()
        mock_nc_app.state = "enabled"
        mock_nc_app.update_available = True
        mock_nc_app.update.return_value = "3.0.0"
        mock_nc_app.version = "2.9.0"
        mock_app_class.return_value = mock_nc_app

        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"name": "calendar", "state": "updated"}
        mock_module.check_mode = False

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.AnsibleModule",
            return_value=mock_module,
        ):
            app_module.main()

        mock_module.exit_json.assert_called_once_with(
            actions_taken=["updated"],
            version="3.0.0",
            changed=True,
        )

    @patch("ansible_collections.nextcloud.admin.plugins.modules.app.app")
    def test_toggle_app_exception_calls_fail_json(self, mock_app_class):
        mock_nc_app = MagicMock()
        mock_nc_app.state = "enabled"
        mock_nc_app.toggle.side_effect = AppExceptions(
            msg="Failed toggle", app_name="files"
        )
        mock_nc_app.version = "1.0.0"
        mock_app_class.return_value = mock_nc_app

        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"name": "files", "state": "disabled"}
        mock_module.check_mode = False

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.AnsibleModule",
            return_value=mock_module,
        ):
            app_module.main()

        mock_module.fail_json.assert_called_once()
        args, kwargs = mock_module.fail_json.call_args
        assert "Failed toggle" in kwargs["msg"]

    @patch("ansible_collections.nextcloud.admin.plugins.modules.app.app")
    def test_install_app_exception_calls_fail_json(self, mock_app_class):
        mock_nc_app = MagicMock()
        mock_nc_app.state = "absent"
        mock_nc_app.install.side_effect = AppExceptions(
            msg="Failed install", app_name="contacts"
        )
        mock_nc_app.version = None
        mock_app_class.return_value = mock_nc_app

        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"name": "contacts", "state": "present"}
        mock_module.check_mode = False

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.AnsibleModule",
            return_value=mock_module,
        ):
            app_module.main()

        mock_module.fail_json.assert_called_once()
        args, kwargs = mock_module.fail_json.call_args
        assert "Failed install" in kwargs["msg"]

    @patch("ansible_collections.nextcloud.admin.plugins.modules.app.app")
    def test_remove_app_exception_calls_fail_json(self, mock_app_class):
        mock_nc_app = MagicMock()
        mock_nc_app.state = "present"
        mock_nc_app.remove.side_effect = AppExceptions(
            msg="Failed remove", app_name="mail"
        )
        mock_nc_app.version = "4.0.0"
        mock_app_class.return_value = mock_nc_app

        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"name": "mail", "state": "absent"}
        mock_module.check_mode = False

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.AnsibleModule",
            return_value=mock_module,
        ):
            app_module.main()

        mock_module.fail_json.assert_called_once()
        args, kwargs = mock_module.fail_json.call_args
        assert "Failed remove" in kwargs["msg"]

    @patch("ansible_collections.nextcloud.admin.plugins.modules.app.app")
    def test_update_app_exception_calls_fail_json(self, mock_app_class):
        mock_nc_app = MagicMock()
        mock_nc_app.state = "enabled"
        mock_nc_app.update_available = True
        mock_nc_app.update.side_effect = AppExceptions(
            msg="Failed update", app_name="deck"
        )
        mock_nc_app.version = "2.0.0"
        mock_app_class.return_value = mock_nc_app

        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"name": "deck", "state": "updated"}
        mock_module.check_mode = False

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.AnsibleModule",
            return_value=mock_module,
        ):
            app_module.main()

        mock_module.fail_json.assert_called_once()
        args, kwargs = mock_module.fail_json.call_args
        assert "Failed update" in kwargs["msg"]

    @patch("ansible_collections.nextcloud.admin.plugins.modules.app.app")
    def test_state_present_check_mode_keep_disabled(self, mock_app_class):
        mock_nc_app = MagicMock()
        mock_nc_app.state = "absent"
        mock_nc_app.version = None
        mock_app_class.return_value = mock_nc_app

        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"name": "contacts", "state": "disabled"}
        mock_module.check_mode = True

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.AnsibleModule",
            return_value=mock_module,
        ):
            app_module.main()

        mock_nc_app.install.assert_not_called()
        mock_module.exit_json.assert_called_once_with(
            actions_taken=["installed"],
            version="undefined in check mode",
            changed=True,
        )

    @patch("ansible_collections.nextcloud.admin.plugins.modules.app.app")
    def test_state_present_check_mode_enable_app(self, mock_app_class):
        mock_nc_app = MagicMock()
        mock_nc_app.state = "absent"
        mock_nc_app.version = None
        mock_app_class.return_value = mock_nc_app

        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"name": "contacts", "state": "present"}
        mock_module.check_mode = True

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.AnsibleModule",
            return_value=mock_module,
        ):
            app_module.main()

        mock_nc_app.install.assert_not_called()
        mock_module.exit_json.assert_called_once_with(
            actions_taken=["installed", "enabled"],
            version="undefined in check mode",
            changed=True,
        )

    @patch("ansible_collections.nextcloud.admin.plugins.modules.app.app")
    def test_state_disabled_check_mode_no_toggle(self, mock_app_class):
        mock_nc_app = MagicMock()
        mock_nc_app.state = "enabled"
        mock_nc_app.version = "1.0.0"
        mock_app_class.return_value = mock_nc_app

        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"name": "contacts", "state": "disabled"}
        mock_module.check_mode = True

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.AnsibleModule",
            return_value=mock_module,
        ):
            app_module.main()

        mock_nc_app.toggle.assert_not_called()
        mock_module.exit_json.assert_called_once_with(
            actions_taken=["disabled"],
            version="1.0.0",
            changed=True,
        )

    @patch("ansible_collections.nextcloud.admin.plugins.modules.app.app")
    def test_state_absent_check_mode_no_remove(self, mock_app_class):
        mock_nc_app = MagicMock()
        mock_nc_app.state = "present"
        mock_nc_app.version = "2.5.0"
        mock_app_class.return_value = mock_nc_app

        mock_module = MagicMock(spec=basic.AnsibleModule)
        mock_module.params = {"name": "mail", "state": "absent"}
        mock_module.check_mode = True

        with patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app.AnsibleModule",
            return_value=mock_module,
        ):
            app_module.main()

        mock_nc_app.remove.assert_not_called()
        mock_module.exit_json.assert_called_once_with(
            actions_taken=["disabled", "removed"],
            version="2.5.0",
            changed=True,
        )
