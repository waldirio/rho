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

""" AuthEditCommand is used to edit existing authentication credentials
for system access
"""

from __future__ import print_function
import sys
import os
from getpass import getpass
from rho import utilities
from rho.clicommand import CliCommand
from rho.vault import get_vault
from rho.translation import _


def optional_arg(arg_default):
    """Call back function for arg-parse
    for when arguments are optional
    :param arg_default: The default for the argument
    :returns: Function for handling the argument
    """
    # pylint: disable=unused-argument
    def func(option, opt_str, value, parser):
        """Function for handling CLI option
        :param option: The option
        :param opt_str: The option string
        :param value: The value
        :param parser: The parser for handling the option
        """
        if parser.rargs and \
                not parser.rargs[0].startswith('-'):
            val = parser.rargs[0]
            parser.rargs.pop(0)
        else:
            val = arg_default
        setattr(parser.values, option.dest, val)
    return func


class AuthEditCommand(CliCommand):
    """
    This command is fpr editing the auths already
    existing. The user can edit the username, password
    and ssh key file path.
    """

    def __init__(self):
        usage = _("usage: %prog auth edit [options]")
        shortdesc = _("edits a given auth")
        desc = _("edit a given auth")

        CliCommand.__init__(self, "auth edit", usage, shortdesc, desc)

        self.parser.add_option("--name", dest="name", metavar="NAME",
                               help=_("NAME of the auth - REQUIRED"))
        self.parser.add_option("--username", dest="username",
                               metavar="USERNAME",
                               help=_("user name for authenticating "
                                      "against target machine"
                                      " - REQUIRED"))
        self.parser.add_option("--password", dest="password",
                               action="store_true",
                               help=_("password for authenticating"
                                      " against target machine"))
        self.parser.add_option("--sshkeyfile", dest="filename",
                               metavar="FILENAME", action='callback',
                               callback=optional_arg('empty'),
                               help=_("file containing SSH key"))
        self.parser.add_option("--vault", dest="vaultfile", metavar="VAULT",
                               help=_("file containing vault password for"
                                      " scripting"))

        self.parser.set_defaults(password=False)

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.name:
            self.parser.print_help()
            sys.exit(1)

        if not (self.options.filename or
                self.options.username or
                self.options.password):
            print(_("Should specify an option to update:"
                    " --username, --password or --sshkeyfile"))
            sys.exit(1)

    def _do_command(self):
        vault = get_vault(self.options.vaultfile)
        auth_found = False

        if not os.path.isfile(utilities.CREDENTIALS_PATH):
            print(_("No auth credentials found"))
            sys.exit(1)
        else:
            cred_list = vault.load_as_json(utilities.CREDENTIALS_PATH)

            for cred in cred_list:
                if cred.get('name') == self.options.name:
                    auth_found = True
                    if self.options.username:
                        cred['username'] = self.options.username
                    if self.options.password:
                        cred['password'] = getpass()
                    if self.options.filename:
                        cred['ssh_key_file'] = self.options.filename
                    break
            if not auth_found:
                print(_('Auth "%s" does not exist' % self.options.name))
                sys.exit(1)

            vault.dump_as_json_to_file(cred_list, utilities.CREDENTIALS_PATH)

        print(_("Auth '%s' updated") % self.options.name)
