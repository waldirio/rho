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

""" AuthAddCommand is used to add authentication credentials
for system access
"""

from __future__ import print_function
import os
import sys
import uuid
from getpass import getpass
from collections import OrderedDict
from rho import utilities
from rho.clicommand import CliCommand
from rho.vault import get_vault
from rho.translation import _


def auth_exists(cred_list, auth_name):
    """ Checks whether authentication credential already exists
    :param cred_list: A list of credential dictionaries
    :param auth_name: Name of credential to check for existence
    :returns: True if auth_name exists, False otherwise
    """
    auth_found = False
    for cred in cred_list:
        if cred.get('name') == auth_name:
            auth_found = True
            break
    return auth_found


def _save_cred(vault, new_cred, cred_list):
    """ Write new credentials in the related file
    :param vault: Vault object for writing encrypted data
    :param new_cred: New credential to be added to the credentials file
    :param cred_list: A list of existing credential dictionaries from the
    credential file
    """

    utilities.ensure_config_dir_exists()
    cred_list.append(new_cred)
    vault.dump_as_json_to_file(cred_list, utilities.CREDENTIALS_PATH)


class AuthAddCommand(CliCommand):
    """
    This command is for creating new auths
    which can be later associated with profiles
    to gather facts.
    """

    def __init__(self):
        usage = _("usage: %prog auth add [options]")
        shortdesc = _("add auth credentials to config")
        desc = _("adds the authorization credentials to the config")

        CliCommand.__init__(self, "auth add", usage, shortdesc, desc)

        self.parser.add_option("--name", dest="name", metavar="NAME",
                               help=_("auth credential name - REQUIRED"))
        self.parser.add_option("--sshkeyfile", dest="filename",
                               metavar="FILENAME",
                               help=_("file containing SSH key"))
        self.parser.add_option("--username", dest="username",
                               metavar="USERNAME",
                               help=_("user name for authenticating"
                                      " against target machine - REQUIRED"))
        self.parser.add_option("--password", dest="password",
                               action="store_true",
                               help=_("password for authenticating against"
                                      " target machine"))
        self.parser.add_option("--vault", dest="vaultfile", metavar="VAULT",
                               help=_("file containing vault password for"
                                      " scripting"))

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.name:
            self.parser.print_help()
            sys.exit(1)

        # need to pass in file or username:
        if not self.options.filename \
                and not (self.options.username and
                         self.options.password):
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        vault = get_vault(self.options.vaultfile)
        cred = OrderedDict()
        ssh_file = None
        pass_to_store = None
        auth_name = self.options.name
        cred_list = []

        if os.path.isfile(utilities.CREDENTIALS_PATH):
            cred_list = vault.load_as_json(utilities.CREDENTIALS_PATH)
            auth_found = auth_exists(cred_list, auth_name)
            if auth_found:
                print(_("Auth with name exists"))
                sys.exit(1)

        if self.options.password:
            pass_prompt = getpass()
            pass_to_store = None if pass_prompt == '' else pass_prompt

        if self.options.filename:
            # using sshkey
            ssh_file = self.options.filename

            cred = OrderedDict([("id",
                                 str(uuid.uuid4())),
                                ("name",
                                 self.options.name),
                                ("username",
                                 self.options.username),
                                ("password",
                                 pass_to_store),
                                ("ssh_key_file",
                                 ssh_file)])

        elif self.options.username and self.options.password:
            cred = OrderedDict([("id",
                                 str(uuid.uuid4())),
                                ("name",
                                 self.options.name),
                                ("username",
                                 self.options.username),
                                ("password",
                                 pass_to_store),
                                ("ssh_key_file",
                                 ssh_file)])

        _save_cred(vault, cred, cred_list)
