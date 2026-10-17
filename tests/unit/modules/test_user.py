from unittest import TestCase
from unittest.mock import patch, MagicMock
from ansible_collections.nextcloud.admin.plugins.modules import user
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    OccExceptions,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.identities import (
    idState,
)


class TestUserModule(TestCase):
    def setUp(self):
        self.user_id = "test_user"
        self.fake_result = dict(
            changed=False,
        )

        self.module_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.user.AnsibleModule"
        )
        self.mock_module_obj = self.module_patcher.start()
        self.mock_module = self.mock_module_obj.return_value
        self.mock_module.check_mode = False
        self.mock_module_obj.return_value = self.mock_module
        self.mock_module.params = {
            "nextcloud_path": "/path/to/nextcloud",
            "php_runtime": "/usr/bin/php",
            "id": self.user_id,
            "state": "present",
            "password": "test_password",
        }

        self.server_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.user.NCServer"
        )
        self.mock_server_obj = self.server_patcher.start()
        self.mock_server = self.mock_server_obj.return_value

        self.mock_user = self.mock_server.user.return_value

        self.mock_group_add = MagicMock()
        self.mock_group_add.state = idState.PRESENT
        self.mock_group_remove = MagicMock()
        self.mock_group_remove.state = idState.PRESENT
        self.mock_server.group.side_effect = [
            self.mock_group_add,
            self.mock_group_remove,
        ]

    def tearDown(self):
        self.module_patcher.stop()
        self.server_patcher.stop()

    def test_user_creation(self):
        self.mock_user.state = idState.ABSENT
        self.fake_result["changed"] = True

        user.main()

        self.mock_user.add.assert_called_once_with(
            False, self.mock_module.params["password"], None, None, None
        )
        self.mock_module.exit_json.assert_called_with(**self.fake_result)

    def test_user_creation_with_display_name(self):
        self.mock_module.params.update({"display_name": "Engineering Team"})
        self.mock_user.state = idState.ABSENT
        self.fake_result["changed"] = True

        user.main()

        self.mock_user.add.assert_called_once_with(
            False,
            self.mock_module.params["password"],
            self.mock_module.params["display_name"],
            None,
            None,
        )
        self.mock_module.exit_json.assert_called_with(**self.fake_result)

    def test_user_deletion(self):
        self.mock_user.state = idState.PRESENT
        self.mock_module.params["state"] = "absent"
        self.fake_result["changed"] = True

        user.main()

        self.mock_user.delete.assert_called_once()
        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_no_operation_on_existing_user(self):
        self.mock_user.state = idState.PRESENT

        user.main()

        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_no_operation_on_absent_user(self):
        self.mock_user.state = idState.ABSENT
        self.mock_module.params["state"] = "absent"

        user.main()

        self.mock_module.exit_json.assert_called_with(**self.fake_result)

    def test_user_membership_exact_match_groups_list(self):
        self.mock_module.params.update({"groups": ["Ateam", "admin"]})
        self.mock_user.groups = ["Ateam", "Bteam"]
        self.mock_user.state = idState.PRESENT
        self.fake_result["changed"] = True

        user.main()

        self.mock_group_add.add_user.assert_called_with(self.user_id)
        self.mock_group_remove.remove_user.assert_called_with(self.user_id)
        self.mock_module.exit_json.assert_called_with(**self.fake_result)

    def test_ignore_missing_groups(self):
        self.mock_module.params.update(
            {"groups": ["Ateam", "admin"], "ignore_missing_groups": True}
        )
        self.mock_user.groups = ["Ateam"]

        self.mock_user.state = idState.PRESENT
        self.mock_group_add.state = idState.ABSENT

        user.main()

        # Since ignore_missing_users is True, we expect no raise a warning and exit normally
        self.mock_module.warn.assert_called_once()
        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_reset_password(self):
        self.mock_module.params.update({"reset_password": True})
        self.fake_result["changed"] = True

        user.main()

        self.mock_user.reset_password.assert_called_with(
            self.mock_module.params["password"]
        )
        self.mock_module.exit_json.assert_called_with(**self.fake_result)

    def test_disable_absent_user(self):
        self.mock_module.params.update({"state": "disabled"})
        self.mock_user.state = idState.ABSENT
        self.fake_result["changed"] = True

        user.main()

        self.mock_user.add.assert_called_once_with(
            False, self.mock_module.params["password"], None, None, None
        )
        self.mock_user.disable.assert_called_once()
        self.mock_module.exit_json.assert_called_with(**self.fake_result)

    def test_enable_disabled_user(self):
        self.mock_user.state = idState.DISABLED
        self.fake_result["changed"] = True

        user.main()

        self.mock_user.enable.assert_called_once()
        self.mock_user.add.assert_not_called()
        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_groups_given_as_string(self):
        self.mock_module.params.update({"groups": "Ateam"})
        self.mock_user.groups = []
        self.mock_user.state = idState.PRESENT
        self.fake_result["changed"] = True

        user.main()

        self.mock_server.group.assert_called_once_with("Ateam")
        self.mock_group_add.add_user.assert_called_once_with(self.user_id)
        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_groups_not_a_list(self):
        self.mock_module.params.update({"groups": 42})
        self.mock_user.groups = []
        self.mock_user.state = idState.PRESENT

        user.main()

        self.mock_module.fail_json.assert_called_once_with(
            msg="The groups argument must be a list"
        )

    def test_add_user_to_absent_group_fails(self):
        self.mock_module.params.update({"groups": ["Ateam"]})
        self.mock_user.groups = []
        self.mock_user.state = idState.PRESENT
        absent_group = MagicMock()
        absent_group.state = idState.ABSENT
        self.mock_server.group.side_effect = [absent_group]

        user.main()

        self.mock_module.fail_json.assert_called_once_with(
            "Cannot add user test_user to absent group Ateam."
        )
        absent_group.add_user.assert_not_called()

    def test_email_update(self):
        self.mock_module.params.update({"email": "new@example.com"})
        self.mock_user.state = idState.PRESENT
        self.fake_result["changed"] = True

        user.main()

        self.mock_user.edit_settings.assert_called_once_with("email", "new@example.com")
        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_email_update_check_mode(self):
        self.mock_module.params.update({"email": "new@example.com"})
        self.mock_module.check_mode = True
        self.mock_user.state = idState.PRESENT
        self.fake_result["changed"] = True

        user.main()

        self.mock_user.edit_settings.assert_not_called()
        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_email_update_occ_exception(self):
        self.mock_module.params.update({"email": "new@example.com"})
        self.mock_user.state = idState.PRESENT
        self.mock_user.edit_settings.side_effect = OccExceptions(stderr="boom")

        user.main()

        self.mock_module.fail_json.assert_called_once()

    def test_group_occ_exception(self):
        self.mock_module.params.update({"groups": ["Ateam"]})
        self.mock_user.groups = []
        self.mock_user.state = idState.PRESENT
        self.mock_group_add.add_user.side_effect = OccExceptions(stderr="boom")

        user.main()

        self.mock_module.fail_json.assert_called_once()

    def test_display_name_occ_exception(self):
        self.mock_module.params.update({"display_name": "Engineering Team"})
        self.mock_user.state = idState.PRESENT
        self.mock_user.edit_settings.side_effect = OccExceptions(stderr="boom")

        user.main()

        self.mock_module.fail_json.assert_called_once()
