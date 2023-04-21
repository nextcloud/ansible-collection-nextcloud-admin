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

module: app_infos

short_description: Display informations about applications present in a Nextcloud server

author:
  - "Marc Crébassa (@aalaesar)"

description:
  - Return a set of facts about applications present in a Nextcloud server.
  - Always returns state as 'OK'.
  - This module requires to be run with advanced privileges
    unless it is run as the user that own the occ tool.

extends_documentation_fragment:
  - nextcloud.admin.occ_common_options

options:
  name:
    description:
      - Only collect informations for this application.
      - If not set, informations are collected for all present applications.
      - Depending on the size of your cluster, the module may take a while to gather informations for all applications.
    type: str
    default: null

requirements:
  - "python >=3.6"
"""

EXAMPLES = r"""
- name: get the list of applications installed
  nextcloud.admin.app_infos:
    nextcloud_path: /var/lib/www/nextcloud
  register: nc_apps_list

- name: get configuration information about an application
  nextcloud.admin.app_infos:
    nextcloud_path: /var/lib/www/nextcloud
    name: photos

"""
RETURN = r"""
nextcloud_applications:
  description: The informations collected for each application requested or any present.
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
      description: What is the version proposed for update
      type: string
      returned: success
    path:
      description: The full path to the application folder.
      type: string
      returned: success
updates_available:
  description: All applications name and version eligible for update
  returned: always
  type: dict
"""

import copy
import json
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.nextcloud.admin.plugins.module_utils.occ import run_occ
from ansible_collections.nextcloud.admin.plugins.module_utils.app_infos import (
    get_app_infos,
)
from ansible_collections.nextcloud.admin.plugins.module_utils.occ_args_common import (
    OCC_ARGS_SPEC,
)


def args_spec():
    arg_spec = copy.deepcopy(OCC_ARGS_SPEC)
    arg_spec.update(
        dict(
            name=dict(
                type="str",
                required=False,
                default=None,
            ),
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
    result = dict(nextcloud_applications={}, updates_available={})

    # if name is not none, proceed to get app info for this one
    if app_name:
        result["nextcloud_applications"][app_name] = get_app_infos(
            module, app_name, all_shipped_apps, all_present_apps
        )
        if (
            result["nextcloud_applications"][app_name]["state"] == "present"
            and result["nextcloud_applications"][app_name]["update_available"]
        ):
            result["updates_available"][app_name] = result["nextcloud_applications"][
                app_name
            ]["version_available"]

    else:
        # flatten the all_present_apps dict into a simple list of app names
        for app_name in [
            s for a in all_present_apps.keys() for s in all_present_apps[a].keys()
        ]:
            result["nextcloud_applications"][app_name] = get_app_infos(
                module, app_name, all_shipped_apps, all_present_apps
            )
            if result["nextcloud_applications"][app_name]["update_available"]:
                result["updates_available"][app_name] = result[
                    "nextcloud_applications"
                ][app_name]["version_available"]

    module.exit_json(changed=False, **result)


if __name__ == "__main__":
    main()
