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
from rho import utilities
from rho.clicommand import CliCommand
from rho.vault import get_vault
from rho.utilities import multi_arg, _check_range_validity, _read_in_file
from rho.translation import _


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
        self.parser.add_option("--vault", dest="vaultfile", metavar="VAULT",
                               help=_("file containing vault password for"
                                      " scripting"))

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

        if hasattr(self.options, 'sshport') \
           and self.options.sshport is not None:
            ssh_port = self.options.sshport
            try:
                ssh_port = utilities.validate_port(ssh_port)
                self.options.sshport = ssh_port
            except ValueError as port_error:
                print(str(port_error))
                self.parser.print_help()
                sys.exit(1)

    def _do_command(self):
        # pylint: disable=too-many-locals, too-many-branches
        # pylint: disable=too-many-statements, too-many-nested-blocks
        vault = get_vault(self.options.vaultfile)
        cred_list = []
        profiles_list = []
        range_list = []
        profile_found = False
        auth_found = False

        if not os.path.isfile(utilities.CREDENTIALS_PATH):
            print(_('No credentials exist yet.'))
            sys.exit(1)

        if not os.path.isfile(utilities.PROFILES_PATH):
            print(_('No profiles exist yet.'))
            sys.exit(1)

        cred_list = vault.load_as_json(utilities.CREDENTIALS_PATH)
        profiles_list = vault.load_as_json(utilities.PROFILES_PATH)

        if self.options.hosts:
            hosts_list = self.options.hosts
            range_list = hosts_list
            if os.path.isfile(hosts_list[0]):
                range_list = _read_in_file(hosts_list[0])

            # makes sure the hosts passed in are in a format Ansible
            # understands.
            _check_range_validity(range_list)

        for curr_profile in profiles_list:
            if curr_profile.get('name') == self.options.name:
                profile_found = True
                if self.options.hosts:
                    curr_profile['hosts'] = range_list

                if self.options.sshport:
                    curr_profile['ssh_port'] = str(self.options.sshport)

                if self.options.auth:
                    new_auths = []
                    auth_list = self.options.auth
                    for auth in auth_list:
                        for cred in cred_list:
                            if auth == cred.get('name'):
                                auth_found = True
                                store_cred = {'id': cred.get('id'),
                                              'name': cred.get('name')}
                                new_auths.append(store_cred)
                    if not auth_found:
                        print(_("Auths do not exist."))
                        sys.exit(1)

                    curr_profile['auth'] = new_auths
                break

        if not profile_found:
            print(_("Profile '%s' does not exist.") % self.options.name)
            sys.exit(1)

        vault.dump_as_json_to_file(profiles_list, utilities.PROFILES_PATH)
        print(_("Profile '%s' edited" % self.options.name))
