#!/usr/bin/env python
from unittest import TestCase
from unittest.mock import MagicMock, call
import unittest.main
import json
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


class TestUser(TestCase):

    def setUp(self):
        self.testuser = dict(
            id="gabitbol",
            enabled=True,
            display_name="Georges Abitbol",
            email="goat.abitbol@american.class",
            groups=["tegzas"],
        )
        self.mocked_server = MagicMock(spec=NCServer)

        # Setup default return for successful user lookup
        self.mocked_server.occ.return_value = (0, json.dumps(self.testuser), "", False)
        self.user = ncid.NCUser(self.mocked_server, str(self.testuser["id"]))

    def test_user_init_present(self):
        self.assertEqual(self.user.state, ncid.idState.PRESENT)

    def test_user_init_absent(self):
        self.mocked_server.occ.side_effect = occ_exceptions.OccExceptions(
            stdout="User does not exist",
            stderr="",
        )
        user = ncid.NCUser(self.mocked_server, "testuser")
        self.assertEqual(user.state, ncid.idState.ABSENT)
        self.assertDictEqual(user.infos, {})

    def test_user_groups_property(self):
        groups = self.user.groups
        self.assertEqual(groups, self.testuser["groups"])

    def test_user_add_with_no_args(self):
        with self.assertRaises(ValueError):
            self.user.add()

    def test_user_add_with_gen_pwd(self):
        self.user.add(generate_password=True)
        self.mocked_server.occ.assert_called_with(
            [
                "user:add",
                "--no-interaction",
                "--generate-password",
                self.testuser["id"],
            ],
            environ_update={},
        )

    def test_user_add_with_password(self):
        self.user.add(password="total-investigation")
        self.mocked_server.occ.assert_called_with(
            [
                "user:add",
                "--no-interaction",
                "--password-from-env",
                self.testuser["id"],
            ],
            environ_update={"NC_PASS": "total-investigation"},
        )

    def test_user_add_with_both_pwd_and_gen_pwd(self):
        self.user.add(generate_password=True, password="total-investigation")
        self.mocked_server.occ.assert_called_with(
            [
                "user:add",
                "--no-interaction",
                "--password-from-env",
                self.testuser["id"],
            ],
            environ_update={"NC_PASS": "total-investigation"},
        )

    def test_user_add_with_args_gen_pwd(self):
        kwargs = {**self.testuser}
        kwargs.pop("id")
        kwargs.pop("enabled")
        kwargs["generate_password"] = True
        self.user.add(**kwargs)  # pyright: ignore[reportArgumentType]
        self.mocked_server.occ.assert_called_with(
            [
                "user:add",
                "--no-interaction",
                "--generate-password",
                "--display-name",
                self.testuser["display_name"],
                "--email",
                self.testuser["email"],
                "--group",
                self.testuser["groups"][0],  # pyright: ignore[reportIndexIssue]
                self.testuser["id"],
            ],
            environ_update={},
        )

    def test_user_disable(self):
        self.user.disable()
        self.mocked_server.occ.assert_called_with(
            ["user:disable", "--no-interaction", self.testuser["id"]]
        )
        self.assertEqual(self.user.state, ncid.idState.DISABLED)

    def test_user_enable(self):
        self.user.state = ncid.idState.DISABLED
        self.user.enable()
        self.mocked_server.occ.assert_called_with(
            ["user:enable", "--no-interaction", self.testuser["id"]]
        )
        self.assertEqual(self.user.state, ncid.idState.PRESENT)

    def test_user_reset_pwd_with_no_arg(self):
        self.user.reset_password()
        self.mocked_server.occ.assert_called_with(
            ["user:resetpassword", "--no-interaction", self.testuser["id"]],
            environ_update={},
        )

    def test_user_reset_pwd_with_password(self):
        self.user.reset_password(password="total-investigation")
        self.mocked_server.occ.assert_called_with(
            [
                "user:resetpassword",
                "--no-interaction",
                "--password-from-env",
                self.testuser["id"],
            ],
            environ_update={"NC_PASS": "total-investigation"},
        )


# TODO: User's Settings management
#     def test_user_edit_settings(self):
#         self.mocked_server.occ.return_value = (0, 'Success', '', False)


if __name__ == "__main__":
    unittest.main()
