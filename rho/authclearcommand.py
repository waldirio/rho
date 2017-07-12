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

""" AuthClearCommand is for removing a specific or all
existing authentication credentials.
"""

from __future__ import print_function
import os
import sys
from rho.clicommand import CliCommand
from rho.translation import get_translation

_ = get_translation()


class AuthClearCommand(CliCommand):
    """
    This command is for removing a specific
    or all existing auths.
    """

    def __init__(self):
        usage = _("usage: %prog auth clear")
        shortdesc = _("clears out the credentials")
        desc = _("clears out the crendentials")

        CliCommand.__init__(self, "auth clear", usage, shortdesc, desc)

        self.parser.add_option("--name", dest="name", metavar="NAME",
                               help=_("NAME of the auth "
                                      "credential to be removed"))
        self.parser.add_option("--all", dest="all", action="store_true",
                               help=_("remove ALL auth credentials"))

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.name and not self.options.all:
            self.parser.print_help()
            sys.exit(1)

        if self.options.name and self.options.all:
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        if self.options.name:
            with open('data/credentials', 'r') as creds_read:
                with open('data/cred-temp', 'w') as temp_creds_write:
                    for line in creds_read:
                        temp_creds_write.write(line)

            with open('data/cred-temp', 'r') as temp_creds_read:
                with open('data/credentials', 'w') as creds_write:
                    for line in temp_creds_read:
                        if not line.strip().split(',')[1] \
                                == self.options.name:
                            creds_write.write(line)

            os.remove('data/cred-temp')

        elif self.options.all:
            if os.path.isfile('data/credentials'):
                os.remove('data/credentials')
            if os.path.isfile('data/cred-temp'):
                os.remove('data/cred-temp')

            print(_("All authorization credentials removed"))
