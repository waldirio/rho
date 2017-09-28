#
# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

# pylint: disable=too-few-public-methods

""" ProfileClearCommand is used to clear profiles that already existing
either individually or all profiles
"""

from __future__ import print_function
import os
import sys
import glob
from rho import utilities
from rho.clicommand import CliCommand
from rho.vault import get_vault
from rho.utilities import (
    PROFILE_HOSTS_SUFIX,
    PROFILE_HOST_AUTH_MAPPING_SUFFIX,
    get_config_path,
)
from rho.translation import _


def _backup_host_auth_mapping(profile):
    """Backup the ``profile`` host auth mapping file.

    When a profile is removed, it 'archives' the host auth mapping by
    renaming it to '(DELETED PROFILE)<profile_name>_host_auth_mapping
    for identification by the user. The time stamps in mapping files
    help in identifying the various forms and times in which the said
    profile existed.
    """
    mapping_name = profile + PROFILE_HOST_AUTH_MAPPING_SUFFIX
    mapping_path = get_config_path(mapping_name)
    if os.path.isfile(mapping_path):
        renamed_mapping_name = '(DELETED PROFILE)' + mapping_name
        renamed_mapping_path = get_config_path(renamed_mapping_name)
        os.rename(mapping_path, renamed_mapping_path)


class ProfileClearCommand(CliCommand):
    """
    This command is for removing profiles.
    A user can remove an existing profile by
    passing in the name or ask to delete all
    profiles.
    """

    def __init__(self):
        usage = _("usage: %prog profile clear [--name | --all] [options]")
        shortdesc = _("removes 1 or all profiles from list")
        desc = _("removes profiles")

        CliCommand.__init__(self, "profile clear", usage, shortdesc, desc)

        self.parser.add_option("--name", dest="name", metavar="NAME",
                               help=_("NAME of the profile to be removed"))
        self.parser.add_option("--all", dest="all", action="store_true",
                               help=_("remove ALL profiles"))

        self.parser.set_defaults(all=False)
        self.parser.add_option("--vault", dest="vaultfile", metavar="VAULT",
                               help=_("file containing vault password for"
                                      " scripting"))

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.name and not self.options.all:
            print(_('You must provide either "--all" or a value for '
                    '"--name".'))
            self.parser.print_help()
            sys.exit(1)

        if self.options.name and self.options.all:
            print(_('You must provide either "--all" or a value for '
                    '"--name". You cannot supply both.'))
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        if not os.path.isfile(utilities.PROFILES_PATH):
            print(_("All network profiles removed"))
            return

        if self.options.name:
            vault = get_vault(self.options.vaultfile)
            profile = self.options.name
            profiles_list = vault.load_as_json(utilities.PROFILES_PATH)
            profile_found = False

            for index, curr_profile in enumerate(profiles_list):
                if curr_profile.get('name') == profile:
                    del profiles_list[index]
                    print(_('Profile "%s" was removed' % profile))
                    profile_found = True
                    break

            if not profile_found:
                print(_("No such profile: '%s'") % profile)
                sys.exit(1)

            vault.dump_as_json_to_file(profiles_list, utilities.PROFILES_PATH)

            # removes inventory associated with the profile
            profile_hosts_path = get_config_path(profile + PROFILE_HOSTS_SUFIX)
            if os.path.isfile(profile_hosts_path):
                os.remove(profile_hosts_path)
            _backup_host_auth_mapping(profile)

        # removes all inventories ever.
        elif self.options.all:
            os.remove(utilities.PROFILES_PATH)
            wildcard_hosts_path = get_config_path('*' + PROFILE_HOSTS_SUFIX)
            for file_list in glob.glob(wildcard_hosts_path):
                os.remove(file_list)
                file_list = os.path.basename(file_list)
                profile = file_list[:file_list.rfind(PROFILE_HOSTS_SUFIX)]
                _backup_host_auth_mapping(profile)
            print(_("All network profiles removed"))
