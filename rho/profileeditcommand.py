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

""" ProfileEditCommand is used to edit existing profiles that associate hosts
and authentication credentials
"""

from __future__ import print_function
import os
import sys
from copy import copy
from rho.clicommand import CliCommand
from rho.utilities import multi_arg, _check_range_validity, _read_in_file
from rho.translation import get_translation

_ = get_translation()


class ProfileEditCommand(CliCommand):
    """
    This command is for editing an existing profile.
    The name of the profile has to be supplied. The
    hosts, auths attached or both can be changed.
    """

    def __init__(self):
        usage = _("usage: %prog profile edit [options]")
        shortdesc = _("edits a given profile")
        desc = _("edit a given profile")

        CliCommand.__init__(self, "profile edit", usage, shortdesc, desc)

        self.parser.add_option("--name", dest="name", metavar="NAME",
                               help=_("NAME of the profile - REQUIRED"))
        self.parser.add_option("--hosts", dest="hosts", action="callback",
                               callback=multi_arg,
                               metavar="RANGE", default=[],
                               help=_("IP range to scan. See "
                                      "'man rho' for supported formats."))
        self.parser.add_option("--sshport", dest="sshport", metavar="SSHPORT",
                               help=_("SSHPORT for connection; default=22"))
        # can only replace auth
        self.parser.add_option("--auth", dest="auth", metavar="AUTH",
                               action="callback", callback=multi_arg,
                               default=[], help=_("auth"
                                                  " class"
                                                  " to associate"
                                                  " with profile"))

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.name:
            self.parser.print_help()
            sys.exit(1)

        if not self.options.hosts and not self.options.auth \
           and not self.options.sshport:
            print(_("Specify either hosts, sshport, or auths to update."))
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        # pylint: disable=too-many-locals, too-many-branches
        # pylint: disable=too-many-statements, too-many-nested-blocks
        profile_exists = False
        auth_exists = False

        range_list = []

        if self.options.hosts:
            hosts_list = self.options.hosts

            range_list = hosts_list
            # pylint: disable=len-as-condition
            if len(hosts_list) > 0 and os.path.isfile(hosts_list[0]):
                range_list = _read_in_file(hosts_list[0])

        # makes sure the hosts passed in are in a format Ansible
        # understands.

            _check_range_validity(range_list)
        if not os.path.isfile('data/profiles'):
            print(_('No profiles exist yet.'))
            sys.exit(1)

        if not os.path.isfile('data/credentials'):
            print(_('No credentials exist yet.'))
            sys.exit(1)

        with open('data/profiles', 'r') as profiles_file:
            lines = profiles_file.readlines()

        with open('data/credentials', 'r') as credentials_file:
            auth_lines = credentials_file.readlines()

        with open('data/profiles', 'w') as profiles_file:
            for line in lines:
                range_change = False
                auth_change = False
                line_list = line.strip().split(',____,')
                old_line_list = copy(line_list)

                if line_list[0] \
                        == self.options.name:
                    range_change = True
                    string_id_one = ''
                    profile_exists = True

                    if self.options.hosts:

                        for range_item in range_list:
                            string_id_one += ', ' + range_item

                        string_id_one = string_id_one.strip(',')
                        line_list[1] = string_id_one.rstrip(',').rstrip(' ')

                    if self.options.sshport:
                        line_list[2] = str(self.options.sshport)

                    if self.options.auth:
                        string_id_two = ''
                        string_id_three = ''
                        auth_list = self.options.auth
                        for auth in auth_list:
                            for auth_line in auth_lines:
                                line_auth_list = auth_line.strip().split(',')
                                if line_auth_list[1] == auth:
                                    auth_change = True
                                    auth_exists = True
                                    string_id_two += line_auth_list[0] + ', '
                                    string_id_three += auth + ', '

                        if auth_change:
                            line_list[3] = \
                                string_id_two.rstrip(',').rstrip(' ')
                            line_list[4] = \
                                string_id_three.rstrip(',').rstrip(' ')

                if range_change or auth_change:
                    line_string = ',____,'.join(line_list)
                else:
                    line_string = ',____,'.join(old_line_list)

                profiles_file.write(line_string + '\n')

        if not profile_exists:
            print(_("Profile '%s' does not exist.") % self.options.name)
            sys.exit(1)

        if not auth_exists:
            print(_("Auths do not exist."))
            sys.exit(1)

        print(_("Profile '%s' edited" % self.options.name))
