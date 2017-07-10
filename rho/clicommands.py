#
# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#

# pylint: disable=too-few-public-methods, too-many-lines

""" Rho CLI Commands """

from __future__ import print_function
import csv
import os
import sys
import uuid
import re
import glob
import time
import json
import subprocess as sp
from collections import defaultdict
from collections import OrderedDict
from copy import copy
from optparse import OptionParser  # pylint: disable=deprecated-module
from getpass import getpass
import gettext

T = gettext.translation('rho', 'locale', fallback=True)
if hasattr(T, 'ugettext'):
    _ = T.ugettext
else:
    _ = T.gettext


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


# pylint: disable=unused-argument
def multi_arg(option, opt_str, value, parser):
    """Call back function for arg-parse
    for when arguments are multiple
    :param option: The option
    :param opt_str: The option string
    :param value: The value
    :param parser: The parser for handling the option
    """
    args = []
    for arg in parser.rargs:
        if arg[0] != "-":
            args.append(arg)
        else:
            del parser.rargs[:len(args)]
            break
    if getattr(parser.values, option.dest):
        args.extend(getattr(parser.values, option.dest))
    setattr(parser.values, option.dest, args)


# Read ssh key from file
def _read_key_file(filename):
    keyfile = open(os.path.expanduser(
        os.path.expandvars(filename)), "r")
    sshkey = keyfile.read()
    keyfile.close()
    return sshkey


# Read in a file and make it a list
def _read_in_file(filename):
    result = None
    hosts = None
    try:
        hosts = open(os.path.expanduser(os.path.expandvars(filename)), "r")
        result = hosts.read().splitlines()
        hosts.close()
    except EnvironmentError as err:
        sys.stderr.write('Error reading from %s: %s\n' % (filename, err))
        hosts.close()
    return result


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


# Makes sure the hosts passed in are in a format Ansible
# understands.
def _check_range_validity(range_list):
    # pylint: disable=anomalous-backslash-in-string
    regex_list = ['www\[[0-9]*:[0-9]*\].[a-z]*.[a-z]*',
                  '[a-z]*-\[[a-z]*:[a-z]*\].[a-z]*.[a-z]*',
                  '[0-9]*.[0-9]*.[0-9]'
                  '*.\[[0-9]*:[0-9]*\]',
                  '^(([0-9]|[1-9][0-9]|1[0-9]'
                  '{2}|2[0-4][0-9]|25[0-5])\.)'
                  '{3}']

    for reg_item in range_list:
        match = False
        for reg in regex_list:
            if re.match(reg, reg_item):
                match = True
        if not match:
            if len(reg_item) <= 1:
                print(_("No such hosts file."))
            print(_("Bad host name/range : '%s'") % reg_item)
            sys.exit(1)


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


class CliCommand(object):

    """ Base class for all sub-commands. """
    def __init__(self, name="cli", usage=None, shortdesc=None,
                 description=None):

        self.shortdesc = shortdesc
        if shortdesc is not None and description is None:
            description = shortdesc
        self.parser = OptionParser(usage=usage, description=description)
        self.name = name
        self.passphrase = None
        self.args = None
        self.options = None

    def _validate_options(self):
        """
        Sub-commands can override to do any argument validation they
        require.
        """
        pass

    def _do_command(self):
        """
        Sub-commands define this method to perform the
        required action once all options have been verified.
        """
        pass

    def main(self):
        """
        The method that does a basic check for command
        validity and set's the process in motion.
        """

        (self.options, self.args) = self.parser.parse_args()

        # we dont need argv[0] in this list...

        self.args = self.args[1:]

        self._validate_options()

        if len(sys.argv) < 2:
            print(self.parser.error(_("Please enter at least 2 args")))

        # do the work, catch most common errors here:

        self._do_command()


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


class ProfileShowCommand(CliCommand):
    """
    This command is for displaying a particular profile
    the user has added previously if it has not been deleted
    already.
    """

    def __init__(self):
        usage = _("usage: %prog profile show [options]")
        shortdesc = _("show a network profile")
        desc = _("show a network profile")

        CliCommand.__init__(self, "profile show", usage, shortdesc, desc)

        self.parser.add_option("--name", dest="name", metavar="NAME",
                               help=_("profile name - REQUIRED"))

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.name:
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        profile_exists = False
        with open('data/profiles', 'r') as profiles_file:
            lines = profiles_file.readlines()
            for line in lines:
                line_list = line.strip().split(',____,')
                if line_list[0] == self.options.name:
                    profile_exists = True
                    profile_str = ', '.join(line_list[0:3] + [line_list[3]])
                    print(profile_str)

        if not profile_exists:
            print(_("Profile '%s' does not exist.") % self.options.name)
            sys.exit(1)


class ProfileListCommand(CliCommand):
    """
    This command is for displaying all existing profiles
    the user has added previously.
    """

    def __init__(self):
        usage = _("usage: %prog profile list [options]")
        shortdesc = _("list the network profiles")
        desc = _("list the network profiles")

        CliCommand.__init__(self, "profile list", usage, shortdesc, desc)

    def _do_command(self):
        if not os.path.isfile('data/profiles'):
            print(_('No profiles exist yet.'))
            sys.exit(1)

        with open('data/profiles', 'r') as profiles_file:
            lines = profiles_file.readlines()
            for line in lines:
                print(line)


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


class ProfileClearCommand(CliCommand):
    """
    This command is for removing profiles.
    A user can remove an existing profile by
    passing in the name or ask to delete all
    profiles.
    """

    def __init__(self):
        usage = _("usage: %prog profile clear [--name | --all] [options]")
        shortdesc = _("removes 1 or all profiles from list")
        desc = _("removes profiles")

        CliCommand.__init__(self, "profile clear", usage, shortdesc, desc)

        self.parser.add_option("--name", dest="name", metavar="NAME",
                               help=_("NAME of the profile to be removed"))
        self.parser.add_option("--all", dest="all", action="store_true",
                               help=_("remove ALL profiles"))

        self.parser.set_defaults(all=False)

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.name and not self.options.all:
            self.parser.print_help()
            sys.exit(1)

        if self.options.name and self.options.all:
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        if self.options.name:
            profile = self.options.name
            exists = False
            with open('data/profiles', 'r') as profiles_file:
                lines = profiles_file.readlines()

            with open('data/profiles', 'w') as profiles_file:

                for line in lines:
                    line_list = line.strip().split(',')
                    if not line_list[0] == profile:
                        profiles_file.write(line)
                    else:
                        exists = True

            if not exists:
                print(_("No such profile: '%s'") % profile)
                sys.exit(1)

            # removes inventory associated with the profile
            if os.path.isfile('data/' + profile + "_hosts"):
                os.remove('data/' + profile + "_hosts")

            profile_mapping = 'data/' + profile + '_host_auth_mapping'

            # when a profile is removed, it 'archives' the host auth mapping
            # by renaming it '(DELETED PROFILE)<profile_name>_host_auth_mapping
            # for identification by the user. The time stamps in mapping files
            # help in identifying the various forms and times in which the said
            # profile existed.
            if os.path.isfile(profile_mapping):
                os.rename(profile_mapping,
                          'data/(DELETED PROFILE)' +
                          profile + '_host_auth_mapping')

        # removes all inventories ever.
        elif self.options.all:
            if not os.path.isfile('data/profiles'):
                print(_("All network profiles removed"))
            else:
                os.remove('data/profiles')
                for file_list in glob.glob("data/*_hosts"):
                    os.remove(file_list)
                    profile = file_list.strip('_hosts')
                    profile_mapping = 'data/' + profile + '_host_auth_mapping'
                    if os.path.isfile(profile_mapping):
                        os.rename(profile_mapping,
                                  'data/(DELETED PROFILE)' +
                                  profile + '_host_auth_mapping')

                print(_("All network profiles removed"))


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
                    " --username, --password or --filename"))
            sys.exit(1)

    def _do_command(self):

        exists = False

        with open('data/credentials', 'r') as credentials_file:
            lines = credentials_file.readlines()

        with open('data/credentials', 'w') as credentials_file:
            for line in lines:
                line_list = line.strip().split(',')
                if line_list[1] \
                        == self.options.name:
                    exists = True
                    if self.options.username:
                        line_list[2] = self.options.username
                    if self.options.password:
                        pass_prompt = getpass()
                        line_list[3] = 'empty' \
                            if not pass_prompt else pass_prompt
                    if self.options.filename:
                        line_list[4] = self.options.filename
                line_string = ",".join(line_list)
                credentials_file.write(line_string + '\n')

        if not exists:
            print(_("Auth '%s' does not exist.") % self.options.name)
            sys.exit(1)

        print(_("Auth '%s' updated") % self.options.name)


class AuthClearCommand(CliCommand):
    """
    This command is for removing a specific
    or all existing auths.
    """

    def __init__(self):
        usage = _("usage: %prog auth clear")
        shortdesc = _("clears out the credentials")
        desc = _("clears out the crendentials")

        CliCommand.__init__(self, "auth clear", usage, shortdesc, desc)

        self.parser.add_option("--name", dest="name", metavar="NAME",
                               help=_("NAME of the auth "
                                      "credential to be removed"))
        self.parser.add_option("--all", dest="all", action="store_true",
                               help=_("remove ALL auth credentials"))

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.name and not self.options.all:
            self.parser.print_help()
            sys.exit(1)

        if self.options.name and self.options.all:
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        if self.options.name:
            with open('data/credentials', 'r') as creds_read:
                with open('data/cred-temp', 'w') as temp_creds_write:
                    for line in creds_read:
                        temp_creds_write.write(line)

            with open('data/cred-temp', 'r') as temp_creds_read:
                with open('data/credentials', 'w') as creds_write:
                    for line in temp_creds_read:
                        if not line.strip().split(',')[1] \
                                == self.options.name:
                            creds_write.write(line)

            os.remove('data/cred-temp')

        elif self.options.all:
            if os.path.isfile('data/credentials'):
                os.remove('data/credentials')
            if os.path.isfile('data/cred-temp'):
                os.remove('data/cred-temp')
            print(_("All authorization credentials removed"))


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

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.name:
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        if not os.path.isfile('data/credentials'):
            print(_("No auth credentials found"))

        auth_exists = False

        with open('data/credentials', 'r') as credentials_file:
            lines = credentials_file.readlines()
            for line in lines:
                line_list = line.strip().split(',')
                if line_list[1] == self.options.name:
                    auth_exists = True
                    if line_list[4] and line_list[3]:
                        print(', '.join(line_list[0:3]) +
                              ', ********, ' + line_list[4])
                    elif not line_list[4]:
                        print(', '.join(line_list[0:3]) +
                              ', ********')
                    else:
                        print(', '.join(line_list[0:3]) +
                              ', ' + line_list[4])

        if not auth_exists:
            print(_('Auth "%s" does not exist' % self.options.name))
            sys.exit(1)


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

    def _do_command(self):
        if not os.path.isfile('data/credentials'):
            print(_('No credentials exist yet.'))
            sys.exit(1)

        with open('data/credentials', 'r') as credentials_file:
            lines = credentials_file.readlines()
            for line in lines:
                line_list = line.strip().split(',')
                if line_list[3] and line_list[4]:
                    print(', '.join(line_list[0:3]) +
                          ', ********, ' + line_list[4])
                elif not line_list[4]:
                    print(', '.join(line_list[0:3]) +
                          ', ********')
                else:
                    print(', '.join(line_list[0:3]) +
                          ', ' + line_list[4])


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
