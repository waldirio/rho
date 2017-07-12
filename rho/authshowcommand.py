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

""" AuthShowCommand is used to display existing authentication credentials
"""

from __future__ import print_function
import os
import sys
from rho.clicommand import CliCommand
from rho.translation import get_translation

_ = get_translation()


class AuthShowCommand(CliCommand):
    """
    This command is for displaying an existing
    auth requested. Passwords are encrypted in
    the console.
    """

    def __init__(self):
        usage = _("usage: %prog auth show [options]")
        shortdesc = _("show auth credential")
        desc = _("show authentication credential")

        CliCommand.__init__(self, "auth show", usage, shortdesc, desc)

        self.parser.add_option("--name", dest="name", metavar="NAME",
                               help=_("auth credential name - REQUIRED"))

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.name:
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        if not os.path.isfile('data/credentials'):

            print(_("No auth credentials found"))

        auth_exists = False

        with open('data/credentials', 'r') as credentials_file:
            lines = credentials_file.readlines()
            for line in lines:
                line_list = line.strip().split(',')
                if line_list[1] == self.options.name:
                    auth_exists = True
                    if line_list[4] and line_list[3]:
                        print(', '.join(line_list[0:3]) +
                              ', ********, ' + line_list[4])
                    elif not line_list[4]:
                        print(', '.join(line_list[0:3]) +
                              ', ********')
                    else:
                        print(', '.join(line_list[0:3]) +
                              ', ' + line_list[4])

        if not auth_exists:

            print(_('Auth "%s" does not exist' % self.options.name))
            sys.exit(1)
