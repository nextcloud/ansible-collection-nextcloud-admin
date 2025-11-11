from unittest import TestCase
from unittest.mock import patch, MagicMock
from ansible_collections.nextcloud.admin.plugins.modules import user
from ansible.module_utils import basic
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    IdentityNotPresent,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.identities import (
    idState,
)


class TestUserModule(TestCase):
    def setUp(self):
        self.user_id = "test_user"

        self.module_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.user.AnsibleModule"
        )
        self.mock_module = MagicMock(spec=basic.AnsibleModule)
        self.mock_module_obj = self.module_patcher.start()
        self.mock_module.check_mode = False
        self.mock_module_obj.return_value = self.mock_module
        self.mock_module.params = {
            "nextcloud_path": "/path/to/nextcloud",
            "php_runtime": "/usr/bin/php",
            "id": self.user_id,
            "state": "present",
            "password": "test_password",
        }

        self.user_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.user.User"
        )
        self.mock_user = MagicMock()
        self.mock_user_obj = self.user_patcher.start()

        self.group_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.user.Group"
        )
        self.mock_group_obj = self.group_patcher.start()
        self.mock_group_add = MagicMock()
        self.mock_group_add.state = idState.PRESENT
        self.mock_group_remove = MagicMock()
        self.mock_group_remove.state = idState.PRESENT
        self.mock_group_obj.side_effect = [self.mock_group_add, self.mock_group_remove]

        self.fake_result = dict(
            changed=False,
        )
        self.mock_user_obj.return_value = self.mock_user

    def tearDown(self):
        self.module_patcher.stop()
        self.user_patcher.stop()
        self.group_patcher.stop()

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
