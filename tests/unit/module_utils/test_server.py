#!/usr/bin/env python
from unittest import TestCase
from unittest.mock import MagicMock, call, patch
import unittest
import json
from ansible_collections.nextcloud.admin.plugins.module_utils.server import NCServer

SERVER_MODULE = "ansible_collections.nextcloud.admin.plugins.module_utils.server"


class TestNCServerBase(TestCase):

    def setUp(self):
        self.status = {
            "installed": True,
            "version": "29.0.1.1",
            "versionstring": "29.0.1",
            "edition": "",
            "maintenance": False,
            "needsDbUpgrade": False,
            "productname": "Nextcloud",
            "extendedSupport": False,
        }
        self.module = MagicMock()
        patcher = patch(f"{SERVER_MODULE}.run_occ")
        self.mock_run_occ = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_run_occ.return_value = (0, json.dumps(self.status), "", False)
        self.server = NCServer(self.module)
        self.mock_run_occ.reset_mock()
        self.mock_run_occ.return_value = (0, "", "", False)


class TestNCServerInit(TestNCServerBase):

    def test_server_init_runs_status(self):
        self.mock_run_occ.return_value = (0, json.dumps(self.status), "", False)
        NCServer(self.module)
        self.mock_run_occ.assert_called_once_with(
            self.module,
            command=["status", "--output", "json", "--no-warnings"],
        )

    def test_server_init_sets_attributes_from_status(self):
        self.assertTrue(self.server.installed)
        self.assertEqual(self.server.version, "29.0.1.1")
        self.assertEqual(self.server.versionstring, "29.0.1")
        self.assertEqual(self.server.productname, "Nextcloud")
        self.assertFalse(self.server.maintenance)
        self.assertFalse(self.server.extendedSupport)

    def test_server_init_empty_caches(self):
        self.assertEqual(self.server._occ_commands, {})
        self.assertEqual(self.server._setupChecks, {})
        self.assertEqual(self.server._apps, {"shipped": {}, "external": {}})


class TestNCServerOcc(TestNCServerBase):

    def test_occ_forwards_command_to_run_occ(self):
        self.mock_run_occ.return_value = (0, "out", "err", False)
        result = self.server.occ(["status"])
        self.mock_run_occ.assert_called_once_with(self.module, command=["status"])
        self.assertEqual(result, (0, "out", "err", False))

    def test_occ_forwards_kwargs(self):
        self.server.occ(["status"], environ_update={"NC_PASS": "secret"})
        self.mock_run_occ.assert_called_once_with(
            self.module, command=["status"], environ_update={"NC_PASS": "secret"}
        )

    def test_occ_commands_property(self):
        self.mock_run_occ.return_value = (
            0,
            json.dumps(
                {
                    "namespaces": [
                        {"id": "user", "commands": ["user:add", "user:delete"]},
                        {"id": "app", "commands": ["app:list"]},
                    ]
                }
            ),
            "",
            False,
        )
        self.assertEqual(
            self.server.occ_commands,
            {"user": ["user:add", "user:delete"], "app": ["app:list"]},
        )

    def test_occ_commands_property_is_cached(self):
        self.mock_run_occ.return_value = (
            0,
            json.dumps({"namespaces": [{"id": "user", "commands": ["user:add"]}]}),
            "",
            False,
        )
        self.server.occ_commands
        self.server.occ_commands
        self.mock_run_occ.assert_called_once()


class TestNCServerApps(TestNCServerBase):

    def setUp(self):
        super().setUp()
        self.shipped = {
            "enabled": {"files": "1.0"},
            "disabled": {"encryption": "1.0"},
        }
        self.external = {
            "enabled": {"admin_audit": "2.0"},
            "disabled": {"richdocuments": "3.0"},
        }

    def test_get_apps_shipped(self):
        self.mock_run_occ.return_value = (0, json.dumps(self.shipped), "", False)
        self.server._get_apps(shipped=True)
        self.assertEqual(self.server._apps["shipped"], self.shipped)
        self.assertEqual(self.server._apps["external"], {})
        command = self.mock_run_occ.call_args.kwargs["command"]
        self.assertIn("--shipped", command)
        self.assertIn("--output=json", command)

    def test_get_apps_external(self):
        self.mock_run_occ.return_value = (0, json.dumps(self.external), "", False)
        self.server._get_apps(shipped=False)
        self.assertEqual(self.server._apps["external"], self.external)
        self.assertEqual(self.server._apps["shipped"], {})
        command = self.mock_run_occ.call_args.kwargs["command"]
        self.assertNotIn("--shipped", command)

    def test_refresh_shipped_apps(self):
        with patch.object(self.server, "_get_apps") as mock_get_apps:
            self.server.refresh_shipped_apps()
            mock_get_apps.assert_called_once_with(shipped=True)

    def test_refresh_external_apps(self):
        with patch.object(self.server, "_get_apps") as mock_get_apps:
            self.server.refresh_external_apps()
            mock_get_apps.assert_called_once_with(shipped=False)

    def test_refresh_apps_refreshes_both(self):
        with patch.object(self.server, "_get_apps") as mock_get_apps:
            self.server.refresh_apps()
            mock_get_apps.assert_has_calls([call(shipped=True), call(shipped=False)])

    def test_shipped_apps_property_loads_when_empty(self):
        self.mock_run_occ.return_value = (0, json.dumps(self.shipped), "", False)
        self.assertEqual(self.server.shipped_apps, self.shipped)
        self.mock_run_occ.assert_called_once()

    def test_shipped_apps_property_cached(self):
        self.server._apps["shipped"] = self.shipped
        self.assertEqual(self.server.shipped_apps, self.shipped)
        self.mock_run_occ.assert_not_called()

    def test_external_apps_property_loads_when_empty(self):
        self.mock_run_occ.return_value = (0, json.dumps(self.external), "", False)
        self.assertEqual(self.server.external_apps, self.external)
        self.mock_run_occ.assert_called_once()

    def test_external_apps_property_cached(self):
        self.server._apps["external"] = self.external
        self.assertEqual(self.server.external_apps, self.external)
        self.mock_run_occ.assert_not_called()

    def test_apps_property_merges_enabled_and_disabled(self):
        self.server._apps["shipped"] = self.shipped
        self.server._apps["external"] = self.external
        self.assertEqual(
            self.server.apps,
            {
                "enabled": {"admin_audit": "2.0", "files": "1.0"},
                "disabled": {"richdocuments": "3.0", "encryption": "1.0"},
            },
        )


class TestNCServerSetupChecks(TestNCServerBase):

    def setUp(self):
        super().setUp()
        self.report = {
            "security": {
                "OCA\\Settings\\Check\\Foo": {
                    "severity": "warning",
                    "description": "foo description",
                },
                "OCA\\Settings\\Check\\Bar": {
                    "severity": "info",
                    "description": None,
                },
            },
            "system": {
                "OCA\\Files\\Check\\Baz": {
                    "severity": "error",
                    "description": "baz description",
                },
            },
        }

    def test_run_setup_checks_groups_by_category_and_app(self):
        self.mock_run_occ.return_value = (0, json.dumps(self.report), "", False)
        self.server.run_SetupChecks()
        self.assertEqual(
            self.server._setupChecks,
            {
                "security": {
                    "Settings": [
                        {
                            "id": "Foo",
                            "severity": "warning",
                            "description": "foo description",
                        },
                        {"id": "Bar", "severity": "info", "description": None},
                    ]
                },
                "system": {
                    "Files": [
                        {
                            "id": "Baz",
                            "severity": "error",
                            "description": "baz description",
                        }
                    ]
                },
            },
        )

    def test_run_setup_checks_command(self):
        self.mock_run_occ.return_value = (0, "{}", "", False)
        self.server.run_SetupChecks()
        command = self.mock_run_occ.call_args.kwargs["command"]
        self.assertIn("setupchecks", command)
        self.assertIn("--output=json", command)

    def test_setup_checks_property_loads_when_empty(self):
        self.mock_run_occ.return_value = (0, json.dumps(self.report), "", False)
        self.assertIn("security", self.server.setupChecks)
        self.mock_run_occ.assert_called_once()

    def test_setup_checks_property_cached(self):
        self.server._setupChecks = {"security": {}}
        self.assertEqual(self.server.setupChecks, {"security": {}})
        self.mock_run_occ.assert_not_called()


class TestNCServerMaintenance(TestNCServerBase):

    def test_set_maintenance_enable(self):
        self.server.set_maintenance(True)
        self.mock_run_occ.assert_called_once_with(
            self.module,
            command=[
                "maintenance:mode",
                "--on",
                "--no-interaction",
                "--no-warnings",
            ],
        )
        self.assertTrue(self.server.maintenance)

    def test_set_maintenance_disable(self):
        self.server.maintenance = True
        self.server.set_maintenance(False)
        self.mock_run_occ.assert_called_once_with(
            self.module,
            command=[
                "maintenance:mode",
                "--off",
                "--no-interaction",
                "--no-warnings",
            ],
        )
        self.assertFalse(self.server.maintenance)

    def test_set_maintenance_noop_when_unchanged(self):
        self.server.set_maintenance(False)
        self.mock_run_occ.assert_not_called()


class TestNCServerInstall(TestNCServerBase):

    def setUp(self):
        super().setUp()
        self.server.installed = False

    def test_install_raises_when_already_installed(self):
        self.server.installed = True
        with self.assertRaises(RuntimeError):
            self.server.install(database_type="mysql")
        self.mock_run_occ.assert_not_called()

    def test_install_converts_kwargs_to_options(self):
        self.server.install(
            database_type="mysql",
            database_name="nextcloud",
            database_port=3306,
            admin_user="admin",
            data_dir="/var/www/nextcloud/data",
        )
        self.mock_run_occ.assert_called_once_with(
            self.module,
            command=[
                "maintenance:install",
                "--no-interaction",
                "--no-warnings",
                "--database-type",
                "mysql",
                "--database-name",
                "nextcloud",
                "--database-port",
                "3306",
                "--admin-user",
                "admin",
                "--data-dir",
                "/var/www/nextcloud/data",
            ],
        )

    def test_install_true_value_is_flag_only(self):
        self.server.install(password_salt="salt", database_ssl_mode="require")
        command = self.mock_run_occ.call_args.kwargs["command"]
        self.assertIn("--password-salt", command)
        self.assertNotIn("True", command)

    def test_install_false_value_is_dropped(self):
        self.server.install(admin_pass="secret", database_pass=False)
        command = self.mock_run_occ.call_args.kwargs["command"]
        self.assertNotIn("--database-pass", command)
        self.assertIn("--admin-pass", command)

    def test_install_bool_params_true(self):
        self.server.install(disable_admin_user=True, database_ssl_no_verify=True)
        self.mock_run_occ.assert_called_once_with(
            self.module,
            command=[
                "maintenance:install",
                "--no-interaction",
                "--no-warnings",
                "--disable-admin-user",
                "--database-ssl-no-verify",
            ],
        )

    def test_install_bool_params_default_to_absent(self):
        self.server.install(admin_user="admin")
        command = self.mock_run_occ.call_args.kwargs["command"]
        self.assertNotIn("--disable-admin-user", command)
        self.assertNotIn("--database-ssl-no-verify", command)


class TestNCServerFactories(TestNCServerBase):

    def test_app_returns_ncapp(self):
        with patch(f"{SERVER_MODULE}.NCApp") as mock_app:
            result = self.server.app("files")
            mock_app.assert_called_once_with(self.server, app_name="files")
            self.assertEqual(result, mock_app.return_value)

    def test_group_returns_ncgroup(self):
        with patch(f"{SERVER_MODULE}.NCGroup") as mock_group:
            result = self.server.group("admins")
            mock_group.assert_called_once_with(self.server, ident="admins")
            self.assertEqual(result, mock_group.return_value)

    def test_user_returns_ncuser(self):
        with patch(f"{SERVER_MODULE}.NCUser") as mock_user:
            result = self.server.user("alice")
            mock_user.assert_called_once_with(self.server, ident="alice")
            self.assertEqual(result, mock_user.return_value)


if __name__ == "__main__":
    unittest.main()
