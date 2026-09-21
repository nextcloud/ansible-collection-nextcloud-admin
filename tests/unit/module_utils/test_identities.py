#!/usr/bin/env python
from unittest import TestCase
from unittest.mock import MagicMock, call
import unittest.main
import ansible_collections.nextcloud.admin.plugins.module_utils.identities as ncid
import ansible_collections.nextcloud.admin.plugins.module_utils.exceptions as occ_exceptions
from ansible_collections.nextcloud.admin.plugins.module_utils.server import NCServer


class TestNCIdentity(TestCase):

    def setUp(self):
        self.username = "testuser"
        self.mocked_server = MagicMock(spec=NCServer)
        self.mocked_server.occ.return_value = (
            0,
            f'{{"id":"{self.username}","enabled":true}}',
            "",
            False,
        )
        self.identity = ncid.NCIdentity(self.mocked_server, "user", self.username)

    def test_ncidentity_init_present(self):
        # Mock run_occ to return a user/group that exists
        self.assertEqual(self.identity.state, ncid.idState.PRESENT)

    def test_ncidentity_init_disabled(self):
        # Mock run_occ to return a disabled user/group
        self.mocked_server.occ.return_value = (
            0,
            f'{{"id":"{self.username}","enabled":false}}',
            "",
            False,
        )

        self.identity = ncid.NCIdentity(self.mocked_server, "user", self.username)

        self.assertEqual(self.identity.state, ncid.idState.DISABLED)

    def test_ncidentity_init_absent(self):
        # Mock run_occ to return a non-existent user/group
        self.mocked_server.occ.side_effect = occ_exceptions.OccExceptions(
            stdout="User not found"
        )

        self.identity = ncid.NCIdentity(self.mocked_server, "user", self.username)
        self.assertEqual(self.identity.state, ncid.idState.ABSENT)

    def test_ncidentity_take_action(self):
        # check parameters forwarded to mocked_server.occ

        self.identity._take_action("enable")
        self.mocked_server.occ.assert_called_with(
            ["user:enable", "--no-interaction", self.username]
        )

    def test_ncidentity_take_action_with_arguments(self):
        # check parameters forwarded to mocked_server.occ with additionnal arguments

        self.identity._take_action("enable", "additinal-arg")
        self.mocked_server.occ.assert_called_with(
            ["user:enable", "--no-interaction", "additinal-arg", self.username]
        )

    def test_ncidentity_take_action_with_keyworded_arguments(self):
        # check parameters forwarded to mocked_server.occ with additionnal arguments

        self.identity._take_action("enable", keyword="value")
        self.mocked_server.occ.assert_called_with(
            ["user:enable", "--no-interaction", self.username], keyword="value"
        )

    def test_ncidentity_add(self):

        self.identity.add()
        self.assertEqual(self.identity.state, ncid.idState.PRESENT)
        self.mocked_server.occ.assert_called_with(
            ["user:add", "--no-interaction", self.username],
        )

    def test_ncidentity_delete(self):

        self.identity.delete()
        self.assertEqual(self.identity.state, ncid.idState.ABSENT)
        self.mocked_server.occ.assert_called_with(
            ["user:delete", "--no-interaction", self.username],
        )

    def test_ncidentity_delete_exception(self):
        # The function should pass the exception up a level
        self.mocked_server.occ.side_effect = occ_exceptions.OccExceptions(
            stdout="User not found"
        )

        with self.assertRaises(occ_exceptions.OccExceptions):
            self.identity.delete()


class TestGroup(TestCase):

    def setUp(self):
        self.groupname = "testgroup"
        self.test_users = ["gabitbol", "alice"]
        self.mocked_server = MagicMock(spec=NCServer)
        self.mocked_server.occ.side_effect = (
            (0, f'{{"groupID":"{self.groupname}"}}', "", False),
            (
                0,
                f'{{"{self.groupname}": ["' + '", "'.join(self.test_users) + '"]}',
                "",
                False,
            ),
        )
        self.group = ncid.NCGroup(self.mocked_server, self.groupname)

    def test_ncgroup_init_absent(self):
        # Mock run_occ to return a non-existent group
        self.mocked_server.occ.side_effect = occ_exceptions.OccExceptions(
            stdout="Group not found"
        )
        self.group = ncid.NCGroup(self.mocked_server, self.groupname)
        self.assertEqual(self.group.state, ncid.idState.ABSENT)
        self.mocked_server.occ.assert_called_with(
            ["group:info", "--output=json", self.groupname]
        )

    def test_group_get_users(self):
        # Mock run_occ to return a list of users
        self.mocked_server.occ.side_effect = [
            (0, f'{{"{self.groupname}":["gabitbol", "alice"]}}', "", False)
        ]
        result = self.group._get_users()
        self.mocked_server.occ.assert_called_with(
            ["group:list", self.groupname, "--output", "json_pretty"]
        )
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_ncgroup_init_present_with_users(self):
        # return a group that exists and has some users
        self.assertEqual(self.group.state, ncid.idState.PRESENT)
        self.assertEqual(self.group._users, ["gabitbol", "alice"])

    def test_ncgroup_init_present_no_users(self):
        # return a group that exists and has no users
        self.mocked_server.occ.side_effect = (
            (0, f'{{"groupID":"{self.groupname}"}}', "", False),
            (0, f'{{"{self.groupname}":[]}}', "", False),
        )
        self.group = ncid.NCGroup(self.mocked_server, self.groupname)
        self.assertEqual(self.group.state, ncid.idState.PRESENT)
        self.mocked_server.occ.assert_has_calls(
            [
                call(["group:info", "--output=json", self.groupname]),
                call(["group:list", self.groupname, "--output", "json_pretty"]),
            ]
        )
        self.assertEqual(self.group._users, [])

    def test_group_users_property_when_present(self):
        # Mock run_occ to return a list of users
        self.assertEqual(self.group.users, self.group._users)

    def test_group_users_property_when_absent(self):
        # Mock run_occ to return a non-existent group
        self.mocked_server.occ.side_effect = [
            occ_exceptions.OccExceptions(stdout="Group not found"),
        ]
        self.group = ncid.NCGroup(self.mocked_server, self.groupname)
        self.assertEqual(self.group._users, None)
        self.assertEqual(self.group.users, [])
        self.mocked_server.occ.assert_called_once

    def test_group_add_no_display_name(self):
        self.mocked_server.occ.side_effect = [(0, "ok", "", False)]
        self.group.add()
        self.mocked_server.occ.assert_called_with(
            ["group:add", "--no-interaction", self.groupname]
        )

    def test_group_add_with_display_name(self):
        self.mocked_server.occ.side_effect = [(0, "ok", "", False)]
        self.group.add(display_name="Test Group")
        self.mocked_server.occ.assert_called_with(
            [
                "group:add",
                "--no-interaction",
                "--display-name='Test Group'",
                self.groupname,
            ]
        )

    def test_group_add_user(self):
        username = "johndo"
        self.mocked_server.occ.side_effect = [(0, "ok", "", False)]
        self.group.add_user(username)
        self.mocked_server.occ.assert_called_with(
            ["group:adduser", "--no-interaction", self.groupname, username]
        )
        self.assertIn(username, self.group.users)

    def test_group_remove_user(self):
        self.mocked_server.occ.side_effect = [(0, "ok", "", False)]
        username = self.test_users[0]
        self.group.remove_user(username)
        self.mocked_server.occ.assert_called_with(
            ["group:removeuser", "--no-interaction", self.groupname, username]
        )
        self.assertNotIn(username, self.group.users)

    def test_group_add_user_exception(self):
        username = "johndo"
        self.mocked_server.occ.side_effect = occ_exceptions.OccExceptions(
            stdout="User not found"
        )
        with self.assertRaises(occ_exceptions.IdentityNotPresent):
            self.group.add_user(username)


# class TestUser(TestCase):

#     def setUp(self):
#         self.mock_server = MagicMock()
#         self.mocked_server.occ = patch(
#             "ansible_collections.nextcloud.admin.plugins.module_utils.identities.NCServer.occ"
#         ).start()
#         self.addCleanup(patch.stopall)

#         # Setup default return for successful user lookup
#         self.mocked_server.occ.return_value = (0, '{"id":"testuser","enabled":true}', '', False)

#     def test_user_init_present(self):
#         # Mock run_occ to return a user that exists
#         self.mocked_server.occ.return_value = (0, '{"id":"testuser","enabled":true}', '', False)

#         user = ncid.NCUser(self.mocked_server, "testuser")
#         self.assertEqual(user.state, "PRESENT")

#     def test_user_groups_property(self):
#         # Mock run_occ to return a list of groups
#         self.mocked_server.occ.return_value = (
#             0,
#             '{"groups":["group1","group2"]}',
#             '',
#             False
#         )

#         user = ncid.NCUser(self.mocked_server, "testuser")
#         groups = user.groups

#         self.assertEqual(groups, ["group1", "group2"])

#     def test_user_add_no_args(self):
#         self.mocked_server.occ.return_value = (0, 'Success', '', False)

#         with patch.object(ncid.NCUser, '_take_action') as mock_take_action:
#             mock_take_action.return_value = True
#             user = ncid.NCUser(self.mocked_server, "testuser")
#             result = user.add()

#             self.assertTrue(result)

#     def test_user_add_with_email(self):
#         self.mocked_server.occ.return_value = (0, 'Success', '', False)

#         with patch.object(ncid.NCUser, '_take_action') as mock_take_action:
#             mock_take_action.return_value = True
#             user = ncid.NCUser(self.mocked_server, "testuser", email="test@example.com")
#             result = user.add()

#             self.assertTrue(result)

#     def test_user_add_with_password(self):
#         self.mocked_server.occ.return_value = (0, 'Success', '', False)

#         with patch.object(ncid.NCUser, '_take_action') as mock_take_action:
#             mock_take_action.return_value = True
#             user = ncid.NCUser(self.mocked_server, "testuser", password="secret")
#             result = user.add()

#             self.assertTrue(result)

#     def test_user_add_with_display_name(self):
#         self.mocked_server.occ.return_value = (0, 'Success', '', False)

#         with patch.object(ncid.NCUser, '_take_action') as mock_take_action:
#             mock_take_action.return_value = True
#             user = ncid.NCUser(self.mocked_server, "testuser", display_name="Test User")
#             result = user.add()

#             self.assertTrue(result)

#     def test_user_add_with_all_args(self):
#         self.mocked_server.occ.return_value = (0, 'Success', '', False)

#         with patch.object(ncid.NCUser, '_take_action') as mock_take_action:
#             mock_take_action.return_value = True
#             user = ncid.NCUser(
#                 mocked_server,
#                 "testuser",
#                 email="test@example.com",
#                 password="secret",
#                 display_name="Test User"
#             )
#             result = user.add()

#             self.assertTrue(result)

#     def test_user_disable(self):
#         self.mocked_server.occ.return_value = (0, 'Success', '', False)

#         with patch.object(ncid.NCUser, '_take_action') as mock_take_action:
#             mock_take_action.return_value = True
#             user = ncid.NCUser(self.mocked_server, "testuser")
#             result = user.disable()

#             self.assertTrue(result)

#     def test_user_enable(self):
#         self.mocked_server.occ.return_value = (0, 'Success', '', False)

#         with patch.object(ncid.NCUser, '_take_action') as mock_take_action:
#             mock_take_action.return_value = True
#             user = ncid.NCUser(self.mocked_server, "testuser")
#             result = user.enable()

#             self.assertTrue(result)

#     def test_user_reset_password(self):
#         self.mocked_server.occ.return_value = (0, 'Success', '', False)

#         with patch.object(ncid.NCUser, '_take_action') as mock_take_action:
#             mock_take_action.return_value = True
#             user = ncid.NCUser(self.mocked_server, "testuser")
#             result = user.reset_password("newpassword")

#             self.assertTrue(result)

#     def test_user_edit_settings(self):
#         self.mocked_server.occ.return_value = (0, 'Success', '', False)

#         with patch.object(ncid.NCUser, '_take_action') as mock_take_action:
#             mock_take_action.return_value = True
#             user = ncid.NCUser(self.mocked_server, "testuser")
#             result = user.edit_settings(dict(setting="value"))

#             self.assertTrue(result)

#     def test_user_groups_exception(self):
#         self.mocked_server.occ.side_effect = occ_exceptions.OccExceptions("User not found")

#         with self.assertRaises(occ_exceptions.OccExceptions):
#             user = ncid.NCUser(self.mocked_server, "testuser")
#             _ = user.groups


if __name__ == "__main__":
    unittest.main()
