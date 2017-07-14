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

""" ProfileListCommand is used to list existing profiles that associate hosts
and authentication credentials
"""

from __future__ import print_function
import os
import sys
import json
from rho.clicommand import CliCommand
from rho.vault import get_vault
from rho.translation import get_translation

_ = get_translation()


class ProfileListCommand(CliCommand):
    """
    This command is for displaying all existing profiles
    the user has added previously.
    """

    def __init__(self):
        usage = _("usage: %prog profile list [options]")
        shortdesc = _("list the network profiles")
        desc = _("list the network profiles")

        CliCommand.__init__(self, "profile list", usage, shortdesc, desc)
        self.parser.add_option("--vault", dest="vaultfile", metavar="VAULT",
                               help=_("file containing vault password for"
                                      " scripting"))

    def _do_command(self):
        vault = get_vault(self.options.vaultfile)
        profiles_path = 'data/profiles'

        if not os.path.isfile(profiles_path):
            print(_('No profiles exist yet.'))
            sys.exit(1)

        profiles_list = vault.load_as_json(profiles_path)
        data = json.dumps(profiles_list, sort_keys=True, indent=4,
                          separators=(',', ': '))
        print(data)
