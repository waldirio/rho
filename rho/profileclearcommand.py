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
from rho.translation import _


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
            self.parser.print_help()
            sys.exit(1)

        if self.options.name and self.options.all:
            self.parser.print_help()
            sys.exit(1)

    # pylint: disable=too-many-branches
    def _do_command(self):
        profiles_list = []

        if self.options.name:
            vault = get_vault(self.options.vaultfile)
            profile = self.options.name
            profiles_list = vault.load_as_json(utilities.PROFILES_PATH)
            profile_found = False

            for index, curr_profile in enumerate(profiles_list):
                if curr_profile.get('name') == profile:
                    del profiles_list[index]
                    profile_found = True
                    break

            if not profile_found:
                print(_("No such profile: '%s'") % profile)
                sys.exit(1)

            vault.dump_as_json_to_file(profiles_list, utilities.PROFILES_PATH)

            # removes inventory associated with the profile
            if os.path.isfile('data/' + profile + "_hosts"):
                os.remove('data/' + profile + "_hosts")

            profile_mapping = 'data/' + profile + '_host_auth_mapping'

            # when a profile is removed, it 'archives' the host auth mapping
            # by renaming it '(DELETED PROFILE)<profile_name>_host_auth_mapping
            # for identification by the user. The time stamps in mapping files
            # help in identifying the various forms and times in which the said
            # profile existed.
            if os.path.isfile(profile_mapping):
                os.rename(profile_mapping,
                          'data/(DELETED PROFILE)' +
                          profile + '_host_auth_mapping')

        # removes all inventories ever.
        elif self.options.all:
            if not os.path.isfile(utilities.PROFILES_PATH):
                print(_("All network profiles removed"))
            else:
                os.remove(utilities.PROFILES_PATH)
                for file_list in glob.glob("data/*_hosts"):
                    os.remove(file_list)
                    profile = file_list.strip('_hosts')
                    profile_mapping = 'data/' + profile + '_host_auth_mapping'
                    if os.path.isfile(profile_mapping):
                        os.rename(profile_mapping,
                                  'data/(DELETED PROFILE)' +
                                  profile + '_host_auth_mapping')

                print(_("All network profiles removed"))
