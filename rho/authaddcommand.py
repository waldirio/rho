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
import csv
import os
import sys
import uuid
from getpass import getpass
from collections import OrderedDict
from rho.clicommand import CliCommand
from rho.translation import get_translation

_ = get_translation()


# Write new credentials in the related file.
def _save_cred(cred):
    append_or_write = 'a'
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.isfile('data/credentials'):
        append_or_write = 'w'
    with open('data/credentials', append_or_write) as cred_file:
        dict_writer = csv.DictWriter(cred_file, cred.keys())
        dict_writer.writerow(cred)


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
        cred = {}
        ssh_file = 'empty'
        pass_to_store = ''

        cred_keys = ["id", "name", "username", "password", "ssh_key_file"]

        if os.path.isfile('data/credentials'):
            with open('data/credentials', 'r') as credentials_file:
                dict_reader = csv.DictReader(credentials_file, cred_keys)
                for line in dict_reader:
                    if line['name'] == self.options.name:

                        print(_("Auth with name exists"))
                        credentials_file.close()
                        sys.exit(1)

        if self.options.password:
            pass_prompt = getpass()
            pass_to_store = 'empty' if pass_prompt == '' else pass_prompt

        if self.options.filename:
            # using sshkey
            ssh_file = self.options.filename

            cred = OrderedDict([("id",
                                 uuid.uuid4()),
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
                                 uuid.uuid4()),
                                ("name",
                                 self.options.name),
                                ("username",
                                 self.options.username),
                                ("password",
                                 pass_to_store),
                                ("ssh_key_file",
                                 ssh_file)])

        _save_cred(cred)
