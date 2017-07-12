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
from rho.clicommand import CliCommand
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

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.name:
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        profile_exists = False
        with open('data/profiles', 'r') as profiles_file:
            lines = profiles_file.readlines()
            for line in lines:
                line_list = line.strip().split(',____,')
                if line_list[0] == self.options.name:
                    profile_exists = True
                    profile_str = ', '.join(line_list[0:3] + [line_list[3]])
                    print(profile_str)

        if not profile_exists:
            print(_("Profile '%s' does not exist.") % self.options.name)
            sys.exit(1)
