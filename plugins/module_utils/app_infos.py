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

from ansible_collections.nextcloud.admin.plugins.module_utils.occ import run_occ


def check_app_update(module, app_name):
    _check_app_update = run_occ(module, ["app:update", "--showonly", app_name])[1]
    if _check_app_update != "":
        app_update = True
        app_update_version_available = _check_app_update.split()[-1]
    else:
        app_update = False
        app_update_version_available = None

    return app_update, app_update_version_available


def get_app_infos(module, app_name, all_shipped_apps, all_present_apps):
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
