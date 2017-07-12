#
# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

# pylint: disable=too-few-public-methods, too-many-lines

""" Rho CLI Commands """

from __future__ import print_function
import os
import sys
import re
import time
import json
import subprocess as sp
from collections import defaultdict
from copy import copy
from rho.clicommand import CliCommand
from rho.utilities import multi_arg, _read_in_file
from rho.translation import get_translation

_ = get_translation()


# Read ssh key from file
def _read_key_file(filename):
    keyfile = open(os.path.expanduser(
        os.path.expandvars(filename)), "r")
    sshkey = keyfile.read()
    keyfile.close()
    return sshkey


# Creates the inventory for pinging all hosts and records
# successful auths and the hosts they worked on
# pylint: disable=too-many-statements
def _create_ping_inventory(profile_ranges, profile_port, profile_auth_list,
                           forks):
    # pylint: disable=too-many-locals
    success_auths = set()
    success_hosts = set()
    success_port_map = defaultdict()
    success_map = defaultdict(list)
    best_map = defaultdict(list)
    mapped_hosts = set()

    string_to_write = "[all]\n"
    for profile_range in profile_ranges:
        # pylint: disable=anomalous-backslash-in-string
        reg = "[0-9]*.[0-9]*.[0-9]*.\[[0-9]*:[0-9]*\]"
        profile_range = profile_range.strip(',').strip()
        if not re.match(reg, profile_range):
            string_to_write += profile_range + \
                " ansible_host=" + profile_range + " ansible_port=" + \
                str(profile_port) + "\n"
        else:
            string_to_write += profile_range + "\n"

    string_to_write += '\n'

    string_header = copy(string_to_write)

    for auth_item in profile_auth_list:
        ping_inventory = open('data/ping-inventory', 'w')
        string_to_write = \
            string_header + \
            "[all:vars]\n" + \
            "ansible_user=" + \
            auth_item[2]

        auth_pass_or_key = ''

        if (not auth_item[3] == '') and auth_item[3]:
            auth_pass_or_key = '\nansible_ssh_pass=' + auth_item[3]
            if (not auth_item[4] == '') and auth_item[4]:
                auth_pass_or_key += "\nansible_ssh_private_key_file=" + \
                    auth_item[4]
        elif auth_item[3] == '':
            auth_pass_or_key = '\n'
            if (not auth_item[4] == '') and auth_item[4]:
                auth_pass_or_key += "ansible_ssh_private_key_file=" + \
                    auth_item[4]

        string_to_write += auth_pass_or_key

        ping_inventory.write(string_to_write)

        ping_inventory.close()

        cmd_string = 'ansible all -m' \
                     ' ping  -i data/ping-inventory -f ' + forks

        my_env = os.environ.copy()
        my_env["ANSIBLE_HOST_KEY_CHECKING"] = "False"

        process = sp.Popen(cmd_string,
                           shell=True,
                           env=my_env,
                           stdin=sp.PIPE,
                           stdout=sp.PIPE)

        out = process.communicate()[0]

        with open('data/ping_log', 'w') as ping_log:
            ping_log.write(out)

        out = out.split('\n')

        for line, _ in enumerate(out):
            if 'pong' in out[line]:
                tup_auth_item = tuple(auth_item)
                success_auths.add(tup_auth_item)
                host_line = out[line - 2]
                host_ip = host_line.split('|')[0].strip()
                success_hosts.add(host_ip)
                if host_ip not in mapped_hosts:
                    best_map[tup_auth_item].append(host_ip)
                    mapped_hosts.add(host_ip)
                success_map[host_ip].append(tup_auth_item)
                success_port_map[host_ip] = profile_port

    success_auths = list(success_auths)
    success_hosts = list(success_hosts)

    return success_auths, success_hosts, best_map, success_map, \
        success_port_map


# Helper function to create a file to store the mapping
# between hosts and ALL the auths that were ever succesful
# with them arranged according to profile and date of scan.
def _create_hosts_auths_file(success_map, profile):
    with open('data/' + profile + '_host_auth_mapping', 'a') as host_auth_file:
        string_to_write = time.strftime("%c") + '\n-' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---\n'
        for host, line in success_map.iteritems():
            string_to_write += host + '\n----------------------\n'
            for auth in line:
                string_to_write += ', '.join(auth[1:3]) + ', ********, ' +\
                    auth[4]
            string_to_write += '\n\n'
        string_to_write += '\n*******************************' \
                           '*********************************' \
                           '**************\n\n'
        host_auth_file.write(string_to_write)


# Creates the filtered main inventory on which the custom
# modules to collect facts are run. This inventory can be
# used multiple times later after a profile has first been
# processed and the valid mapping as been figured out by
# pinging.
def _create_main_inventory(success_hosts, success_port_map, best_map, profile):
    string_to_write = "[alpha]\n"

    for host in success_hosts:
        string_to_write += host + ' ansible_host=' + host + \
            ' ansible_port=' + success_port_map[host] + '\n'

    with open('data/' + profile + '_hosts', 'w') as profile_hosts:
        for auth in best_map.keys():
            auth_name = auth[1]
            auth_user = auth[2]
            auth_pass = auth[3]
            auth_key = auth[4]

            string_to_write += '\n[' \
                               + auth_name \
                               + ']\n'

            auth_pass_or_key = ''

            for host in best_map[auth]:
                string_to_write += host + ' ansible_host=' \
                    + host + " ansible_user=" + auth_user
                if (not auth_pass == '') and auth_pass:
                    auth_pass_or_key = ' ansible_ssh_pass=' + auth_pass
                    if (not auth_key == '') and auth_key:
                        auth_pass_or_key += " ansible_ssh_private_key_" \
                                            "file=" + auth_key + '\n'
                elif auth_pass == '':
                    if (not auth_key == '') and auth_key:
                        auth_pass_or_key = " ansible_ssh_private_key" \
                                           "_file=" + auth_key + '\n'
                    else:
                        auth_pass_or_key = '\n'

                string_to_write += auth_pass_or_key

        profile_hosts.write(string_to_write)


class ScanCommand(CliCommand):
    """ The command that performs the scanning and collection of
    facts by making the playbook, inventory and running ansible.
    """

    def __init__(self):
        usage = _("usage: %prog scan [options] PROFILE")
        shortdesc = _("scan given host profile")
        desc = _("scans the host profile")

        CliCommand.__init__(self, "scan", usage, shortdesc, desc)

        self.parser.add_option("--reset", dest="reset", action="store_true",
                               metavar="RESET", default=False,
                               help=_("Use if profiles/auths have been "
                                      "changed"))

        self.parser.add_option("--profile", dest="profile", metavar="PROFILE",
                               help=_("NAME of the profile - REQUIRED"))

        self.parser.add_option("--reportfile", dest="report_path",
                               metavar="REPORTFILE",
                               help=_("Report file path - REQUIRED"))

        self.parser.add_option("--facts", dest="facts", metavar="FACTS",
                               action="callback", callback=multi_arg,
                               default=[], help=_("'default' or list " +
                                                  " - REQUIRED"))

        self.parser.add_option("--ansible_forks", dest="ansible_forks",
                               metavar="FORKS",
                               help=_("number of ansible forks"))

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.profile:
            print(_("No profile specified."))
            self.parser.print_help()
            sys.exit(1)

        if not self.options.facts:
            print(_("No facts specified."))
            self.parser.print_help()
            sys.exit(1)

        if not self.options.report_path:
            print(_("No report location specified."))
            self.parser.print_help()
            sys.exit(1)

        if self.options.ansible_forks:
            try:
                if int(self.options.ansible_forks) <= 0:
                    print(_("ansible_forks can only be a positive integer."))
                    self.parser.print_help()
                    sys.exit(1)
            except ValueError:
                print(_("ansible_forks can only be a positive integer."))
                self.parser.print_help()
                sys.exit(1)

    def _do_command(self):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        profile = self.options.profile

        facts = self.options.facts

        forks = self.options.ansible_forks \
            if self.options.ansible_forks else '50'

        report_path = os.path.abspath(os.path.normpath(
            self.options.report_path))

        profile_exists = False

        profile_auth_list = []
        profile_ranges = []

        # Checks if profile exists and stores information
        # about that profile for later use.
        if not os.path.isfile('data/profiles'):
            print(_('No profiles exist yet.'))
            sys.exit(1)

        with open('data/profiles', 'r') as profiles_file:
            lines = profiles_file.readlines()
            for line in lines:
                line_list = line.split(',____,')
                if line_list[0] == profile:
                    profile_exists = True
                    profile_ranges = line_list[1].strip().strip(',').split(',')
                    profile_port = line_list[2].strip().strip(',').split(',')
                    profile_auths = line_list[3].strip().strip(',').split(',')
                    for auth in profile_auths:
                        auth = auth.strip(',').strip()
                        if not os.path.isfile('data/credentials'):
                            print(_('No authorization credentials exist yet.'))
                            sys.exit(1)
                        with open('data/credentials', 'r') as credentials_file:
                            auth_lines = credentials_file.readlines()
                            for auth_line in auth_lines:
                                auth_line_list = auth_line.split(',')
                                if auth_line_list[0] == auth:
                                    profile_auth_list.append(auth_line_list)
                    break

        if not profile_exists:
            print(_("Invalid profile. Create profile first"))
            sys.exit(1)

        # reset is used when the profile has just been created
        # or freshly updated.

        if self.options.reset:

            success_auths, success_hosts, best_map, success_map, \
                success_port_map = _create_ping_inventory(profile_ranges,
                                                          profile_port[0],
                                                          profile_auth_list,
                                                          forks)

            if not len(success_auths):  # pylint: disable=len-as-condition
                print(_('All auths are invalid for this profile'))
                sys.exit(1)

            _create_hosts_auths_file(success_map, profile)

            _create_main_inventory(success_hosts, success_port_map, best_map,
                                   profile)

        elif not os.path.isfile('data/' + profile + '_hosts'):
            print("Profile '" + profile + "' has not been processed. " +
                  "Please use --reset with profile first.")
            sys.exit(1)

        if facts == ['default']:
            facts_to_collect = 'default'
        elif os.path.isfile(facts[0]):
            facts_to_collect = _read_in_file(facts[0])
        else:
            assert isinstance(facts, list)
            facts_to_collect = facts

        ansible_vars = {'facts_to_collect': facts_to_collect,
                        'report_path': report_path}

        cmd_string = ('ansible-playbook rho_playbook.yml '
                      '-i data/{profile}_hosts -v -f {forks} '
                      '--extra-vars \'{vars}\'').format(
                          profile=profile,
                          forks=forks,
                          vars=json.dumps(ansible_vars))

        # process finally runs ansible on the
        # playbook and inventories thus created.

        print('Running:', cmd_string)

        process = sp.Popen(cmd_string,
                           shell=True)

        process.communicate()

        print(_("Scanning has completed. The mapping has been"
                " stored in file '" + self.options.profile +
                "_host_auth_map'. The"
                " facts have been stored in '" +
                report_path + "'"))
