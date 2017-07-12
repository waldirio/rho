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

""" AuthListCommand is used to list authentication credentials
for system access
"""

from __future__ import print_function
import os
import sys
from rho.clicommand import CliCommand
from rho.translation import get_translation

_ = get_translation()


class AuthListCommand(CliCommand):
    """
    This command is for displaying all existing
    auths. Passwords are encrypted in the console.
    """

    def __init__(self):
        usage = _("usage: %prog auth list [options]")
        shortdesc = _("list auth credentials")
        desc = _("list authentication credentials")

        CliCommand.__init__(self, "auth list", usage, shortdesc, desc)

    def _do_command(self):
        if not os.path.isfile('data/credentials'):

            print(_('No credentials exist yet.'))
            sys.exit(1)

        with open('data/credentials', 'r') as credentials_file:
            lines = credentials_file.readlines()
            for line in lines:
                line_list = line.strip().split(',')
                if line_list[3] and line_list[4]:
                    print(', '.join(line_list[0:3]) +
                          ', ********, ' + line_list[4])
                elif not line_list[4]:
                    print(', '.join(line_list[0:3]) +
                          ', ********')
                else:
                    print(', '.join(line_list[0:3]) +
                          ', ' + line_list[4])
