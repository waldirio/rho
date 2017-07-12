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

""" ProfileAddCommand is used to create profiles that associate hosts
and authentication credentials
"""

from __future__ import print_function
import csv
import os
import sys
from rho.clicommand import CliCommand
from rho.utilities import multi_arg, _check_range_validity, _read_in_file
from rho.translation import get_translation

_ = get_translation()


class ProfileAddCommand(CliCommand):
    """
    This command is for creating new profiles
    based on hosts and the auths the user wants
    to associate.
    """

    def __init__(self):
        usage = _("usage: %prog profile add [options]")
        shortdesc = _("add a network profile")
        desc = _("add a network profile")

        CliCommand.__init__(self, "profile add", usage, shortdesc, desc)

        self.parser.add_option("--name", dest="name", metavar="NAME",
                               help=_("NAME of the profile - REQUIRED"))
        self.parser.add_option("--hosts", dest="hosts", action="callback",
                               callback=multi_arg,
                               metavar="HOSTS", default=[],
                               help=_("IP range to scan."
                                      " See 'man rho' for supported formats."))
        self.parser.add_option("--sshport", dest="sshport", metavar="SSHPORT",
                               help=_("SSHPORT for connection; default=22"))
        self.parser.add_option("--auth", dest="auth", metavar="AUTH",
                               action="callback", callback=multi_arg,
                               default=[], help=_("auth class to "
                                                  "associate with profile"))

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.hosts:
            self.parser.print_help()
            sys.exit(1)

        if not self.options.auth:
            self.parser.print_help()
            sys.exit(1)

        if not self.options.name:
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        # pylint: disable=too-many-locals
        profile_exists = False

        hosts_list = self.options.hosts
        ssh_port = 22
        if hasattr(self.options, 'sshport') \
           and self.options.sshport is not None:
            ssh_port = self.options.sshport

        if os.path.isfile('data/profiles'):
            with open('data/profiles', 'r') as profiles_file:
                lines = profiles_file.readlines()
                for line in lines:
                    line_list = line.strip().split(',____,')
                    if line_list[0] == self.options.name:
                        profile_exists = True

            if profile_exists:

                print(_("Profile '%s' already exists.") % self.options.name)
                sys.exit(1)

        range_list = hosts_list

        # pylint: disable=len-as-condition
        if len(hosts_list) > 0 and os.path.isfile(hosts_list[0]):
            range_list = _read_in_file(hosts_list[0])

        _check_range_validity(range_list)

        creds = []
        cred_names = []
        for auth in self.options.auth:
            for auth_item in auth.strip().split(","):
                valid = False
                if not os.path.isfile('data/credentials'):

                    print(_('No credentials exist yet.'))
                    sys.exit(1)

                with open('data/credentials', 'r') as credentials_file:
                    lines = credentials_file.readlines()
                    for line in lines:
                        line_list = line.strip().split(',')
                        if line_list[1] == auth_item:
                            valid = True
                            # add the uuids of credentials
                            creds.append(line_list[0])
                            cred_names.append(line_list[1])

                if not valid:
                    print("Auth " + auth_item + " does not exist")
                    sys.exit(1)

        with open('data/profiles', 'a') as profiles_file:
            profile_list = [self.options.name] + ['____'] + range_list \
                + ['____'] + [str(ssh_port)] + ['____'] + creds + ['____'] + \
                cred_names
            csv_w = csv.writer(profiles_file)
            csv_w.writerow(profile_list)
