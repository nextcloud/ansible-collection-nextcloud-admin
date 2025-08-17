#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, Marc Crébassa <aalaesar@gmail.com>
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

DOCUMENTATION = r"""

module: app_info

short_description: Display informations about an application installed in a Nextcloud server

author:
  - "Marc Crébassa (@aalaesar)"

description:
  - Return a set of facts about the requested application.
  - Always returns state as 'OK'.
  - This module requires to be run with advanced privileges
    unless it is run as the user that own the occ tool.

extends_documentation_fragment:
  - nextcloud.admin.occ_common_options

options:
  name:
    description: Collect informations for a specified nextcloud application.
    type: str
    required: true
    aliases: ["id"]
  show_settings:
    description:
      - EXPERIMENTAL.
      - Display application settings - default values and current values.
    type: bool
    required: false
    default: false

requirements:
  - "python >=3.6"
"""

EXAMPLES = r"""
- name: get the list of applications installed
  nextcloud.admin.app_info:
    nextcloud_path: /var/lib/www/nextcloud
  register: nc_apps_list

- name: get configuration information about an application
  nextcloud.admin.app_info:
    nextcloud_path: /var/lib/www/nextcloud
    name: photos
"""
RETURN = r"""
nextcloud_application:
  description: The informations collected for the application requested.
  returned: always
  type: dict
  contains:
    state:
      description:
        - Either `present`, `disabled` or `absent` when the application is installed and enabled, installed and disabled or not installed.
        - If `absent`, other fields are not returned.
      returned: always
      type: str
    is_shipped:
      description: If the application was shipped with the nextcloud server initially.
      type: bool
      returned: success
    version:
      description: Current version Installed for this application.
      type: str
      returned: success
    update_available:
      description: If the application has an available update.
      type: bool
      returned: success
    version_available:
      description: What is the version proposed for update.
      type: str
      returned: success
    app_path:
      description: The full path to the application folder.
      type: str
      returned: success
    appInfos:
      description: Infos exposed by the application's manifest.
      type: dict
      returned: success
    default_settings:
      description: All the application setting and their default values.
      type: dict
      returned: When show_settings is True
    current_settings:
      description:
        - The app config returned by the server.
        - Content depends on the implementation of nextcloud AppConfig APIs by the developpers.
      type: dict
      returned: When show_settings is True

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nextcloud.admin.plugins.module_utils.app import app
from ansible_collections.nextcloud.admin.plugins.module_utils.nc_tools import (
    extend_nc_tools_args_spec,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.exceptions import (
    AppExceptions,
)

module_arg_spec = dict(
    name=dict(type="str", required=True, aliases=["id"]),
    show_settings=dict(type="bool", required=False, default=False),
)


def main():
    global module

    module = AnsibleModule(
        argument_spec=extend_nc_tools_args_spec(module_arg_spec),
        supports_check_mode=True,
    )
    info_keys = [
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
    ]
    result = dict(changed=False)
    try:
        nc_app = app(module, module.params.get("name"))
        result.update(nc_app.get_facts())
        if nc_app.state != "absent":
            # Display all appInfo if in debug or only a small list of usefull infos.
            if module._debug or module._verbosity >= 3:
                result["AppInfos"] = nc_app.infos
            else:
                result["AppInfos"] = {k: nc_app.infos.get(k) for k in info_keys}

        if module.params.get("show_settings"):
            result["current_settings"] = nc_app.current_settings
            if nc_app.state != "absent":
                result["default_settings"] = nc_app.default_settings
    except AppExceptions as e:
        e.fail_json(module, **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
