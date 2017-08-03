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
import json
from rho import utilities
from rho.clicommand import CliCommand
from rho.vault import get_vault
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
        auth_found = False
        if not os.path.isfile(utilities.CREDENTIALS_PATH):
            print(_("No auth credentials found"))
        else:
            cred_list = vault.load_as_json(utilities.CREDENTIALS_PATH)

            for cred in cred_list:
                if cred.get('name') == self.options.name:
                    auth_found = True
                    password = cred.get('password')
                    if not password == '':
                        cred['password'] = '******'

                    data = json.dumps(cred, sort_keys=True, indent=4,
                                      separators=(',', ': '))
                    print(data)
                    break

            if not auth_found:
                print(_('Auth "%s" does not exist' % self.options.name))
                sys.exit(1)
