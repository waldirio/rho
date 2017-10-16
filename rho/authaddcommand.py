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
from rho import utilities
from rho.clicommand import CliCommand
from rho.vault import get_vault
from rho.translation import _


def auth_exists(cred_list, auth_name):
    """Checks whether authentication credential already exists

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


def make_auth_for_options(options):
    """Construct the OrderedDict auth given our options.

    :param options: an options object, from optparse
    :returns: an OrderedDict representing the auth being added
    """

    auth = {'id': str(uuid.uuid4()),
            'name': options.name,
            'username': options.username}

    if options.password:
        print(_('Provide connection password.'))
        pass_prompt = getpass()
        auth['password'] = pass_prompt or None
    else:
        auth['password'] = None

    auth['ssh_key_file'] = options.filename or None

    if options.sudo_password:
        print(_('Provide password for sudo.'))
        sudo_pass_prompt = getpass()
        auth['sudo_password'] = sudo_pass_prompt or None
    else:
        auth['sudo_password'] = None

    return auth


class AuthAddCommand(CliCommand):
    """
    This command is for creating new auths which can be later associated with
    profiles to gather facts.
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
        self.parser.add_option("--sudo-password", dest="sudo_password",
                               action="store_true",
                               help=_("password for running sudo"))
        self.parser.add_option("--vault", dest="vaultfile", metavar="VAULT",
                               help=_("file containing vault password for"
                                      " scripting"))

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not (self.options.name and self.options.username):
            print(_('You must provide a value for "--name" and "--username".'))
            self.parser.print_help()
            sys.exit(1)
        if not self.options.username:
            self.parser.print_help()
            sys.exit(1)

        # need to pass in file or password:
        if not (self.options.filename or
                self.options.password):
            print(_('You must provide either "--password" or a value for '
                    '"--sshkeyfile".'))
            self.parser.print_help()
            sys.exit(1)
        if self.options.filename and self.options.password:
            print(_('You must provide either "--password" or a value for '
                    '"--sshkeyfile". You cannot supply both.'))
            self.parser.print_help()
            sys.exit(1)

        if self.options.filename:
            keyfile_path = os.path.abspath(os.path.normpath(
                os.path.expanduser(os.path.expandvars(self.options.filename))))
            if os.path.isfile(keyfile_path) is False:
                print(_('You must provide a valid file path for'
                        ' "--sshkeyfile", "%s" could not be found.'
                        % keyfile_path))
                self.parser.print_help()
                sys.exit(1)
            else:
                self.options.filename = keyfile_path

    def _do_command(self):
        vault = get_vault(self.options.vaultfile)
        auth_name = self.options.name
        cred_list = []

        if os.path.isfile(utilities.CREDENTIALS_PATH):
            cred_list = vault.load_as_json(utilities.CREDENTIALS_PATH)
            auth_found = auth_exists(cred_list, auth_name)
            if auth_found:
                print(_("Auth with name exists"))
                sys.exit(1)

        cred = make_auth_for_options(self.options)
        _save_cred(vault, cred, cred_list)
        print(_('Auth "%s" was added' % self.options.name))
