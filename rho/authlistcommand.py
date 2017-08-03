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
import json
from rho import utilities
from rho.clicommand import CliCommand
from rho.vault import get_vault
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
        self.parser.add_option("--vault", dest="vaultfile", metavar="VAULT",
                               help=_("file containing vault password for"
                                      " scripting"))

    def _do_command(self):
        vault = get_vault(self.options.vaultfile)

        if not os.path.isfile(utilities.CREDENTIALS_PATH):
            print(_('No credentials exist yet.'))
            sys.exit(1)

        cred_list = vault.load_as_json(utilities.CREDENTIALS_PATH)

        for cred in cred_list:
            if not cred.get('password') == '':
                cred['password'] = '**********'
        data = json.dumps(cred_list, sort_keys=True, indent=4,
                          separators=(',', ': '))
        print(data)
