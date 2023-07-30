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
      type: string
    is_shipped:
      description: If the application was shipped with the nextcloud server initially.
      type: boolean
      returned: success
    version:
      description: Current version Installed for this application.
      type: string
      returned: success
    update_available:
      description: If the application has an available update.
      type: bool
      returned: success
    version_available:
      description: What is the version proposed for update.
      type: string
      returned: success
    app_path:
      description: The full path to the application folder.
      type: string
      returned: success
"""

import copy
import json
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.nextcloud.admin.plugins.module_utils.occ import run_occ
from ansible_collections.nextcloud.admin.plugins.module_utils.occ_args_common import (
    OCC_ARGS_SPEC,
)


def check_app_update(module, app_name):
    _check_app_update = run_occ(module, ["app:update", "--showonly", app_name])[1]
    if _check_app_update != "":
        app_update = True
        app_update_version_available = _check_app_update.split()[-1]
    else:
        app_update = False
        app_update_version_available = None

    return app_update, app_update_version_available


def get_app_info(module, app_name, all_shipped_apps, all_present_apps):
    if app_name in all_present_apps["enabled"].keys():
        app_state = "present"
        app_version = all_present_apps["enabled"][app_name]
    elif app_name in all_present_apps["disabled"].keys():
        app_state = "disabled"
        app_version = all_present_apps["disabled"][app_name]
    else:
        return dict(state="absent")
    _app_updatable, _app_updatable_to = check_app_update(module, app_name)
    return dict(
        state=app_state,
        is_shipped=app_name
        in [s for a in all_shipped_apps.keys() for s in all_shipped_apps[a].keys()],
        version=app_version,
        update_available=_app_updatable,
        version_available=_app_updatable_to,
        path=run_occ(module, ["app:getpath", app_name])[1].strip(),
    )


def args_spec():
    arg_spec = copy.deepcopy(OCC_ARGS_SPEC)
    arg_spec.update(
        dict(
            name=dict(type="str", required=True),
        ),
    )
    return arg_spec


def main():
    global module

    module = AnsibleModule(
        argument_spec=args_spec(),
        supports_check_mode=True,
    )
    app_name = module.params.get("name")
    # start by gathering all apps present. differentiating between shipped apps and not to reduce calls to occ
    all_shipped_apps = json.loads(
        run_occ(module, ["app:list", "--output=json", "--shipped=true"])[1]
    )
    all_present_apps = json.loads(run_occ(module, ["app:list", "--output=json"])[1])
    result = {}

    if app_name in all_present_apps["enabled"].keys():
        app_state = "present"
        app_version = all_present_apps["enabled"][app_name]
    elif app_name in all_present_apps["disabled"].keys():
        app_state = "disabled"
        app_version = all_present_apps["disabled"][app_name]
    else:
        app_state = None
        result = dict(state="absent", name=app_name)

    if app_state in ["present", "disabled"]:
        _app_updatable, _app_updatable_to = check_app_update(module, app_name)
        result = dict(
            name=app_name,
            state=app_state,
            is_shipped=app_name
            in [s for a in all_shipped_apps.keys() for s in all_shipped_apps[a].keys()],
            version=app_version,
            update_available=_app_updatable,
            version_available=_app_updatable_to,
            app_path=run_occ(module, ["app:getpath", app_name])[1].strip(),
        )

    module.exit_json(changed=False, **result)


if __name__ == "__main__":
    main()
