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

""" ProfileShowCommand is used to show a specific profiles that associate hosts
and authentication credentials
"""

from __future__ import print_function
import sys
import os
import json
from rho import utilities
from rho.clicommand import CliCommand
from rho.vault import get_vault
from rho.translation import get_translation

_ = get_translation()


class ProfileShowCommand(CliCommand):
    """
    This command is for displaying a particular profile
    the user has added previously if it has not been deleted
    already.
    """

    def __init__(self):
        usage = _("usage: %prog profile show [options]")
        shortdesc = _("show a network profile")
        desc = _("show a network profile")

        CliCommand.__init__(self, "profile show", usage, shortdesc, desc)

        self.parser.add_option("--name", dest="name", metavar="NAME",
                               help=_("profile name - REQUIRED"))

        self.parser.add_option("--vault", dest="vaultfile", metavar="VAULT",
                               help=_("file containing vault password for"
                                      " scripting"))

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.name:
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        vault = get_vault(self.options.vaultfile)

        if not os.path.isfile(utilities.PROFILES_PATH):
            print(_('No profiles exist yet.'))
            sys.exit(1)

        profile_found = False
        profiles_list = vault.load_as_json(utilities.PROFILES_PATH)
        for profile in profiles_list:
            if self.options.name == profile.get('name'):
                profile_found = True
                data = json.dumps(profile, sort_keys=True, indent=4,
                                  separators=(',', ': '))
                print(data)
                break

        if not profile_found:
            print(_("Profile '%s' does not exist.") % self.options.name)
            sys.exit(1)
