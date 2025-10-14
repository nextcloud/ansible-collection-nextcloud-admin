from unittest import TestCase
from unittest.mock import patch, MagicMock, ANY
from ansible_collections.nextcloud.admin.plugins.modules import group
from ansible.module_utils import basic
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    IdentityNotPresent,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.identities import (
    idState,
)


class TestGroupModule(TestCase):
    def setUp(self):
        self.group_id = "test_group"

        self.module_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.group.AnsibleModule"
        )
        self.mock_module = MagicMock(spec=basic.AnsibleModule)
        self.mock_module_obj = self.module_patcher.start()
        self.mock_module.check_mode = False
        self.mock_module_obj.return_value = self.mock_module
        self.mock_module.params = {
            "nextcloud_path": "/path/to/nextcloud",
            "php_runtime": "/usr/bin/php",
            "id": self.group_id,
        }

        self.group_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.group.Group"
        )
        self.mock_group = MagicMock()
        self.mock_group_obj = self.group_patcher.start()
        self.fake_result = dict(
            changed=False,
            added_users=[],
            removed_users=[],
        )
        self.mock_group_obj.return_value = self.mock_group

    def tearDown(self):
        self.module_patcher.stop()
        self.group_patcher.stop()

    def test_group_creation(self):
        self.mock_group.state = idState.ABSENT
        self.fake_result["changed"] = True

        group.main()

        self.mock_group.add.assert_called_once_with(None)
        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_group_creation_with_display_name(self):
        self.mock_module.params.update(
            {"state": "present", "display_name": "Engineering Team"}
        )
        self.mock_group.state = idState.ABSENT
        self.fake_result["changed"] = True

        group.main()

        self.mock_group.add.assert_called_once_with("Engineering Team")
        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_group_deletion(self):
        self.mock_group.state = idState.PRESENT
        self.mock_module.params["state"] = "absent"
        self.fake_result["changed"] = True

        group.main()

        self.mock_group.delete.assert_called_once()
        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_no_operation_on_existing_group(self):
        self.mock_group.state = idState.PRESENT

        group.main()

        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_no_operation_on_absent_group(self):
        self.mock_group.state = idState.ABSENT
        self.mock_module.params["state"] = "absent"

        group.main()

        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_group_exact_match_users(self):
        self.mock_module.params.update({"users": ["alice", "bob"], "state": "present"})
        self.mock_group.users = ["alice", "john"]
        self.mock_group.state = idState.PRESENT
        self.fake_result["changed"] = True
        self.fake_result["added_users"] = ["bob"]
        self.fake_result["removed_users"] = ["john"]

        group.main()

        self.mock_group.add_user.assert_called_once_with("bob")
        self.mock_group.remove_user.assert_called_once_with("john")
        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_append_users_to_group(self):
        self.mock_module.params.update({"users": ["charlie"], "state": "append_users"})
        self.mock_group.users = ["alice", "bob"]
        self.mock_group.state = idState.PRESENT
        self.fake_result["changed"] = True
        self.fake_result["added_users"] = ["charlie"]

        group.main()

        self.mock_group.add_user.assert_called_once_with("charlie")
        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_remove_users_from_group(self):
        self.mock_module.params.update({"users": ["dave"], "state": "remove_users"})
        self.mock_group.users = ["dave", "eve"]
        self.mock_group.state = idState.PRESENT
        self.fake_result["changed"] = True
        self.fake_result["removed_users"] = ["dave"]

        group.main()

        self.mock_group.remove_user.assert_called_once_with("dave")
        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_ignore_missing_users_on_add(self):
        self.mock_module.params.update(
            {"users": ["frank"], "ignore_missing_users": True, "state": "append_users"}
        )
        self.mock_group.users = ["alice"]
        self.mock_group.state = idState.PRESENT
        self.mock_group.add_user.side_effect = IdentityNotPresent("user", "frank")

        group.main()

        # Since ignore_missing_users is True, we expect no raise and exit normally
        self.mock_module.exit_json.assert_called_once_with(**self.fake_result)

    def test_fail_on_missing_users_on_add(self):
        self.mock_module.params.update(
            {
                "users": ["george"],
                "ignore_missing_users": False,
                "state": "append_users",
            }
        )
        self.mock_group.users = ["alice"]
        self.mock_group.state = idState.PRESENT
        self.mock_group.add_user.side_effect = IdentityNotPresent("user", "george")

        group.main()

        self.mock_module.fail_json.assert_called_once()

    def test_error_on_missing_group_with_users(self):
        self.mock_module.params.update(
            {"users": ["harry"], "error_on_missing": True, "state": "present"}
        )
        self.mock_group.state = idState.ABSENT

        group.main()

        self.mock_module.fail_json.assert_called_once_with(
            msg=f"Group {self.group_id} is absent while trying to manage its users."
        )
