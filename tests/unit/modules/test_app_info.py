from unittest import TestCase
from unittest.mock import patch, MagicMock, ANY
from ansible_collections.nextcloud.admin.plugins.modules import app_info
from ansible.module_utils import basic

testAppInfos = {
    "author": {
        "@attributes": {"mail": "skjnldsv@protonmail.com"},
        "@value": "John Molakvoæ",
    },
    "bugs": "https://github.com/nextcloud/photos/issues",
    "category": ["multimedia"],
    "commands": ["OCA\\Photos\\Command\\AlbumCreateCommand"],
    "dependencies": {"backend": [], "nextcloud": {}},
    "description": "Your memories under your control",
    "id": "photos",
    "info": [],
    "licence": "agpl",
    "name": "Photos",
    "namespace": "Photos",
    "public": [],
    "remote": [],
    "repository": "https://github.com/nextcloud/photos.git",
    "summary": "Your memories under your control",
    "two-factor-providers": [],
    "version": "4.0.0-dev.1",
    "website": "https://github.com/nextcloud/photos",
    "settings": {
        "admin": [],
        "admin-section": [],
        "personal": [],
        "personal-section": [],
    },
}


class TestAppInfoModuleWithoutSettings(TestCase):

    def setUp(self, show_settings=False):
        self.mock_module = MagicMock(spec=basic.AnsibleModule)
        self.expected_result = {"changed": False}
        self.facts_collected = {
            "state": "present",
            "is_shipped": True,
            "version": "1.2.3",
        }
        self.mock_module.params = {"name": "photos", "show_settings": show_settings}
        self.mock_module._debug = False
        self.mock_module._verbosity = 0
        self.module_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app_info.AnsibleModule"
        )
        self.mock_module_class = self.module_patcher.start()
        self.mock_module_class.return_value = self.mock_module
        self.server_patcher = patch(
            "ansible_collections.nextcloud.admin.plugins.modules.app_info.NCServer"
        )
        self.mock_server_class = self.server_patcher.start()
        self.mock_server = self.mock_server_class.return_value
        self.mock_app = self.mock_server.app.return_value
        self.mock_app.infos = testAppInfos

    def tearDown(self):
        # Stop the patchers after each test
        self.module_patcher.stop()
        self.server_patcher.stop()

    def test_app_absent(self):
        """
        Test the behavior of the app_info module when the app is absent.
        The expected result is that the module exits properly with a state indicating
        the app is not present.
        """
        # Mocking app instance with state 'absent'
        self.mock_app.get_facts.return_value = {"state": "absent"}
        self.mock_app.state = "absent"

        app_info.main()

        self.mock_module.exit_json.assert_called_with(
            **self.expected_result, state="absent"
        )

    def test_app_present_with_low_verbosity(self):
        """
        Test the behavior of the app_info module when the app is present
        and the requested verbosity is not high.
        The expected result is that the module exits properly with a state indicating
        the app is present and display only a subset of the appInfos.
        """

        self.mock_app.get_facts.return_value = self.facts_collected
        app_info.main()

        self.mock_module.exit_json.assert_called_with(
            **self.expected_result,
            **self.facts_collected,
            AppInfos=ANY,  # Ignore the contents of AppInfos here
        )
        actual_args = self.mock_module.exit_json.call_args[1]
        app_infos = actual_args["AppInfos"]
        expected_keys = {
            "id",
            "name",
            "summary",
            "description",
            "licence",
            "author",
            "bugs",
            "category",
            "types",
            "dependencies",
        }
        self.assertEqual(
            set(app_infos.keys()), expected_keys
        )  # Check if all expected keys are present

    def test_app_present_with_verbosity_3_or_more(self):
        """
        Test the behavior of the app_info module when the app is present
        and the requested verbosity is high.
        The expected result is that the module exits properly with a state indicating
        the app is present and display all the appInfos available.
        """
        self.mock_module._debug = False
        self.mock_module._verbosity = 3
        self.mock_app.get_facts.return_value = self.facts_collected

        app_info.main()

        self.mock_module.exit_json.assert_called_with(
            **self.expected_result,
            **self.facts_collected,
            AppInfos=testAppInfos,
        )


class TestAppInfoModuleWithSettings(TestAppInfoModuleWithoutSettings):
    def setUp(self, show_settings=True):
        """
        This is just a slight variation of the normal tests when the arg show_settings
        is set to true.
        Adjust expected results and facts accordingly
        """
        super().setUp(show_settings=True)
        self.mock_app.current_settings = {}
        self.expected_result.update(
            current_settings={}  # pyright: ignore[reportArgumentType]
        )
        self.mock_app.default_settings = {}
        self.facts_collected.update(default_settings={})
